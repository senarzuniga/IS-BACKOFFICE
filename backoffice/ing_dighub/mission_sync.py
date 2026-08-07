from __future__ import annotations

import csv
import json
from datetime import UTC, datetime
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from backoffice.spe.database import SPEDatabase
from db.client import get_supabase_client


@dataclass(frozen=True)
class AhdeCandidate:
    key: str
    confidence: float
    impact: float
    effort: float
    risk_inverse: float


def _ahde_score(candidate: AhdeCandidate) -> float:
    return (candidate.confidence * 0.35) + (candidate.impact * 0.35) + (candidate.effort * 0.10) + (candidate.risk_inverse * 0.20)


def _resolve_ahde(candidates: list[AhdeCandidate]) -> tuple[AhdeCandidate, list[dict[str, Any]]]:
    if not candidates:
        fallback = AhdeCandidate("csv", confidence=6.0, impact=5.0, effort=8.5, risk_inverse=8.0)
        return fallback, [{"key": fallback.key, "score": round(_ahde_score(fallback), 4)}]

    ranked = [{"key": c.key, "score": round(_ahde_score(c), 4)} for c in candidates]
    ranked.sort(key=lambda x: x["score"], reverse=True)
    selected = next(c for c in candidates if c.key == ranked[0]["key"])
    return selected, ranked


class MissionSyncService:
    """Post-mission synchronizer for KAM, Offers, and Actions snapshots."""

    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root
        self.reports_dir = repo_root / "reports" / "ing_dighub"
        self.snapshots_dir = self.reports_dir / "domain_snapshots"
        self.evidence_file = self.reports_dir / "mission_evidence.jsonl"

    def collect_domain_snapshot(self) -> dict[str, Any]:
        offers = self._collect_offers_snapshot()
        actions = self._collect_actions_snapshot()
        kam = self._collect_kam_snapshot(offers, actions)
        return {
            "captured_at": datetime.now(UTC).isoformat(),
            "offers": offers,
            "actions": actions,
            "kam": kam,
        }

    def run_post_mission_sync(self, mission_id: str, mission_name: str, objective: str) -> dict[str, Any]:
        snapshot = self.collect_domain_snapshot()
        files = self._persist_snapshot_files(snapshot)
        evidence_row = self._append_evidence(mission_id=mission_id, mission_name=mission_name, objective=objective, snapshot=snapshot)
        supabase_result = self._persist_supabase(snapshot=snapshot, evidence=evidence_row)
        return {
            "snapshot": snapshot,
            "files": files,
            "supabase": supabase_result,
        }

    def list_evidence_history(self, limit: int = 100) -> list[dict[str, Any]]:
        if not self.evidence_file.exists():
            return []

        rows: list[dict[str, Any]] = []
        for line in self.evidence_file.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
                if isinstance(payload, dict):
                    rows.append(payload)
            except Exception:
                continue
        rows.sort(key=lambda x: str(x.get("timestamp", "")), reverse=True)
        return rows[:limit]

    def list_snapshot_history(self, limit: int = 100) -> list[dict[str, Any]]:
        if not self.snapshots_dir.exists():
            return []

        rows: list[dict[str, Any]] = []
        files = sorted(self.snapshots_dir.glob("snapshot_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        for path in files[:limit]:
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue

            rows.append(
                {
                    "file": str(path),
                    "captured_at": payload.get("captured_at", ""),
                    "kam_health": payload.get("kam", {}).get("avg_account_health", 0),
                    "offers_acceptance": payload.get("offers", {}).get("accepted_ratio_pct", 0),
                    "open_actions": payload.get("actions", {}).get("open_actions", 0),
                    "actions_source": payload.get("actions", {}).get("source", "unknown"),
                }
            )
        return rows

    def check_supabase_compatibility(self) -> dict[str, Any]:
        supabase = get_supabase_client()
        if supabase is None:
            return {
                "connected": False,
                "compatible": False,
                "checks": [],
                "errors": ["Supabase client not configured in environment"],
            }

        checks = []
        errors: list[str] = []
        probes = [
            ("actions", "id,status,importance_score"),
            ("ingecart_research_entries", "id,entry_type,title,structured_data"),
            ("ingecart_documents", "id,title,category,source_type"),
        ]

        for table, columns in probes:
            try:
                supabase.table(table).select(columns).limit(1).execute()
                checks.append({"table": table, "ok": True})
            except Exception as exc:  # noqa: BLE001
                checks.append({"table": table, "ok": False, "error": str(exc)})
                errors.append(f"{table}: {exc}")

        return {
            "connected": True,
            "compatible": len(errors) == 0,
            "checks": checks,
            "errors": errors,
        }

    def _collect_offers_snapshot(self) -> dict[str, Any]:
        db = SPEDatabase()
        proposals = db.list_all(limit=400)

        total = len(proposals)
        accepted = sum(1 for p in proposals if str(p.status).lower() == "accepted")
        draft = sum(1 for p in proposals if str(p.status).lower() == "draft")

        total_value = 0.0
        by_customer: dict[str, int] = {}
        for proposal in proposals:
            total_value += float(getattr(proposal, "total_price", 0.0) or 0.0)
            customer = (proposal.customer or "Unknown").strip()
            by_customer[customer] = by_customer.get(customer, 0) + 1

        top_customers = sorted(by_customer.items(), key=lambda x: x[1], reverse=True)[:8]
        accepted_ratio = (accepted / total * 100.0) if total else 0.0

        return {
            "total_offers": total,
            "accepted_offers": accepted,
            "draft_offers": draft,
            "accepted_ratio_pct": round(accepted_ratio, 2),
            "total_offer_value_eur": round(total_value, 2),
            "top_customers": [{"customer": name, "offers": count} for name, count in top_customers],
        }

    def _collect_actions_snapshot(self) -> dict[str, Any]:
        csv_path = self.repo_root / "Ing_TRADE COMM Actions" / "10_day_sales_action_pool.csv"

        supabase_rows: list[dict[str, Any]] = []
        csv_rows: list[dict[str, Any]] = []

        supabase = get_supabase_client()
        if supabase is not None:
            try:
                result = supabase.table("actions").select("id,status,importance_score,department").limit(500).execute()
                supabase_rows = result.data if isinstance(getattr(result, "data", None), list) else []
            except Exception:
                supabase_rows = []

        if csv_path.exists():
            try:
                with csv_path.open("r", encoding="utf-8", errors="ignore", newline="") as fh:
                    reader = csv.DictReader(fh)
                    for row in reader:
                        csv_rows.append(row)
            except Exception:
                csv_rows = []

        return self._select_actions_source_ahde(supabase_rows, csv_rows)

    def _select_actions_source_ahde(self, supabase_rows: list[dict[str, Any]], csv_rows: list[dict[str, Any]]) -> dict[str, Any]:
        candidates: list[AhdeCandidate] = []

        if supabase_rows:
            candidates.append(
                AhdeCandidate(
                    key="supabase",
                    confidence=9.0,
                    impact=min(10.0, 6.0 + (len(supabase_rows) / 100.0)),
                    effort=8.5,
                    risk_inverse=7.0,
                )
            )
        if csv_rows:
            candidates.append(
                AhdeCandidate(
                    key="csv",
                    confidence=7.0,
                    impact=min(10.0, 5.5 + (len(csv_rows) / 120.0)),
                    effort=9.0,
                    risk_inverse=8.0,
                )
            )

        selected, ranking = _resolve_ahde(candidates)
        if selected.key == "supabase":
            summary = self._summarize_actions(supabase_rows, source="supabase")
        else:
            summary = self._summarize_actions(csv_rows, source="csv")

        summary["source_selection"] = {
            "method": "AHDE",
            "selected": selected.key,
            "ranking": ranking,
        }
        return summary

    def _summarize_actions(self, rows: list[dict[str, Any]], source: str) -> dict[str, Any]:
        total = len(rows)
        open_actions = 0
        done_actions = 0
        avg_importance = 0.0
        importance_count = 0

        for row in rows:
            status = str(row.get("status", "")).lower()
            if status in {"open", "todo", "pending", "queued", "in_progress"}:
                open_actions += 1
            if status in {"done", "closed", "completed", "resolved"}:
                done_actions += 1

            score = row.get("importance_score")
            try:
                avg_importance += float(score)
                importance_count += 1
            except (TypeError, ValueError):
                continue

        unresolved_ratio = ((total - done_actions) / total * 100.0) if total else 0.0
        avg_value = (avg_importance / importance_count) if importance_count else 0.0

        return {
            "source": source,
            "total_actions": total,
            "open_actions": open_actions,
            "closed_actions": done_actions,
            "unresolved_ratio_pct": round(unresolved_ratio, 2),
            "avg_importance_score": round(avg_value, 2),
        }

    def _collect_kam_snapshot(self, offers: dict[str, Any], actions: dict[str, Any]) -> dict[str, Any]:
        top_customers = offers.get("top_customers", [])
        account_count = len(top_customers)
        accepted_ratio = float(offers.get("accepted_ratio_pct", 0.0) or 0.0)
        unresolved = float(actions.get("unresolved_ratio_pct", 0.0) or 0.0)

        avg_health = max(0.0, min(100.0, (accepted_ratio * 0.65) + ((100.0 - unresolved) * 0.35)))

        high_risk_accounts = []
        for item in top_customers:
            customer = str(item.get("customer", "Unknown"))
            exposure = float(item.get("offers", 0.0) or 0.0)
            risk = max(0.0, min(100.0, 75.0 - accepted_ratio + (exposure * 2.5)))
            if risk >= 60.0:
                high_risk_accounts.append({"customer": customer, "risk": round(risk, 2)})

        return {
            "tracked_accounts": account_count,
            "avg_account_health": round(avg_health, 2),
            "high_risk_accounts": high_risk_accounts[:8],
        }

    def _persist_snapshot_files(self, snapshot: dict[str, Any]) -> dict[str, str]:
        ts = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)

        latest_path = self.snapshots_dir / "latest.json"
        versioned_path = self.snapshots_dir / f"snapshot_{ts}.json"

        payload = json.dumps(snapshot, indent=2, ensure_ascii=False)
        latest_path.write_text(payload, encoding="utf-8")
        versioned_path.write_text(payload, encoding="utf-8")

        return {
            "latest": str(latest_path),
            "versioned": str(versioned_path),
        }

    def _append_evidence(
        self,
        *,
        mission_id: str,
        mission_name: str,
        objective: str,
        snapshot: dict[str, Any],
    ) -> dict[str, Any]:
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        row = {
            "timestamp": datetime.now(UTC).isoformat(),
            "mission_id": mission_id,
            "mission_name": mission_name,
            "objective": objective,
            "domains": {
                "kam": snapshot.get("kam", {}),
                "offers": snapshot.get("offers", {}),
                "actions": snapshot.get("actions", {}),
            },
        }
        with self.evidence_file.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        return row

    def _persist_supabase(self, snapshot: dict[str, Any], evidence: dict[str, Any]) -> dict[str, Any]:
        supabase = get_supabase_client()
        if supabase is None:
            return {"connected": False, "writes": 0, "errors": ["Supabase not configured"]}

        writes = 0
        errors: list[str] = []

        rows = [
            {
                "entry_type": "kam_snapshot",
                "title": "KAM Snapshot",
                "content": json.dumps(snapshot.get("kam", {}), ensure_ascii=False),
                "structured_data": snapshot.get("kam", {}),
                "tags": ["ing_dighub", "kam", "mission_sync"],
                "verified": True,
            },
            {
                "entry_type": "offers_snapshot",
                "title": "Offers Snapshot",
                "content": json.dumps(snapshot.get("offers", {}), ensure_ascii=False),
                "structured_data": snapshot.get("offers", {}),
                "tags": ["ing_dighub", "offers", "mission_sync"],
                "verified": True,
            },
            {
                "entry_type": "actions_snapshot",
                "title": "Actions Snapshot",
                "content": json.dumps(snapshot.get("actions", {}), ensure_ascii=False),
                "structured_data": snapshot.get("actions", {}),
                "tags": ["ing_dighub", "actions", "mission_sync"],
                "verified": True,
            },
        ]

        for row in rows:
            try:
                supabase.table("ingecart_research_entries").insert(row).execute()
                writes += 1
            except Exception as exc:  # noqa: BLE001
                errors.append(f"ingecart_research_entries: {exc}")

        try:
            supabase.table("ingecart_documents").insert(
                {
                    "title": f"Mission Evidence {evidence.get('mission_id', '')}",
                    "category": "report",
                    "subcategory": "mission_sync",
                    "source_type": "json",
                    "summary": evidence.get("objective", ""),
                    "raw_text": json.dumps(evidence, ensure_ascii=False),
                    "tags": ["ing_dighub", "mission", "evidence"],
                    "client_ref": "ingecart",
                }
            ).execute()
            writes += 1
        except Exception as exc:  # noqa: BLE001
            errors.append(f"ingecart_documents: {exc}")

        return {
            "connected": True,
            "writes": writes,
            "errors": errors,
        }
