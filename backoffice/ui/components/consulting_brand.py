"""Branding helpers for the consulting / funding cross-sell hero used in ERP pages."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

_REPORTS_DIR = Path(__file__).resolve().parents[3] / "reports" / "consulting"

# Optional deliverables surfaced as downloads when present; guarded by .exists() at call sites.
CONSULTING_HTML_REPORT = _REPORTS_DIR / "cta_consulting_report.html"
CONSULTING_QUICKSTART = _REPORTS_DIR / "cta_consulting_quickstart.html"


def render_cta_brand_hero(title: str, subtitle: str, context_label: str | None = None) -> None:
    """Render a compact branded hero banner used to cross-sell consulting/funding modules."""
    label = f'<div style="font-size:0.75rem;font-weight:600;letter-spacing:.08em;text-transform:uppercase;opacity:.75;margin-bottom:4px;">{context_label}</div>' if context_label else ""
    st.markdown(
        f"""
        <div style="
            padding:18px 22px;
            border-radius:12px;
            background:linear-gradient(135deg,#0f172a,#1e293b);
            color:#f8fafc;
            margin-bottom:16px;
            border:1px solid rgba(148,163,184,.25);
        ">
            {label}
            <div style="font-size:1.35rem;font-weight:700;margin-bottom:4px;">{title}</div>
            <div style="font-size:0.95rem;opacity:.85;">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
