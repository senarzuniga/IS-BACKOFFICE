from __future__ import annotations

from datetime import datetime
from typing import Any

import streamlit as st

# ---------------------------------------------------------------------------
# Navigation structure: (section_label, [(page_name, icon), ...])
# ---------------------------------------------------------------------------
_NAV_STRUCTURE: list[tuple[str, list[tuple[str, str]]]] = [
    ("📥 INGESTION", [
        ("File Upload",       "📂"),
        ("URL Ingest",        "🌐"),
        ("Watch Folder",      "👁️"),
        ("Bulk Import",       "📦"),
        ("Scraper",           "🕷️"),
    ]),
    ("🧹 CLEANING", [
        ("Deduplication",     "🔁"),
        ("Standardization",   "📐"),
        ("Quality Audit",     "✅"),
        ("Outlier Detection", "⚠️"),
        ("Fuzzy Merge",       "🔗"),
    ]),
    ("🔍 EXTRACTION", [
        ("Text NER",          "📝"),
        ("PDF Extraction",    "📄"),
        ("Batch Processing",  "⚙️"),
        ("Few-Shot Examples", "🎯"),
        ("Table Detection",   "📊"),
    ]),
    ("🕸️ GRAPH", [
        ("Search Graph",         "🔍"),
        ("Entity Explorer",      "🧩"),
        ("Path Finder",          "🛣️"),
        ("Community Detection",  "👥"),
        ("Subgraph Visualizer",  "🌐"),
    ]),
    ("📊 ANALYTICS", [
        ("Dataset Insights", "💡"),
        ("NL Query",         "💬"),
        ("Forecasting",      "📈"),
        ("What-If Analysis", "🧪"),
        ("Dashboard Builder","🖥️"),
    ]),
    ("📑 REPORTING", [
        ("Generate Report",  "📋"),
        ("Schedule Report",  "⏰"),
        ("Export",           "💾"),
        ("Email Template",   "📧"),
        ("Report History",   "🗂️"),
    ]),
    ("🤖 AGENTS", [
        ("Run All Agents",   "▶️"),
        ("Agent Status",     "🟢"),
        ("Configure Agents", "⚙️"),
    ]),
]

MODULE_KEYS = ["ingestion", "cleaning", "extraction", "graph", "analytics", "reporting"]

_SECTION_TO_MODULE: dict[str, str] = {
    "📥 INGESTION": "ingestion",
    "🧹 CLEANING": "cleaning",
    "🔍 EXTRACTION": "extraction",
    "🕸️ GRAPH": "graph",
    "📊 ANALYTICS": "analytics",
    "📑 REPORTING": "reporting",
    "🤖 AGENTS": "agents",
}


def _dot(is_healthy: bool) -> str:
    return "🟢" if is_healthy else "🔴"


def _render_system_status(health: dict[str, bool]) -> None:
    st.sidebar.markdown("---")
    st.sidebar.subheader("⚙️ System Status")
    for module in MODULE_KEYS:
        label = module.title()
        state = _dot(bool(health.get(module, False)))
        st.sidebar.markdown(f"{state} **{label}**")

    memory_pct = int(st.session_state.get("memory_usage", 87))
    st.sidebar.caption("Memory usage")
    st.sidebar.progress(memory_pct / 100.0)
    st.sidebar.caption(f"{memory_pct}% memory")

    last_activity = st.session_state.get("last_activity", datetime.now().isoformat(timespec="seconds"))
    st.sidebar.caption(f"Last activity: {last_activity}")


def _render_quick_actions() -> str | None:
    st.sidebar.markdown("---")
    st.sidebar.subheader("⚡ Quick Actions")
    if st.sidebar.button("📄 Document Analysis", key="qa_doc_analysis", use_container_width=True):
        return "Document Analysis"
    if st.sidebar.button("💬 Instruction Panel", key="qa_instruction", use_container_width=True):
        return "Instruction Panel"
    if st.sidebar.button("⚡ Process All Files", key="qa_process_all", use_container_width=True):
        return "Process All New Files"
    if st.sidebar.button("🤖 Ask AI Assistant", key="qa_ai_assistant", use_container_width=True):
        return "Ask AI Assistant"
    return None


def render_sidebar() -> dict[str, Any]:
    st.markdown(
        """
        <style>
            section[data-testid="stSidebar"] { width: 280px !important; }
            .nav-section-header {
                font-size: 0.72rem;
                font-weight: 700;
                letter-spacing: 0.08em;
                text-transform: uppercase;
                padding: 8px 0 2px 0;
                opacity: 0.7;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    module_health = st.session_state.get(
        "module_health",
        {m: True for m in MODULE_KEYS},
    )

    st.sidebar.markdown("## 🏢 IS-BACKOFFICE")
    st.sidebar.caption("AI Back Office Intelligence")
    st.sidebar.markdown("---")

    active_page = st.session_state.get("active_page", "Dashboard")

    # Dashboard home button
    if st.sidebar.button("🏠 Dashboard", key="nav_Dashboard", use_container_width=True):
        st.session_state["active_page"] = "Dashboard"
        st.rerun()

    # Render navigation sections
    for section_label, items in _NAV_STRUCTURE:
        st.sidebar.markdown(
            f'<div class="nav-section-header">{section_label}</div>',
            unsafe_allow_html=True,
        )
        for page_name, icon in items:
            btn_label = f"{icon} {page_name}"
            is_active = active_page == page_name
            btn_key = f"nav_{page_name.replace(' ', '_')}"
            if st.sidebar.button(btn_label, key=btn_key, use_container_width=True):
                st.session_state["active_page"] = page_name
                # Also map active_page to legacy current_section for backward compat
                module = _SECTION_TO_MODULE.get(section_label, "")
                st.session_state["_active_section"] = section_label
                st.rerun()

    _render_system_status(module_health)
    quick_action = _render_quick_actions()

    return {
        "active_page": st.session_state.get("active_page", "Dashboard"),
        "quick_action": quick_action,
        "run_action": False,
        "payload": {},
    }
