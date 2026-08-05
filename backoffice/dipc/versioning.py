from __future__ import annotations

import difflib
import json
from pathlib import Path
from typing import Any

from knowledge_hub.competitive_intel.fact_versioning import FactVersioning

from .component_library import summarize_component_usage
from .models import DocumentDiff, DocumentModel, VersionEntry


class DocumentVersionStore:
    def __init__(self, base_dir: str | Path) -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.history_file = self.base_dir / "document_versions.json"
        self.fact_store = FactVersioning(self.base_dir / "facts")
        if not self.history_file.exists():
            self.history_file.write_text("[]", encoding="utf-8")

    def load_history(self) -> list[dict[str, Any]]:
        return json.loads(self.history_file.read_text(encoding="utf-8"))

    def append_version(self, document: DocumentModel, version: VersionEntry) -> None:
        history = self.load_history()
        history.append(version.model_dump(mode="json"))
        self.history_file.write_text(json.dumps(history, indent=2, ensure_ascii=False), encoding="utf-8")
        self.fact_store.upsert_fact(
            entity=f"document:{document.id}",
            attribute="version",
            value=str(version.version_number),
            source_id=version.mission_id,
            confidence=1.0,
            meta={"objective": version.objective, "result": version.result},
        )

    def build_diff(self, previous: DocumentModel | None, current: DocumentModel, previous_html: str = "", current_html: str = "") -> DocumentDiff:
        if previous is None:
            return DocumentDiff(
                structural_diff={"initial": True, "sections": len(current.sections), "components": _count_components(current)},
                visual_diff={"theme": current.theme_variant, "palette": current.metadata.get("palette", [])},
                html_diff=[],
                component_diff={"current": summarize_component_usage(_flatten_components(current))},
            )

        prev_components = _flatten_components(previous)
        curr_components = _flatten_components(current)
        prev_usage = summarize_component_usage(prev_components)
        curr_usage = summarize_component_usage(curr_components)

        html_diff = list(
            difflib.unified_diff(
                previous_html.splitlines(),
                current_html.splitlines(),
                fromfile="previous.html",
                tofile="current.html",
                lineterm="",
            )
        )[:300]

        return DocumentDiff(
            structural_diff={
                "sections_before": len(previous.sections),
                "sections_after": len(current.sections),
                "components_before": len(prev_components),
                "components_after": len(curr_components),
            },
            visual_diff={
                "theme_before": previous.theme_variant,
                "theme_after": current.theme_variant,
                "palette_before": previous.metadata.get("palette", []),
                "palette_after": current.metadata.get("palette", []),
            },
            html_diff=html_diff,
            component_diff={
                "before": prev_usage,
                "after": curr_usage,
            },
        )


def _flatten_components(document: DocumentModel):
    components = []
    for section in document.sections:
        for block in section.blocks:
            components.extend(block.components)
    return components


def _count_components(document: DocumentModel) -> int:
    return len(_flatten_components(document))
