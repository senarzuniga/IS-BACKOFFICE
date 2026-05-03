from __future__ import annotations

from datetime import datetime
from typing import Any

import streamlit as st


MODULE_KEYS = ["ingestion", "cleaning", "extraction", "graph", "analytics", "reporting"]

ACTIONS_BY_SECTION = {
    "ðŸ“¥ INGESTION": [
        "Ingest local files",
        "Ingest from URL",
        "Watch folder",
        "Bulk import",
        "Run scraper",
    ],
    "ðŸ§¹ CLEANING": [
        "Run deduplication",
        "Standardize data",
        "Quality audit",
        "Find outliers",
        "Merge duplicates",
    ],
    "ðŸ” EXTRACTION": [
        "Extract entities from text",
        "Process documents",
        "Batch extract",
        "Custom entity extraction",
        "Table extraction",
    ],
    "ðŸ•¸ï¸ GRAPH": [
        "Search knowledge graph",
        "Explore connections",
        "Find path between entities",
        "Graph statistics",
        "Visualize subgraph",
    ],
    "ðŸ“Š ANALYTICS": [
        "Generate insights",
        "Natural language query",
        "Forecast",
        "What-if analysis",
        "Create dashboard",
    ],
    "ðŸ“‘ REPORTING": [
        "Generate report",
        "Schedule report",
        "Export data",
        "Email report",
        "View report history",
    ],
}


def _dot(is_healthy: bool) -> str:
    return "ðŸŸ¢" if is_healthy else "ðŸ”´"


def _render_system_status(health: dict[str, bool]) -> None:
    st.sidebar.subheader("System Status")
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
    st.sidebar.info("3.2GB processed | 14,521 entities | 87% memory")


def _render_action_inputs(section: str, action: str) -> dict[str, Any]:
    payload: dict[str, Any] = {}

    if section == "ðŸ“¥ INGESTION" and action == "Ingest local files":
        payload["files"] = st.sidebar.file_uploader(
            "Upload files",
            type=["csv", "xlsx", "xls", "pdf", "json"],
            accept_multiple_files=False,
        )
    elif section == "ðŸ“¥ INGESTION" and action == "Ingest from URL":
        payload["url"] = st.sidebar.text_input("Source URL", placeholder="https://api.example.com/data")
        payload["method"] = st.sidebar.selectbox("Method", ["API", "Scrape"])
    elif section == "ðŸ“¥ INGESTION" and action == "Watch folder":
        payload["folder_path"] = st.sidebar.text_input("Folder path", placeholder="C:/data/incoming")
        payload["scheduled"] = st.sidebar.toggle("Enable schedule", value=False)
    elif section == "ðŸ“¥ INGESTION" and action == "Bulk import":
        payload["files"] = st.sidebar.file_uploader(
            "Bulk upload",
            type=["csv", "xlsx", "xls", "pdf", "json"],
            accept_multiple_files=True,
        )
    elif section == "ðŸ“¥ INGESTION" and action == "Run scraper":
        payload["urls"] = st.sidebar.text_area("URLs (one per line)", height=120)
        payload["depth"] = st.sidebar.select_slider("Scraping depth", options=[1, 2, 3, 4, 5], value=2)

    elif section == "ðŸ§¹ CLEANING" and action == "Run deduplication":
        payload["entity_type"] = st.sidebar.selectbox("Entity type", ["client", "contact", "offer", "opportunity", "sale"])
        payload["threshold"] = st.sidebar.slider("Threshold", min_value=0.5, max_value=1.0, value=0.85, step=0.01)
    elif section == "ðŸ§¹ CLEANING" and action == "Standardize data":
        payload["preset"] = st.sidebar.selectbox("Rule preset", ["E.164 phones", "ISO dates", "Currency normalization", "Address cleanup"])
    elif section == "ðŸ§¹ CLEANING" and action == "Quality audit":
        payload["dataset"] = st.sidebar.selectbox("Dataset", ["clients", "offers", "sales", "opportunities"])
    elif section == "ðŸ§¹ CLEANING" and action == "Find outliers":
        payload["column"] = st.sidebar.text_input("Column", placeholder="deal_value")
        payload["method"] = st.sidebar.selectbox("Method", ["IQR", "Z-score", "Isolation Forest"])
    elif section == "ðŸ§¹ CLEANING" and action == "Merge duplicates":
        payload["threshold"] = st.sidebar.slider("Fuzzy matching threshold", min_value=0.5, max_value=1.0, value=0.9, step=0.01)
        payload["review_mode"] = st.sidebar.toggle("Review mode", value=True)

    elif section == "ðŸ” EXTRACTION" and action == "Extract entities from text":
        payload["text"] = st.sidebar.text_area("Input text", height=140)
    elif section == "ðŸ” EXTRACTION" and action == "Process documents":
        payload["documents"] = st.sidebar.file_uploader("Upload PDFs", type=["pdf"], accept_multiple_files=True)
    elif section == "ðŸ” EXTRACTION" and action == "Batch extract":
        payload["folder_path"] = st.sidebar.text_input("Folder path", placeholder="C:/docs")
        payload["entity_types"] = st.sidebar.multiselect(
            "Entity types",
            ["clients", "contacts", "offers", "opportunities", "sales", "products"],
            default=["clients", "offers"],
        )
    elif section == "ðŸ” EXTRACTION" and action == "Custom entity extraction":
        payload["few_shot_examples"] = st.sidebar.text_area("Few-shot examples", height=140)
    elif section == "ðŸ” EXTRACTION" and action == "Table extraction":
        payload["documents"] = st.sidebar.file_uploader("Upload PDF/Image", type=["pdf", "png", "jpg", "jpeg"], accept_multiple_files=False)
        payload["table_detection"] = st.sidebar.toggle("Enable table detection", value=True)

    elif section == "ðŸ•¸ï¸ GRAPH" and action == "Search knowledge graph":
        payload["query"] = st.sidebar.text_input("Graph search", placeholder="ACME digital roadmap")
    elif section == "ðŸ•¸ï¸ GRAPH" and action == "Explore connections":
        payload["entity_id"] = st.sidebar.text_input("Entity ID", value="entity_001")
        payload["depth"] = st.sidebar.slider("Depth", min_value=1, max_value=5, value=2)
    elif section == "ðŸ•¸ï¸ GRAPH" and action == "Find path between entities":
        payload["from_entity"] = st.sidebar.text_input("From entity", value="client_001")
        payload["to_entity"] = st.sidebar.text_input("To entity", value="offer_210")
    elif section == "ðŸ•¸ï¸ GRAPH" and action == "Graph statistics":
        payload["include_communities"] = st.sidebar.toggle("Include communities", value=True)
    elif section == "ðŸ•¸ï¸ GRAPH" and action == "Visualize subgraph":
        payload["entity_id"] = st.sidebar.text_input("Center entity", value="client_001")
        payload["depth"] = st.sidebar.slider("Visualization depth", min_value=1, max_value=5, value=2)

    elif section == "ðŸ“Š ANALYTICS" and action == "Generate insights":
        payload["dataset"] = st.sidebar.selectbox("Dataset", ["sales", "pipeline", "accounts", "offers"])
        payload["insight_type"] = st.sidebar.selectbox("Insight type", ["anomaly", "trend", "correlation"])
    elif section == "ðŸ“Š ANALYTICS" and action == "Natural language query":
        payload["question"] = st.sidebar.text_input("Query", value="Show sales by region Q3")
    elif section == "ðŸ“Š ANALYTICS" and action == "Forecast":
        payload["metric"] = st.sidebar.selectbox("Metric", ["revenue", "conversion_rate", "pipeline_value"])
        payload["horizon"] = st.sidebar.slider("Horizon (months)", min_value=1, max_value=24, value=6)
        payload["model"] = st.sidebar.selectbox("Model", ["Prophet", "ARIMA", "LSTM"])
    elif section == "ðŸ“Š ANALYTICS" and action == "What-if analysis":
        payload["price_delta"] = st.sidebar.slider("Price delta %", min_value=-30, max_value=30, value=0)
        payload["conversion_delta"] = st.sidebar.slider("Conversion delta %", min_value=-30, max_value=30, value=0)
    elif section == "ðŸ“Š ANALYTICS" and action == "Create dashboard":
        payload["layout"] = st.sidebar.selectbox("Dashboard template", ["Executive", "Operations", "Sales"])

    elif section == "ðŸ“‘ REPORTING" and action == "Generate report":
        payload["template"] = st.sidebar.selectbox("Template", ["Executive Summary", "Client Diagnostic", "Sales Performance"])
        payload["date_range"] = st.sidebar.date_input("Date range", value=())
    elif section == "ðŸ“‘ REPORTING" and action == "Schedule report":
        payload["frequency"] = st.sidebar.selectbox("Frequency", ["Daily", "Weekly", "Monthly"])
        payload["recipients"] = st.sidebar.text_area("Recipients (comma separated)")
        payload["format"] = st.sidebar.selectbox("Format", ["PDF", "Excel", "PPT", "DOCX"])
    elif section == "ðŸ“‘ REPORTING" and action == "Export data":
        payload["format"] = st.sidebar.selectbox("Export format", ["PDF", "Excel", "PPT", "DOCX"])
    elif section == "ðŸ“‘ REPORTING" and action == "Email report":
        payload["template"] = st.sidebar.selectbox("Email template", ["Executive", "Alert", "KPI Snapshot"])
        payload["recipients"] = st.sidebar.text_area("Recipient list")
    elif section == "ðŸ“‘ REPORTING" and action == "View report history":
        payload["show_failed"] = st.sidebar.toggle("Show failed jobs", value=False)

    return payload


def _render_quick_actions() -> str | None:
    st.sidebar.markdown("---")
    st.sidebar.subheader("Quick Actions")

    if st.sidebar.button("Document Analysis", width="stretch"):
        return "Document Analysis"
    if st.sidebar.button("Instruction Panel", width="stretch"):
        return "Instruction Panel"
    if st.sidebar.button("Process All New Files", width="stretch"):
        return "Process All New Files"
    if st.sidebar.button("Today's Dashboard", width="stretch"):
        return "Today's Dashboard"
    if st.sidebar.button("Ask AI Assistant", width="stretch"):
        return "Ask AI Assistant"
    if st.sidebar.button("Create Summary", width="stretch"):
        return "Create Summary"
    if st.sidebar.button("Settings", width="stretch"):
        return "Settings"

    return None


def render_sidebar() -> dict[str, Any]:
    st.markdown(
        """
        <style>
            section[data-testid=\"stSidebar\"] {
                width: 300px !important;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    module_health = st.session_state.get(
        "module_health",
        {
            "ingestion": True,
            "cleaning": True,
            "extraction": True,
            "graph": True,
            "analytics": True,
            "reporting": False,
        },
    )

    st.sidebar.title("Virtual Back Office")
    panel_view = st.sidebar.radio(
        "Sidebar section",
        ["SYSTEM STATUS", "COMMAND CENTER"],
        horizontal=False,
    )

    section = st.session_state.get("current_section", "")
    action = st.session_state.get("current_action", "")
    payload: dict[str, Any] = {}

    if panel_view == "SYSTEM STATUS":
        _render_system_status(module_health)
    else:
        st.sidebar.subheader("Command Center")
        section = st.sidebar.selectbox("Module", list(ACTIONS_BY_SECTION.keys()), index=0)
        actions = ACTIONS_BY_SECTION.get(section, [])
        action = st.sidebar.selectbox("Action", actions, index=0)
        payload = _render_action_inputs(section, action)

    run_action = st.sidebar.button("Run Selected Action", type="primary", width="stretch")
    quick_action = _render_quick_actions()

    return {
        "panel_view": panel_view,
        "section": section,
        "action": action,
        "payload": payload,
        "run_action": run_action,
        "quick_action": quick_action,
    }

