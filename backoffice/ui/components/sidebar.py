from __future__ import annotations

import os
from typing import Any

import streamlit as st


WORKFLOWS: dict[str, dict[str, Any]] = {
    "Workspace Reader": {
        "summary": "Read local folders, inspect supported files, and verify what the parser can process.",
        "actions": ["Scan folder", "Analyze folder"],
    },
    "Document Factory": {
        "summary": "Create summaries, briefs, timelines, and reports directly from folder content.",
        "actions": ["Create document"],
    },
    "Web Intelligence": {
        "summary": "Scrape web pages and convert them into structured competitive intelligence.",
        "actions": ["Scrape URL"],
    },
}

OUTPUT_FORMAT_OPTIONS = {
    "Summary": "summary",
    "Executive Summary": "executive_summary",
    "Full Report": "report",
    "Presentation Outline": "presentation",
    "Document List": "list",
    "Database Entry (JSON)": "database_entry",
    "Knowledge Graph Export": "knowledge_graph",
    "Intelligence Brief": "new_brief",
    "Comparison Table": "comparison",
    "Timeline": "timeline",
}


def _status_label(is_ready: bool) -> str:
    return "Ready" if is_ready else "Needs setup"


def _render_capability_status() -> None:
    st.sidebar.subheader("Capability Status")

    ai_ready = bool(os.environ.get("OPENAI_API_KEY"))
    scraping_ready = True
    try:
        from backoffice.ingestion.intelligence.agents.scraper_agent import ScraperAgent  # noqa: F401
    except Exception:
        scraping_ready = False

    capability_rows = [
        ("Folder intelligence", True, "Local discovery, parsing, and analysis are available."),
        ("AI rewriting", ai_ready, "OpenAI-powered output enhancement for generated documents."),
        ("Web intelligence", scraping_ready, "Static, dynamic, and antibot scraping pipelines."),
    ]

    for label, ready, description in capability_rows:
        state = "OK" if ready else "WARN"
        st.sidebar.markdown(f"**{label}**")
        st.sidebar.caption(f"{state} - {_status_label(ready)}")
        st.sidebar.caption(description)


def _render_folder_inputs(prefix: str) -> dict[str, Any]:
    return {
        "folder_path": st.sidebar.text_input(
            "Folder path",
            key=f"{prefix}_folder_path",
            placeholder="C:/Users/you/Documents/project",
        ),
        "recursive": st.sidebar.toggle("Include sub-folders", value=True, key=f"{prefix}_recursive"),
        "max_file_size_mb": st.sidebar.slider(
            "Max file size (MB)",
            min_value=1,
            max_value=200,
            value=50,
            key=f"{prefix}_max_file_size_mb",
        ),
    }


def _render_action_inputs(workflow: str, action: str) -> dict[str, Any]:
    payload: dict[str, Any] = {}

    if workflow == "Workspace Reader":
        payload.update(_render_folder_inputs("workspace_reader"))
        payload["include_entity_preview"] = st.sidebar.toggle(
            "Preview extracted entities",
            value=action == "Analyze folder",
            key="workspace_reader_include_entity_preview",
        )

    elif workflow == "Document Factory":
        payload.update(_render_folder_inputs("document_factory"))
        selected_label = st.sidebar.selectbox(
            "Document type",
            options=list(OUTPUT_FORMAT_OPTIONS.keys()),
            index=1,
            key="document_factory_output_format_label",
        )
        payload["output_format"] = OUTPUT_FORMAT_OPTIONS[selected_label]
        payload["use_ai"] = st.sidebar.toggle(
            "Enhance with AI",
            value=True,
            key="document_factory_use_ai",
        )
        payload["save_output"] = st.sidebar.toggle(
            "Save generated file",
            value=True,
            key="document_factory_save_output",
        )
        payload["output_directory"] = st.sidebar.text_input(
            "Save directory",
            key="document_factory_output_directory",
            placeholder="Leave empty to save into the source folder",
        )
        payload["output_name"] = st.sidebar.text_input(
            "Output file name",
            value="generated_brief",
            key="document_factory_output_name",
            placeholder="generated_brief",
        )

    elif workflow == "Web Intelligence":
        payload["url"] = st.sidebar.text_input(
            "Target URL",
            key="web_intelligence_url",
            placeholder="https://example.com/news/product-launch",
        )
        payload["scraper_type"] = st.sidebar.selectbox(
            "Scraper mode",
            ["static", "dynamic", "antibot"],
            key="web_intelligence_scraper_type",
        )
        payload["data_type"] = st.sidebar.selectbox(
            "Expected data",
            ["product", "news", "price", "specs"],
            key="web_intelligence_data_type",
        )
        payload["save_output"] = st.sidebar.toggle(
            "Save intelligence brief",
            value=True,
            key="web_intelligence_save_output",
        )
        payload["output_directory"] = st.sidebar.text_input(
            "Save directory",
            key="web_intelligence_output_directory",
            placeholder="Leave empty to save in the workspace root",
        )
        payload["output_name"] = st.sidebar.text_input(
            "Brief file name",
            value="web_intelligence_brief",
            key="web_intelligence_output_name",
            placeholder="web_intelligence_brief",
        )

    return payload


def _render_quick_actions() -> str | None:
    st.sidebar.markdown("---")
    st.sidebar.subheader("Quick Actions")

    if st.sidebar.button("Open Document Analysis Page", width="stretch"):
        return "Document Analysis"
    if st.sidebar.button("Open Instruction Panel", width="stretch"):
        return "Instruction Panel"
    if st.sidebar.button("Reset to Dashboard", width="stretch"):
        return "Dashboard"

    return None


def render_sidebar() -> dict[str, Any]:
    st.markdown(
        """
        <style>
            section[data-testid=\"stSidebar\"] {
                width: 340px !important;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.sidebar.title("IS-BACKOFFICE")
    st.sidebar.caption("One sidebar, three workflows, each mapped to a real engine.")

    _render_capability_status()
    st.sidebar.markdown("---")

    workflow = st.sidebar.radio(
        "Primary workflow",
        list(WORKFLOWS.keys()),
        index=0,
        key="sidebar_workflow",
    )
    st.sidebar.caption(WORKFLOWS[workflow]["summary"])

    actions = WORKFLOWS[workflow]["actions"]
    action = st.sidebar.selectbox("Action", actions, index=0, key="sidebar_action")
    payload = _render_action_inputs(workflow, action)

    run_action = st.sidebar.button("Run workflow", type="primary", width="stretch")
    quick_action = _render_quick_actions()

    return {
        "workflow": workflow,
        "action": action,
        "payload": payload,
        "run_action": run_action,
        "quick_action": quick_action,
    }

