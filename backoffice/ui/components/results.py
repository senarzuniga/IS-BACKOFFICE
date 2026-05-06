from __future__ import annotations

import json

import pandas as pd
import streamlit as st

from .dashboard import render_default_dashboard


def _render_folder_scan(result: dict[str, object]) -> None:
    stats = result.get("folder_stats", {}) or {}
    files = result.get("files", []) or []

    col1, col2, col3 = st.columns(3)
    col1.metric("Total files", stats.get("total_files", 0))
    col2.metric("Supported files", stats.get("supported_files", 0))
    col3.metric("Total size (MB)", round((stats.get("total_size_bytes", 0) or 0) / (1024 * 1024), 2))

    st.caption(result.get("folder_path", ""))
    if files:
        st.dataframe(pd.DataFrame(files), width="stretch")
    else:
        st.info("No files found for this folder.")


def _render_folder_analysis(result: dict[str, object]) -> None:
    analysis = result.get("analysis", {}) or {}
    files = result.get("files", []) or []
    documents = analysis.get("documents", []) or []

    st.subheader("Analysis Summary")
    st.write(analysis.get("narrative", "No narrative generated."))

    col1, col2, col3 = st.columns(3)
    col1.metric("Documents parsed", len(documents))
    col2.metric("Themes", len(analysis.get("cross_themes", []) or []))
    col3.metric("Timeline events", len(analysis.get("timeline", []) or []))

    themes = analysis.get("cross_themes", []) or []
    if themes:
        st.markdown("### Shared Themes")
        st.write(", ".join(themes[:15]))

    gaps = analysis.get("gaps", []) or []
    if gaps:
        st.markdown("### Gaps")
        for item in gaps:
            st.write(f"- {item}")

    if result.get("include_entity_preview") and documents:
        entities = []
        for doc in documents:
            for entity in doc.get("entities", [])[:20]:
                entities.append(
                    {
                        "document": doc.get("file_name"),
                        "entity": entity.get("text"),
                        "type": entity.get("entity_type"),
                        "confidence": entity.get("confidence"),
                    }
                )
        if entities:
            st.markdown("### Entity Preview")
            st.dataframe(pd.DataFrame(entities), width="stretch")

    st.markdown("### Files")
    st.dataframe(pd.DataFrame(files), width="stretch")


def _render_document_output(result: dict[str, object]) -> None:
    output = result.get("output", {}) or {}
    analysis = result.get("analysis", {}) or {}

    col1, col2, col3 = st.columns(3)
    col1.metric("Output words", output.get("word_count", 0))
    col2.metric("Themes", len(analysis.get("cross_themes", []) or []))
    col3.metric("AI enhanced", "Yes" if output.get("ai_enhanced") else "No")

    if result.get("saved_to"):
        st.success(f"Saved to {result['saved_to']}")

    if result.get("ai_requested") and not result.get("ai_available"):
        st.warning("AI enhancement was requested, but OPENAI_API_KEY is not configured. Fallback analysis was used.")

    st.markdown("### Generated Document")
    content = output.get("content", "")
    if content:
        st.markdown(content)
        file_name = output.get("title", "generated_output").replace(" ", "_").lower()
        mime = "application/json" if output.get("output_format") == "database_entry" else "text/markdown"
        suffix = ".json" if mime == "application/json" else ".md"
        st.download_button(
            "Download generated file",
            data=content,
            file_name=f"{file_name}{suffix}",
            mime=mime,
        )

    structured_data = output.get("structured_data") or {}
    if structured_data:
        with st.expander("Structured Data", expanded=False):
            st.code(json.dumps(structured_data, indent=2, ensure_ascii=False, default=str), language="json")


def _render_web_intelligence(result: dict[str, object]) -> None:
    scraper = result.get("scraper", {}) or {}
    intelligence = result.get("intelligence", []) or []

    col1, col2, col3 = st.columns(3)
    col1.metric("Signals", len(intelligence))
    col2.metric("Confidence", f"{round((result.get('confidence_score', 0.0) or 0.0) * 100, 1)}%")
    col3.metric("Response time (ms)", round(scraper.get("response_time_ms", 0) or 0, 1))

    st.caption(result.get("url", ""))
    if result.get("saved_to"):
        st.success(f"Saved to {result['saved_to']}")

    st.markdown("### Structured Extraction")
    st.code(json.dumps(result.get("extracted", {}), indent=2, ensure_ascii=False, default=str), language="json")

    st.markdown("### Intelligence Outputs")
    if intelligence:
        for item in intelligence:
            st.markdown(f"**{item.get('title', 'Untitled signal')}**")
            st.write(item.get("description", ""))
            st.caption(f"Impact: {item.get('impact', 'unknown')} | Action: {item.get('suggested_action', 'n/a')}")
    else:
        st.info("No intelligence outputs were generated from this page.")


def render_main_content() -> None:
    result = st.session_state.get("last_result")

    if not result:
        render_default_dashboard()
        return

    st.markdown(f"## {result.get('workflow', 'Workflow result')}")
    st.caption(result.get("summary", ""))

    kind = result.get("kind")
    if kind == "folder_scan":
        _render_folder_scan(result)
    elif kind == "folder_analysis":
        _render_folder_analysis(result)
    elif kind == "document_output":
        _render_document_output(result)
    elif kind == "web_intelligence":
        _render_web_intelligence(result)
    else:
        render_default_dashboard()

