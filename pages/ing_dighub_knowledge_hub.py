from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Dict, List

import streamlit as st


REPO_ROOT = Path(__file__).resolve().parent.parent

CATEGORY_RULES = {
    "Product Knowledge": ["product", "catalog", "spec", "sr1400"],
    "Machine Catalogue": ["machine", "catalogue", "equipment"],
    "Engineering Standards": ["standard", "norm", "governance", "architecture"],
    "Projects": ["project", "plan", "roadmap"],
    "Layouts": ["layout", "dwg", "dxf"],
    "Reports": ["report", "status", "audit"],
    "Suppliers": ["supplier", "vendor"],
    "Customers": ["customer", "client"],
    "ROI Studies": ["roi", "return"],
    "Case Studies": ["case_study", "case-study", "use_case"],
    "Patents": ["patent"],
    "Competitor Intelligence": ["competitive", "competitor", "intel"],
    "Technical Calculations": ["calculator", "calculation", "kpi", "formula"],
    "Documents": ["pdf", "docx", "txt", "md"],
    "Media Library": ["png", "jpg", "jpeg", "webp", "mp4", "mov"],
}


def _is_text_file(path: Path) -> bool:
    return path.suffix.lower() in {".md", ".txt", ".json", ".jsonl", ".py", ".yaml", ".yml", ".csv"}


def _guess_category(path: Path) -> str:
    text = str(path).lower().replace("\\", "/")
    for category, keys in CATEGORY_RULES.items():
        if any(k in text for k in keys):
            return category
    return "Documents"


def _evidence(path: Path) -> str:
    if not _is_text_file(path):
        return "Binary asset"
    try:
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if line:
                return line[:140]
    except Exception:
        return "Unable to parse evidence"
    return "No textual evidence"


def _related_products(path: Path) -> str:
    low = path.name.lower()
    if "sr1400" in low:
        return "SR1400"
    if "ingetrans" in low:
        return "INGETRANS"
    if "reel" in low:
        return "REEL_LOADING"
    return "General"


def _collect_assets(limit: int = 600) -> List[Dict[str, str]]:
    roots = [
        REPO_ROOT / "knowledge_hub",
        REPO_ROOT / "reports",
        REPO_ROOT / "docs",
        REPO_ROOT / "assets",
    ]

    files: List[Path] = []
    for root in roots:
        if not root.exists():
            continue
        files.extend([p for p in root.rglob("*") if p.is_file()])

    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)

    rows: List[Dict[str, str]] = []
    for path in files[:limit]:
        rel = str(path.relative_to(REPO_ROOT)).replace("\\", "/")
        rows.append(
            {
                "Category": _guess_category(path),
                "Asset": path.name,
                "Source": rel,
                "Confidence": "High" if rel.startswith("knowledge_hub/") else "Medium",
                "Evidence": _evidence(path),
                "Last Update": datetime.fromtimestamp(path.stat().st_mtime, tz=UTC).isoformat(),
                "Related Missions": "SPOE Governance Mission",
                "Related Products": _related_products(path),
                "Related Documents": path.name,
            }
        )
    return rows


def main() -> None:
    st.set_page_config(page_title="ING_DIGHUB Knowledge Hub", page_icon="📚", layout="wide")

    try:
        from backoffice.theme import inject_theme
        inject_theme()
    except Exception:
        pass

    st.title("📚 Knowledge Hub")
    st.caption("Unified executive access to existing Knowledge Hub assets")

    assets = _collect_assets()
    categories = sorted({row["Category"] for row in assets})

    q = st.text_input("Global Search", placeholder="Search by source, evidence, product, or category")
    selected_categories = st.multiselect(
        "Knowledge Domains",
        options=categories,
        default=categories,
    )

    filtered = []
    for row in assets:
        if row["Category"] not in selected_categories:
            continue
        blob = " ".join([str(v) for v in row.values()]).lower()
        if q.strip() and q.lower() not in blob:
            continue
        filtered.append(row)

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Assets", len(assets))
    c2.metric("Filtered Assets", len(filtered))
    c3.metric("Domains", len(categories))

    st.dataframe(filtered, use_container_width=True)

    st.markdown("### Domains")
    st.write(
        [
            "Product Knowledge",
            "Machine Catalogue",
            "Engineering Standards",
            "Projects",
            "Layouts",
            "Reports",
            "Suppliers",
            "Customers",
            "ROI Studies",
            "Case Studies",
            "Patents",
            "Competitor Intelligence",
            "Technical Calculations",
            "Documents",
            "Media Library",
        ]
    )


if __name__ == "__main__":
    main()
