from __future__ import annotations

import json
import os
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict, List

from backoffice.ing_dighub_platform import MODULE_SPECS
from backoffice.integrations.ai_factory_client import AIFactoryClient


def _safe_read_json(path: Path) -> Dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _safe_read_jsonl(path: Path, limit: int = 100) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    rows: List[Dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines()[-limit:]:
        line = line.strip()
        if not line:
            continue
        try:
            parsed = json.loads(line)
            if isinstance(parsed, dict):
                rows.append(parsed)
        except Exception:
            continue
    return rows


def build_capability_map() -> List[Dict[str, str]]:
    capability_map: List[Dict[str, str]] = []
    for spec in MODULE_SPECS:
        capability_map.append(
            {
                "key": spec.key,
                "name": spec.name,
                "service": spec.service,
                "description": spec.description,
            }
        )
    return capability_map


def knowledge_stats(repo_root: Path) -> Dict[str, Any]:
    kh_root = repo_root / "knowledge_hub"
    reports_root = repo_root / "reports"

    kh_files = [p for p in kh_root.rglob("*") if p.is_file()] if kh_root.exists() else []
    report_files = [p for p in reports_root.rglob("*") if p.is_file()] if reports_root.exists() else []

    confidence = "High" if kh_files else "Medium"
    return {
        "knowledge_assets": len(kh_files),
        "report_assets": len(report_files),
        "confidence": confidence,
        "last_update": datetime.now(UTC).isoformat(),
    }


def recent_missions(repo_root: Path, limit: int = 8) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []

    funding_backlog = _safe_read_json(repo_root / "reports" / "rd_funding" / "backlog.json")
    if isinstance(funding_backlog, list):
        for row in funding_backlog:
            out.append(
                {
                    "mission": row.get("objective", "R&D Funding Mission"),
                    "status": row.get("status", "OPEN"),
                    "score": row.get("confidence", "n/a"),
                    "hypothesis": row.get("next_action", "n/a"),
                    "updated_at": row.get("updated_at", "n/a"),
                }
            )

    mission_file = repo_root / "reports" / "spoe" / "mission_portfolio_spoe.json"
    mission_payload = _safe_read_json(mission_file)
    if mission_payload:
        out.append(
            {
                "mission": "SPOE Governance Mission",
                "status": "completed",
                "score": mission_payload.get("selected_score", "n/a"),
                "hypothesis": mission_payload.get("selected_hypothesis", "n/a"),
                "updated_at": mission_payload.get("updated_at", "n/a"),
            }
        )

    score_rows = _safe_read_jsonl(repo_root / "reports" / "spoe" / "platform_score_history.jsonl", limit=limit)
    for row in reversed(score_rows[-limit:]):
        out.append(
            {
                "mission": "Platform Maturity Iteration",
                "status": "completed",
                "score": row.get("global_platform_score", "n/a"),
                "hypothesis": "C",
                "updated_at": row.get("timestamp", "n/a"),
            }
        )

    return out[:limit]


def coordinator_snapshot() -> Dict[str, Any]:
    client = AIFactoryClient()
    health = client.get_json("/health")
    unavailable = health.get("status") == "unavailable" or health.get("error") == "ai_factory_unreachable"

    if unavailable:
        mode = "LOCAL EXECUTION MODE"
        status = "offline"
    else:
        mode = "AI-FACTORY"
        status = "online"

    connected_services = [spec.service for spec in MODULE_SPECS]
    return {
        "status": status,
        "current_mode": mode,
        "runtime": "local" if unavailable else "ai-factory",
        "approval_status": os.environ.get("AI_COORDINATOR_APPROVAL_STATUS", "auto-approval"),
        "evidence_runtime": "enabled",
        "knowledge_runtime": "enabled",
        "mission_runtime": "enabled",
        "governance_runtime": "enabled",
        "connected_services": connected_services,
        "health": health,
    }


def pending_reviews_count(repo_root: Path) -> int:
    review_file = repo_root / "backoffice" / "extraction" / "review_queue.py"
    return 1 if review_file.exists() else 0


def open_projects_count(repo_root: Path) -> int:
    projects = repo_root / "reports" / "PROJECT_IMPLEMENTATION_PLAN_V2.md"
    return 1 if projects.exists() else 0


def latest_reports(repo_root: Path, limit: int = 6) -> List[Dict[str, str]]:
    reports_root = repo_root / "reports"
    if not reports_root.exists():
        return []

    files = [p for p in reports_root.rglob("*") if p.is_file()]
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)

    rows: List[Dict[str, str]] = []
    for p in files[:limit]:
        rows.append(
            {
                "name": p.name,
                "path": str(p).replace("\\", "/"),
                "last_update": datetime.fromtimestamp(p.stat().st_mtime, tz=UTC).isoformat(),
            }
        )
    return rows


def module_table() -> List[Dict[str, Any]]:
    return [asdict(spec) for spec in MODULE_SPECS]
