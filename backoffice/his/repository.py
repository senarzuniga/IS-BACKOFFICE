from __future__ import annotations

import json
import os
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from backoffice.dipc.models import DocumentModel


REPO_ROOT = Path(__file__).resolve().parents[2]
REPORTS_ROOT = REPO_ROOT / "reports"


class DocumentRepository:
    """Persistence and query layer for HIS document runs and metadata."""

    def __init__(self, reports_root: Path | None = None) -> None:
        self.reports_root = reports_root or REPORTS_ROOT

    def list(self, limit: int = 500) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for model_path in self.reports_root.glob("**/metadata/document_model.json"):
            try:
                rows.append(self._to_summary(model_path))
            except Exception:
                continue
        rows.sort(key=lambda x: x.get("date", ""), reverse=True)
        return rows[:limit]

    def get(self, document_model_path: str) -> dict[str, Any]:
        model_path = Path(document_model_path).expanduser().resolve()
        model = DocumentModel.model_validate_json(model_path.read_text(encoding="utf-8"))
        base_dir = model_path.parent.parent
        return {
            "model": model.model_dump(mode="json"),
            "document_model_path": str(model_path),
            "output_dir": str(base_dir),
        }

    def open(self, document_model_path: str) -> dict[str, Any]:
        return self.get(document_model_path)

    def save(self, document_model_path: str, updates: dict[str, Any]) -> dict[str, Any]:
        model_path = Path(document_model_path).expanduser().resolve()
        model = DocumentModel.model_validate_json(model_path.read_text(encoding="utf-8"))
        metadata_updates = updates.get("metadata", {}) if isinstance(updates, dict) else {}
        for key, value in metadata_updates.items():
            model.metadata[key] = value
        model.metadata["updated_at"] = datetime.now(UTC).isoformat()
        model_path.write_text(model.model_dump_json(indent=2), encoding="utf-8")
        return {
            "document_model_path": str(model_path),
            "updated": True,
            "metadata": model.metadata,
        }

    def delete(self, document_model_path: str) -> bool:
        model_path = Path(document_model_path).expanduser().resolve()
        if not model_path.exists():
            return False
        base_dir = model_path.parent.parent
        shutil.rmtree(base_dir, ignore_errors=True)
        return True

    def duplicate(self, document_model_path: str) -> dict[str, Any]:
        src_model = Path(document_model_path).expanduser().resolve()
        if not src_model.exists():
            raise FileNotFoundError(f"Document model not found: {src_model}")

        src_dir = src_model.parent.parent
        dst_dir = src_dir.parent / f"{src_dir.name}_dup_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}"
        shutil.copytree(src_dir, dst_dir, dirs_exist_ok=False)
        self._make_tree_writable(dst_dir)

        dst_model = dst_dir / "metadata" / "document_model.json"
        model = DocumentModel.model_validate_json(dst_model.read_text(encoding="utf-8"))
        model.id = uuid4().hex
        history = model.metadata.get("publication_state_history", [])
        if not isinstance(history, list):
            history = []
        history.append({"state": "Draft", "ts": datetime.now(UTC).isoformat(), "reason": "duplicate_document"})
        model.metadata["publication_state"] = "Draft"
        model.metadata["publication_state_history"] = history
        model.metadata["duplicated_from"] = str(src_model)
        dst_model.write_text(model.model_dump_json(indent=2), encoding="utf-8")

        return {
            "document_model_path": str(dst_model),
            "output_dir": str(dst_dir),
            "duplicated_from": str(src_model),
        }

    def list_versions(self, document_model_path: str) -> list[dict[str, Any]]:
        model_path = Path(document_model_path).expanduser().resolve()
        model = DocumentModel.model_validate_json(model_path.read_text(encoding="utf-8"))
        if model.version_history:
            return [v.model_dump(mode="json") for v in model.version_history]
        return self._load_version_records(model_path)

    def restore_version(self, document_model_path: str, version_number: int) -> dict[str, Any]:
        model_path = Path(document_model_path).expanduser().resolve()
        model = DocumentModel.model_validate_json(model_path.read_text(encoding="utf-8"))
        versions = [v.model_dump(mode="json") for v in model.version_history if int(v.version_number) == int(version_number)]
        if not versions:
            versions = [v for v in self._load_version_records(model_path) if int(v.get("version_number", 0)) == int(version_number)]
        if not versions:
            raise ValueError(f"Version not found: {version_number}")

        selected = versions[-1]
        history = model.metadata.get("publication_state_history", [])
        if not isinstance(history, list):
            history = []
        history.append({"state": "Editing", "ts": datetime.now(UTC).isoformat(), "reason": f"restore_version_{version_number}"})
        model.metadata["publication_state"] = "Editing"
        model.metadata["publication_state_history"] = history
        model.metadata["restored_version"] = version_number
        model_path.write_text(model.model_dump_json(indent=2), encoding="utf-8")
        return {
            "document_model_path": str(model_path),
            "version": selected,
        }

    def quality_report(self, document_model_path: str) -> dict[str, Any]:
        model_path = Path(document_model_path).expanduser().resolve()
        qpath = model_path.parent / "quality_report.json"
        if not qpath.exists():
            return {}
        return json.loads(qpath.read_text(encoding="utf-8"))

    def search(self, query: str, limit: int = 200) -> list[dict[str, Any]]:
        q = (query or "").strip().lower()
        if not q:
            return self.list(limit=limit)
        rows: list[dict[str, Any]] = []
        for row in self.list(limit=5000):
            blob = " ".join(
                [
                    str(row.get("name", "")),
                    str(row.get("client", "")),
                    str(row.get("project", "")),
                    str(row.get("category", "")),
                    str(row.get("status", "")),
                ]
            ).lower()
            if q in blob:
                rows.append(row)
        return rows[:limit]

    def statistics(self) -> dict[str, Any]:
        docs = self.list(limit=10000)
        by_status: dict[str, int] = {}
        for row in docs:
            status = str(row.get("status", "Draft"))
            by_status[status] = by_status.get(status, 0) + 1
        published = by_status.get("Published", 0)
        editing = by_status.get("Editing", 0)
        return {
            "total_documents": len(docs),
            "published_documents": published,
            "editing_documents": editing,
            "status_breakdown": by_status,
        }

    def _to_summary(self, model_path: Path) -> dict[str, Any]:
        model = DocumentModel.model_validate_json(model_path.read_text(encoding="utf-8"))
        base_dir = model_path.parent.parent
        state = str(model.metadata.get("publication_state", "Draft"))
        score = float(model.metadata.get("executive_quality_score", 0.0))
        updated_at = str(model.metadata.get("published_at") or model.metadata.get("updated_at") or "")
        version_count = len(model.version_history) or len(self._load_version_records(model_path))
        return {
            "name": model.title,
            "client": model.metadata.get("client", ""),
            "project": model.metadata.get("project", ""),
            "category": model.metadata.get("category", ""),
            "language": model.metadata.get("language", ""),
            "version": version_count,
            "status": state,
            "executive_score": score,
            "date": updated_at,
            "last_edit": updated_at,
            "document_model_path": str(model_path),
            "output_dir": str(base_dir),
        }

    def _load_version_records(self, model_path: Path) -> list[dict[str, Any]]:
        history_path = model_path.parent.parent / "history" / "document_versions.json"
        if not history_path.exists():
            return []
        try:
            data = json.loads(history_path.read_text(encoding="utf-8"))
        except Exception:
            return []
        if not isinstance(data, list):
            return []
        return [row for row in data if isinstance(row, dict)]

    def _make_tree_writable(self, root: Path) -> None:
        for path in [root, *root.rglob("*")]:
            try:
                os.chmod(path, 0o666 if path.is_file() else 0o777)
            except OSError:
                continue
