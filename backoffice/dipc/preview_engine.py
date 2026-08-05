from __future__ import annotations

import json
from pathlib import Path

from .models import DocumentModel, PreviewProfile


class PreviewEngine:
    def build_profiles(self, document: DocumentModel, html_path: str) -> list[PreviewProfile]:
        return [
            PreviewProfile(device="desktop", width_px=1440, height_px=1024, theme=document.theme_variant, html_path=html_path),
            PreviewProfile(device="tablet", width_px=1024, height_px=1366, theme=document.theme_variant, html_path=html_path),
            PreviewProfile(device="mobile", width_px=390, height_px=844, theme=document.theme_variant, html_path=html_path),
            PreviewProfile(device="print", width_px=1240, height_px=1754, theme=document.theme_variant, html_path=html_path),
        ]

    def write_manifest(self, document: DocumentModel, path: str | Path) -> str:
        payload = {
            "document_id": document.id,
            "title": document.title,
            "profiles": [profile.model_dump(mode="json") for profile in document.preview_profiles],
            "capabilities": [
                "live_preview",
                "responsive_preview",
                "dark_mode",
                "print_preview",
                "scroll_spy",
                "performance_review",
                "accessibility_review",
            ],
        }
        target = Path(path)
        target.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        return str(target)
