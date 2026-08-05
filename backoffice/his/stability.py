from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4


REPO_ROOT = Path(__file__).resolve().parents[2]
STABILITY_DIR = REPO_ROOT / "reports" / "html_intelligence_studio" / "stability"
WATCHDOG_STATE_PATH = STABILITY_DIR / "watchdog_state.json"
CHECKPOINT_MANIFEST_PATH = STABILITY_DIR / "checkpoint_manifest.jsonl"
SMART_CACHE_PATH = STABILITY_DIR / "smart_cache.json"


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _sha256_of_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as fh:
        while True:
            chunk = fh.read(1024 * 1024)
            if not chunk:
                break
            hasher.update(chunk)
    return hasher.hexdigest()


@dataclass
class StallTask:
    task_id: str
    task_name: str
    elapsed_seconds: float
    timeout_seconds: int


class MissionWatchdog:
    """Persistent watchdog that tracks mission task heartbeats and detects stalls."""

    def __init__(self, timeout_seconds: int = 120) -> None:
        self.timeout_seconds = max(30, int(timeout_seconds))
        STABILITY_DIR.mkdir(parents=True, exist_ok=True)
        if not WATCHDOG_STATE_PATH.exists():
            WATCHDOG_STATE_PATH.write_text(
                json.dumps(
                    {
                        "active": True,
                        "timeout_seconds": self.timeout_seconds,
                        "updated_at": _utc_now(),
                        "tasks": {},
                        "events": [],
                    },
                    indent=2,
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

    def _load(self) -> dict[str, Any]:
        try:
            return json.loads(WATCHDOG_STATE_PATH.read_text(encoding="utf-8"))
        except Exception:
            return {
                "active": True,
                "timeout_seconds": self.timeout_seconds,
                "updated_at": _utc_now(),
                "tasks": {},
                "events": [],
            }

    def _save(self, state: dict[str, Any]) -> None:
        state["updated_at"] = _utc_now()
        state["timeout_seconds"] = self.timeout_seconds
        WATCHDOG_STATE_PATH.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")

    def start_task(self, task_name: str, metadata: dict[str, Any] | None = None) -> str:
        task_id = datetime.now(UTC).strftime("%Y%m%d_%H%M%S") + "_" + uuid4().hex[:8]
        state = self._load()
        state.setdefault("tasks", {})[task_id] = {
            "task_name": task_name,
            "status": "RUNNING",
            "started_at": _utc_now(),
            "last_heartbeat": _utc_now(),
            "progress": 0.0,
            "metadata": metadata or {},
        }
        state.setdefault("events", []).append(
            {
                "ts": _utc_now(),
                "event": "task_started",
                "task_id": task_id,
                "task_name": task_name,
            }
        )
        self._save(state)
        return task_id

    def heartbeat(self, task_id: str, progress: float | None = None, note: str = "") -> None:
        state = self._load()
        task = state.get("tasks", {}).get(task_id)
        if not task:
            return
        task["last_heartbeat"] = _utc_now()
        if progress is not None:
            task["progress"] = float(max(0.0, min(1.0, progress)))
        if note:
            task["note"] = note
        state.setdefault("events", []).append(
            {
                "ts": _utc_now(),
                "event": "heartbeat",
                "task_id": task_id,
                "progress": task.get("progress", 0.0),
                "note": note,
            }
        )
        self._save(state)

    def complete_task(self, task_id: str, result: str = "OK") -> None:
        state = self._load()
        task = state.get("tasks", {}).get(task_id)
        if not task:
            return
        task["status"] = "COMPLETED"
        task["completed_at"] = _utc_now()
        task["result"] = result
        state.setdefault("events", []).append({"ts": _utc_now(), "event": "task_completed", "task_id": task_id, "result": result})
        self._save(state)

    def fail_task(self, task_id: str, error: str) -> None:
        state = self._load()
        task = state.get("tasks", {}).get(task_id)
        if not task:
            return
        task["status"] = "FAILED"
        task["failed_at"] = _utc_now()
        task["error"] = error
        state.setdefault("events", []).append({"ts": _utc_now(), "event": "task_failed", "task_id": task_id, "error": error})
        self._save(state)

    def detect_stalled_tasks(self) -> list[StallTask]:
        state = self._load()
        out: list[StallTask] = []
        now = datetime.now(UTC)
        for task_id, task in state.get("tasks", {}).items():
            if task.get("status") != "RUNNING":
                continue
            hb = task.get("last_heartbeat") or task.get("started_at")
            try:
                hb_dt = datetime.fromisoformat(str(hb))
            except Exception:
                continue
            elapsed = (now - hb_dt).total_seconds()
            if elapsed > self.timeout_seconds:
                out.append(
                    StallTask(
                        task_id=task_id,
                        task_name=str(task.get("task_name", "unknown")),
                        elapsed_seconds=float(elapsed),
                        timeout_seconds=self.timeout_seconds,
                    )
                )
        return out


class CheckpointManager:
    """Checkpoint manager for mission phases and rollback references."""

    def __init__(self) -> None:
        STABILITY_DIR.mkdir(parents=True, exist_ok=True)

    def create(self, phase: str, stage: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        checkpoint = {
            "checkpoint_id": datetime.now(UTC).strftime("%Y%m%d_%H%M%S") + "_" + uuid4().hex[:8],
            "ts": _utc_now(),
            "phase": phase,
            "stage": stage,
            "metadata": metadata or {},
        }
        CHECKPOINT_MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
        with CHECKPOINT_MANIFEST_PATH.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(checkpoint, ensure_ascii=False) + "\n")
        return checkpoint


class SmartAssetCache:
    """Smart cache for asset analysis and mission reuse by SHA256."""

    def __init__(self) -> None:
        STABILITY_DIR.mkdir(parents=True, exist_ok=True)
        if not SMART_CACHE_PATH.exists():
            SMART_CACHE_PATH.write_text(json.dumps({"assets": {}, "missions": {}}, indent=2), encoding="utf-8")

    def _load(self) -> dict[str, Any]:
        try:
            return json.loads(SMART_CACHE_PATH.read_text(encoding="utf-8"))
        except Exception:
            return {"assets": {}, "missions": {}}

    def _save(self, cache: dict[str, Any]) -> None:
        SMART_CACHE_PATH.write_text(json.dumps(cache, indent=2, ensure_ascii=False), encoding="utf-8")

    def register_asset(
        self,
        asset_path: str,
        *,
        version: str = "1",
        confidence: float = 1.0,
        dependencies: list[str] | None = None,
        status: str = "processed",
    ) -> dict[str, Any] | None:
        path = Path(asset_path).expanduser().resolve()
        if not path.exists() or not path.is_file():
            return None
        sha = _sha256_of_file(path)
        cache = self._load()
        cache.setdefault("assets", {})[sha] = {
            "path": str(path),
            "sha256": sha,
            "version": version,
            "confidence": round(float(confidence), 4),
            "dependencies": dependencies or [],
            "timestamp": _utc_now(),
            "status": status,
        }
        self._save(cache)
        return cache["assets"][sha]

    def mission_key(self, sources: list[str], source_format: str, language: str, document_name: str) -> str:
        tokens: list[str] = [source_format.strip().lower(), language.strip().lower(), document_name.strip().lower()]
        hashes: list[str] = []
        for src in sources:
            path = Path(src).expanduser().resolve()
            if path.exists() and path.is_file():
                hashes.append(_sha256_of_file(path))
        hashes.sort()
        tokens.extend(hashes)
        return hashlib.sha256("|".join(tokens).encode("utf-8")).hexdigest()

    def register_mission_result(self, key: str, result: dict[str, Any], confidence: float = 0.99) -> None:
        cache = self._load()
        cache.setdefault("missions", {})[key] = {
            "confidence": round(float(confidence), 4),
            "timestamp": _utc_now(),
            "result": result,
        }
        self._save(cache)

    def get_reusable_mission(self, key: str, min_confidence: float = 0.95) -> dict[str, Any] | None:
        cache = self._load()
        mission = cache.get("missions", {}).get(key)
        if not mission:
            return None
        if float(mission.get("confidence", 0.0)) < float(min_confidence):
            return None
        result = mission.get("result", {})
        model_path = Path(str(result.get("document_model_path", ""))).expanduser()
        html_path = Path(str(result.get("html_path", ""))).expanduser()
        if model_path.exists() and html_path.exists():
            return result
        return None


class HealthChecker:
    """Service-level health checks with READY/WARNING/FAIL statuses."""

    def __init__(self, repo_root: Path | None = None) -> None:
        self.repo_root = repo_root or REPO_ROOT

    def run(self) -> dict[str, Any]:
        checks: dict[str, dict[str, Any]] = {}

        checks["repository"] = self._check_path(self.repo_root)
        checks["knowledge_hub"] = self._check_path(self.repo_root / "knowledge_hub")
        checks["enterprise_memory"] = self._check_path(self.repo_root / "data" / "knowledge_memory")
        checks["html_intelligence_studio"] = self._check_path(self.repo_root / "backoffice" / "his")
        checks["mission_registry"] = self._check_file(self.repo_root / "reports" / "html_intelligence_studio" / "mission_registry.jsonl")
        checks["persistence_reports"] = self._check_path(self.repo_root / "reports")
        checks["assistant"] = self._check_path(self.repo_root / "agents")
        checks["mission_manager"] = self._check_file(self.repo_root / "backoffice" / "dipc" / "mission_manager.py")
        checks["database"] = self._check_database_health()

        rollup = "READY"
        if any(v.get("status") == "FAIL" for v in checks.values()):
            rollup = "FAIL"
        elif any(v.get("status") == "WARNING" for v in checks.values()):
            rollup = "WARNING"

        return {
            "generated_at": _utc_now(),
            "overall_status": rollup,
            "services": checks,
        }

    def _check_path(self, path: Path) -> dict[str, Any]:
        if path.exists() and path.is_dir():
            return {"status": "READY", "path": str(path)}
        return {"status": "FAIL", "path": str(path), "reason": "path_missing"}

    def _check_file(self, path: Path) -> dict[str, Any]:
        if path.exists() and path.is_file():
            return {"status": "READY", "path": str(path)}
        return {"status": "WARNING", "path": str(path), "reason": "file_missing"}

    def _check_database_health(self) -> dict[str, Any]:
        db_files = [p for p in self.repo_root.glob("**/*.db") if p.is_file()]
        if not db_files:
            return {"status": "WARNING", "reason": "no_db_files_found", "checked": 0}
        issues = 0
        checked = 0
        for db in db_files[:20]:
            checked += 1
            try:
                con = sqlite3.connect(str(db))
                cur = con.cursor()
                cur.execute("PRAGMA integrity_check")
                row = cur.fetchone()
                con.close()
                if not row or str(row[0]).lower() != "ok":
                    issues += 1
            except Exception:
                issues += 1
        if issues == 0:
            return {"status": "READY", "checked": checked, "issues": issues}
        if issues < checked:
            return {"status": "WARNING", "checked": checked, "issues": issues}
        return {"status": "FAIL", "checked": checked, "issues": issues}


def scan_streamlit_widget_collisions(pages_dir: Path) -> dict[str, Any]:
    """Scan streamlit pages for duplicate button labels without explicit keys and auto-repair when possible."""
    report: dict[str, Any] = {"scanned_files": 0, "collisions": [], "repaired": []}
    if not pages_dir.exists():
        return report

    pattern = re.compile(r"st\.button\(\s*([\"'])(?P<label>.+?)\1(?P<rest>[^\)]*)\)")
    for file_path in sorted(pages_dir.glob("*.py")):
        text = file_path.read_text(encoding="utf-8", errors="ignore")
        report["scanned_files"] += 1

        matches: list[tuple[str, str]] = []
        for m in pattern.finditer(text):
            label = m.group("label")
            rest = m.group("rest") or ""
            call = m.group(0)
            if "key=" in rest:
                continue
            matches.append((label, call))

        label_counts: dict[str, int] = {}
        for label, _ in matches:
            label_counts[label] = label_counts.get(label, 0) + 1

        duplicated_labels = {k for k, v in label_counts.items() if v > 1}
        if not duplicated_labels:
            continue

        new_text = text
        for label in sorted(duplicated_labels):
            calls = [call for lbl, call in matches if lbl == label]
            for idx, call in enumerate(calls, start=1):
                safe = re.sub(r"[^a-zA-Z0-9]+", "_", label).strip("_").lower() or "button"
                key = f"auto_{safe}_{idx}"
                replacement = call[:-1] + f", key=\"{key}\")"
                new_text = new_text.replace(call, replacement, 1)
            report["collisions"].append({"file": str(file_path), "label": label, "count": len(calls)})

        if new_text != text:
            file_path.write_text(new_text, encoding="utf-8")
            report["repaired"].append(str(file_path))

    report["repaired_count"] = len(report["repaired"])
    return report
