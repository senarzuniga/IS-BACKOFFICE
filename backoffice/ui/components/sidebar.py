from __future__ import annotations

from datetime import datetime
from typing import Any

import streamlit as st

_WORKSPACES: list[dict[str, str]] = [
    {
        "page": "Intelligence Center",
        "icon": "🧠",
        "label": "Intelligence Center",
        "description": "Cockpit ejecutivo con insights, alertas y acciones.",
    },
    {
        "page": "Clients & Accounts",
        "icon": "👥",
        "label": "Clients & Accounts",
        "description": "Vista 360 de clientes, actividad y próximos pasos.",
    },
    {
        "page": "Deals & Pipeline",
        "icon": "💼",
        "label": "Deals & Pipeline",
        "description": "Seguimiento del pipeline, pricing y cierre comercial.",
    },
    {
        "page": "Research & Documents",
        "icon": "📄",
        "label": "Research & Documents",
        "description": "Investigación, análisis documental y trazabilidad.",
    },
    {
        "page": "Transcriptions",
        "icon": "🎧",
        "label": "Audio Transcription",
        "description": "Upload audio, transcribe with AI, diarize speakers and summarise (EN/ES).",
    },
    {
        "page": "AI Agents",
        "icon": "🤖",
        "label": "AI Agents",
        "description": "Agentes visibles, automatizaciones y estado operativo.",
    },
    {
        "page": "Alerts & Risks",
        "icon": "🚨",
        "label": "Alerts & Risks",
        "description": "Riesgos, anomalías y señales explicables.",
    },
    {
        "page": "Knowledge Graph",
        "icon": "🕸️",
        "label": "Knowledge Graph",
        "description": "Relaciones entre entidades y contexto persistente.",
    },
    {
        "page": "Reports & Executive",
        "icon": "📈",
        "label": "Reports & Executive",
        "description": "Narrativas ejecutivas, reporting y decisiones.",
    },
    {
        "page": "Settings & Integrations",
        "icon": "⚙️",
        "label": "Settings & Integrations",
        "description": "Capacidades, conectores e integraciones activas.",
    },
]

_POWER_VIEWS: list[tuple[str, list[tuple[str, str]]]] = [
    ("Data Intake", [("File Upload", "📂"), ("URL Ingest", "🌐"), ("Watch Folder", "👁️"), ("Bulk Import", "📦"), ("Scraper", "🕷️")]),
    ("Data Quality", [("Deduplication", "🔁"), ("Standardization", "📐"), ("Quality Audit", "✅"), ("Outlier Detection", "⚠️"), ("Fuzzy Merge", "🔗")]),
    ("Extraction", [("Text NER", "📝"), ("PDF Extraction", "📄"), ("Batch Processing", "⚙️"), ("Few-Shot Examples", "🎯"), ("Table Detection", "📊")]),
    ("Knowledge", [("Search Graph", "🔍"), ("Entity Explorer", "🧩"), ("Path Finder", "🛣️"), ("Community Detection", "👥"), ("Subgraph Visualizer", "🌐")]),
    ("Analytics", [("Dataset Insights", "💡"), ("NL Query", "💬"), ("Forecasting", "📈"), ("What-If Analysis", "🧪"), ("Dashboard Builder", "🖥️")]),
    ("Reporting", [("Generate Report", "📋"), ("Schedule Report", "⏰"), ("Export", "💾"), ("Email Template", "📧"), ("Report History", "🗂️")]),
]

MODULE_KEYS = ["ingestion", "cleaning", "extraction", "graph", "analytics", "reporting"]


def _dot(is_healthy: bool) -> str:
    return "🟢" if is_healthy else "🔴"


def _render_system_status(health: dict[str, bool]) -> None:
    st.sidebar.markdown("---")
    st.sidebar.subheader("Operational Health")
    for module in MODULE_KEYS:
        state = _dot(bool(health.get(module, False)))
        st.sidebar.markdown(f"{state} **{module.title()}**")

    memory_pct = int(st.session_state.get("memory_usage", 87))
    st.sidebar.caption("Runtime memory")
    st.sidebar.progress(memory_pct / 100.0)
    st.sidebar.caption(f"{memory_pct}% memory in use")

    last_activity = st.session_state.get("last_activity", datetime.now().isoformat(timespec="seconds"))
    st.sidebar.caption(f"Last activity: {last_activity}")


def _render_quick_actions() -> str | None:
    st.sidebar.markdown("---")
    st.sidebar.subheader("AI Commands")
    if st.sidebar.button("📄 Open document workspace", key="qa_doc_analysis", use_container_width=True):
        return "Document Analysis"
    if st.sidebar.button("💬 Open command workspace", key="qa_instruction", use_container_width=True):
        return "Instruction Panel"
    if st.sidebar.button("⚠️ Show risky accounts", key="qa_risky_accounts", use_container_width=True):
        return "Show Risky Accounts"
    if st.sidebar.button("📈 Review pipeline now", key="qa_pipeline_review", use_container_width=True):
        return "Review Pipeline"
    if st.sidebar.button("🤖 Open agent center", key="qa_ai_agents", use_container_width=True):
        return "Open Agent Center"
    return None


def render_sidebar() -> dict[str, Any]:
    st.markdown(
        """
        <style>
            section[data-testid="stSidebar"] { width: 320px !important; }
            .workspace-button-caption {
                font-size: 0.75rem;
                opacity: 0.8;
                margin: -4px 0 8px 0;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    module_health = st.session_state.get(
        "module_health",
        {m: True for m in MODULE_KEYS},
    )

    active_page = st.session_state.get("active_page", "Intelligence Center")

    st.sidebar.markdown("## IS-BACKOFFICE")
    st.sidebar.caption("Commercial Intelligence Operating System")
    st.sidebar.markdown("---")
    st.sidebar.subheader("Workspaces")

    for workspace in _WORKSPACES:
        label = f"{workspace['icon']} {workspace['label']}"
        if st.sidebar.button(label, key=f"workspace_{workspace['page']}", use_container_width=True):
            st.session_state["active_page"] = workspace["page"]
            st.rerun()
        if active_page == workspace["page"]:
            st.sidebar.caption(f"→ {workspace['description']}")

    with st.sidebar.expander("Capability Views", expanded=False):
        st.caption("Power-user access to technical capabilities.")
        for group_name, items in _POWER_VIEWS:
            st.markdown(f"**{group_name}**")
            for page_name, icon in items:
                if st.button(f"{icon} {page_name}", key=f"view_{page_name.replace(' ', '_')}", use_container_width=True):
                    st.session_state["active_page"] = page_name
                    st.rerun()

    _render_system_status(module_health)
    quick_action = _render_quick_actions()

    return {
        "active_page": st.session_state.get("active_page", "Intelligence Center"),
        "quick_action": quick_action,
        "run_action": False,
        "payload": {},
    }
