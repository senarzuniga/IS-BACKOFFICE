from __future__ import annotations

import json
from datetime import datetime
from typing import Any

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from .dashboard import render_default_dashboard


# ---------------------------------------------------------------------------
# Real document analysis result renderer
# ---------------------------------------------------------------------------

def _render_document_analysis_result(result: dict[str, Any]) -> None:
    """Render output from a real folder/URL analysis run."""
    source = result.get("folder_path") or result.get("url") or "—"
    st.subheader("📂 Document Analysis Results")

    cols = st.columns(4)
    cols[0].metric("Files processed", result.get("doc_count", result.get("file_count", 0)))
    cols[1].metric("Words analysed", f"{result.get('word_count', 0):,}")
    cols[2].metric("Cross-references", result.get("relationships", 0))
    cols[3].metric("Timeline events", result.get("timeline_events", 0))

    st.caption(f"Source: {source}")

    narrative = result.get("narrative", "")
    if narrative:
        st.markdown("**Overview**")
        st.write(narrative)

    themes = result.get("themes", [])
    if themes:
        st.markdown("**Key Themes**")
        theme_cols = st.columns(min(5, len(themes)))
        for i, theme in enumerate(themes[:10]):
            theme_cols[i % len(theme_cols)].markdown(f"`{theme}`")

    output_content = result.get("output_content", "")
    if output_content:
        st.markdown("---")
        st.markdown("**Generated Output**")
        fmt = result.get("output_format", "")
        if fmt == "database_entry":
            try:
                st.json(json.loads(output_content))
            except json.JSONDecodeError:
                st.warning("Output content is not valid JSON. Displaying as raw text.")
                st.code(output_content, language="json")
        else:
            st.markdown(output_content)
        st.download_button(
            "⬇️ Download as Markdown",
            data=output_content.encode("utf-8"),
            file_name=f"analysis_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
            mime="text/markdown",
        )

    errors = result.get("errors", [])
    if errors:
        with st.expander(f"⚠️ {len(errors)} parsing error(s)", expanded=False):
            for err in errors:
                st.warning(err)

    msg = result.get("message", "")
    if msg and not output_content:
        st.info(msg)


# ---------------------------------------------------------------------------
# Section-specific renderers
# ---------------------------------------------------------------------------

def _render_ingestion_results(result: dict[str, Any]) -> None:
    if result.get("type") == "document_analysis":
        _render_document_analysis_result(result)
        return

    st.subheader("Ingestion Results")

    msg = result.get("message", "")
    if msg:
        st.info(msg)
        return

    file_list = pd.DataFrame(
        [
            {"file": "q1_pipeline.csv", "status": "✅ processed"},
            {"file": "prospects.xlsx", "status": "⏳ queued"},
            {"file": "legacy_dump.json", "status": "❌ failed"},
        ]
    )
    st.dataframe(file_list, width="stretch")

    st.caption("Bulk operation progress")
    st.progress(0.72)

    preview = pd.DataFrame(
        [
            {"client": "ACME", "offer": "Digital Roadmap", "value": 25000, "region": "EU"},
            {"client": "Globex", "offer": "Optimization Program", "value": 48000, "region": "NA"},
        ]
    )
    st.markdown("Schema detected: client (str), offer (str), value (float), region (str)")
    st.dataframe(preview.head(100), width="stretch")

    with st.expander("View full data"):
        st.dataframe(preview, width="stretch")


def _render_cleaning_results(result: dict[str, Any]) -> None:
    st.subheader("Cleaning Results")

    msg = result.get("message", "")
    if msg:
        st.info(msg)
        return

    before = pd.DataFrame(
        [{"phone": "(555) 123-4567", "date": "01/12/2026", "amount": "25.000,00"}]
    )
    after = pd.DataFrame(
        [{"phone": "+15551234567", "date": "2026-12-01", "amount": "25000.00"}]
    )

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("Before")
        st.dataframe(before, width="stretch")
    with col2:
        st.markdown("After")
        st.dataframe(after, width="stretch")

    st.metric("Quality score", "94", delta="+12")

    issues = pd.DataFrame(
        [
            {"row": 14, "issue": "Invalid date format", "suggestion": "Convert to ISO-8601"},
            {"row": 21, "issue": "Possible duplicate", "suggestion": "Merge with row 17"},
        ]
    )
    st.dataframe(issues, width="stretch")

    for idx in range(len(issues)):
        c1, c2 = st.columns(2)
        with c1:
            st.button(f"Accept change {idx + 1}", key=f"accept_{idx}")
        with c2:
            st.button(f"Reject change {idx + 1}", key=f"reject_{idx}")


def _render_extraction_results(result: dict[str, Any]) -> None:
    if result.get("type") == "document_analysis":
        _render_document_analysis_result(result)
        return

    st.subheader("Extraction Results")

    msg = result.get("message", "")
    if msg:
        st.info(msg)
        return

    entities = pd.DataFrame(
        [
            {"entity": "ACME", "type": "Client", "confidence": 0.98, "context": "client=ACME"},
            {"entity": "Digital Roadmap", "type": "Offer", "confidence": 0.91, "context": "offer=Digital Roadmap"},
            {"entity": "80000", "type": "OpportunityValue", "confidence": 0.86, "context": "value=80000"},
        ]
    )
    st.dataframe(entities, width="stretch")

    hist = pd.DataFrame({"bucket": ["0.8-0.85", "0.86-0.9", "0.91-0.95", "0.96-1.0"], "count": [1, 1, 1, 1]})
    st.bar_chart(hist.set_index("bucket"))

    relations = pd.DataFrame(
        [
            {"source": "ACME", "relation": "HAS_OFFER", "target": "Digital Roadmap"},
            {"source": "Digital Roadmap", "relation": "LEADS_TO", "target": "Opportunity_1"},
        ]
    )
    st.markdown("Entity relationship diagram (adjacency table)")
    st.dataframe(relations, width="stretch")

    structured_output = entities.to_json(orient="records", indent=2)
    st.code(structured_output, language="json")
    st.download_button(
        "Copy structured output",
        data=structured_output,
        file_name="extracted_entities.json",
        mime="application/json",
    )


def _render_graph_results(result: dict[str, Any]) -> None:
    st.subheader("Graph Results")

    msg = result.get("message", "")
    if msg:
        st.info(msg)
        return

    html = """
    <html>
      <body style='font-family: sans-serif;'>
        <h4>Interactive network preview</h4>
        <p>Graph module requires ingested data. Use Ingestion first.</p>
      </body>
    </html>
    """
    components.html(html, height=220)


def _render_analytics_results(result: dict[str, Any]) -> None:
    st.subheader("Analytics Results")

    msg = result.get("message", "")
    if msg:
        st.info(msg)
        return

    chart_df = pd.DataFrame(
        {
            "month": ["Jan", "Feb", "Mar", "Apr", "May"],
            "revenue": [42000, 45000, 47000, 53000, 56000],
            "forecast": [43000, 45500, 49000, 52500, 57000],
        }
    )
    st.line_chart(chart_df.set_index("month"))

    st.success("Trend insight: Revenue growth trajectory remains positive.")
    st.info("Correlation insight: Offer discounting strongly affects conversion in SMB segment.")
    st.warning("Anomaly insight: Region South had a sudden drop in April activity.")

    table = pd.DataFrame(
        [
            {"account": "ACME", "score": 92, "anomaly": "No"},
            {"account": "Globex", "score": 77, "anomaly": "Yes"},
        ]
    )
    st.dataframe(table.style.highlight_max(axis=0), width="stretch")

    st.download_button(
        "Download results",
        data=table.to_csv(index=False),
        file_name="analytics_results.csv",
        mime="text/csv",
    )


def _render_reporting_results(result: dict[str, Any]) -> None:
    st.subheader("Reporting Results")

    msg = result.get("message", "")
    if msg:
        st.info(msg)
        return

    preview_html = """
    <div style='padding: 10px; border: 1px solid #e5e5e5; border-radius: 8px;'>
      <h4>Executive Summary Preview</h4>
      <p>Revenue grew 8.2% month-over-month with stronger enterprise conversion.</p>
    </div>
    """
    st.markdown(preview_html, unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    c1.download_button("Download PDF", data="placeholder", file_name="report.pdf")
    c2.download_button("Download Excel", data="placeholder", file_name="report.xlsx")
    c3.download_button("Download PPT", data="placeholder", file_name="report.pptx")
    c4.download_button("Download DOCX", data="placeholder", file_name="report.docx")

    st.success("Email status: Report sent to configured recipients.")
    st.info("Scheduling confirmation: Weekly report job active.")


def render_main_content() -> None:
    current_section = st.session_state.get("current_section", "")
    current_action = st.session_state.get("current_action", "")
    last_result = st.session_state.get("last_result")

    if not current_section or not current_action or not last_result:
        render_default_dashboard()
        return

    section = current_section
    # Use the real result stored in session state instead of hardcoded mock data
    result = last_result

    st.markdown(f"### Active module: {section}")
    st.caption(result.get("message", result.get("summary", "")))

    if section == "📥 INGESTION":
        _render_ingestion_results(result)
    elif section == "🧹 CLEANING":
        _render_cleaning_results(result)
    elif section == "🔍 EXTRACTION":
        _render_extraction_results(result)
    elif section == "🕸️ GRAPH":
        _render_graph_results(result)
    elif section == "📊 ANALYTICS":
        _render_analytics_results(result)
    elif section == "📑 REPORTING":
        _render_reporting_results(result)
    else:
        render_default_dashboard()
