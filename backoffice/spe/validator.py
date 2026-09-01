from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup


def _extract_local_image_paths(html: str) -> list[str]:
    return re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', html, flags=re.IGNORECASE)


def validate_proposal_document(*, html_text: str, model_path: str, proposal_language: str, proposal_currency: str) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []

    lower = html_text.lower()
    soup = BeautifulSoup(html_text, "html.parser")
    if "<html" not in lower or "</html>" not in lower:
        errors.append("HTML root element missing")
    if soup.find("meta", attrs={"name": "viewport"}) is None:
        warnings.append("Responsive viewport meta missing")
    has_header_signal = (soup.find("header") is not None) or (soup.find("h1") is not None)
    if not has_header_signal:
        errors.append("Corporate header signal missing")
    has_logo_signal = ("ingeeniering.png" in html_text) or ("data:image/" in html_text) or bool(soup.find("img"))
    if not has_logo_signal:
        warnings.append("Official logo signal not detected in HTML")
    if "kpi-row" in html_text or "kpi-card" in html_text:
        errors.append("Forbidden KPI summary block detected")
    heading_count = len(soup.find_all(["h1", "h2", "h3"]))
    if "table of contents" not in lower and "índice" not in lower and "toc" not in lower and heading_count < 5:
        warnings.append("TOC explicit marker not detected")

    for src in _extract_local_image_paths(html_text):
        if src.startswith("http://") or src.startswith("https://") or src.startswith("data:"):
            continue
        path = Path(src)
        if not path.is_absolute():
            warnings.append(f"Non-embedded relative image detected: {src}")
            continue
        if path.is_absolute() and not path.exists():
            errors.append(f"Broken local image: {src}")

    model_file = Path(model_path)
    if not model_file.exists():
        errors.append("Document model file not found")
        metadata = {}
    else:
        data = json.loads(model_file.read_text(encoding="utf-8"))
        metadata = data.get("metadata", {}) if isinstance(data, dict) else {}

    quality_file = model_file.parent / "quality_report.json"
    quality_metrics = {}
    if quality_file.exists():
        try:
            quality_data = json.loads(quality_file.read_text(encoding="utf-8"))
            quality_metrics = (quality_data.get("selected_quality") or {}).get("metrics", {})
        except Exception:
            warnings.append("Could not parse quality_report.json")
    else:
        errors.append("quality_report.json missing")

    accessibility = float(quality_metrics.get("accessibility", 0.0))
    theme = float(quality_metrics.get("theme_compliance", 0.0))
    visual = float(quality_metrics.get("visual_similarity", 0.0))
    responsive = float(quality_metrics.get("responsive", 0.0))

    if accessibility < 90.0:
        errors.append(f"Accessibility score below AA threshold: {accessibility}")
    if theme < 100.0:
        errors.append(f"Corporate theme score below 100: {theme}")
    # HIS may emit scores either as 0..1 or 0..100; normalize for gate checks.
    visual_norm = visual / 100.0 if visual > 1.0 else visual
    responsive_norm = responsive / 100.0 if responsive > 1.0 else responsive
    if visual_norm < 0.99:
        warnings.append(f"Visual similarity below target 0.99: {visual}")
    if responsive_norm < 0.95:
        warnings.append(f"Responsive score below target 0.95: {responsive}")

    if proposal_language.lower() not in {"en", "es"}:
        warnings.append(f"Unexpected language value: {proposal_language}")
    if proposal_currency.upper() not in {"EUR", "USD"}:
        warnings.append(f"Unexpected currency value: {proposal_currency}")

    return {
        "ok": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "scores": {
            "accessibility": accessibility,
            "corporate_theme": theme,
            "visual_diff": visual_norm,
            "responsive": responsive_norm,
        },
        "metadata": metadata,
    }
