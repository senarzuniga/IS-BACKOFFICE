from __future__ import annotations

from datetime import datetime

import pandas as pd
import streamlit as st


def render_default_dashboard() -> None:
    today = datetime.now().strftime("%Y-%m-%d")

    st.markdown("## Virtual Back Office")
    st.markdown(f"Welcome to your operations console. Date: **{today}**")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Files Processed Today", "1,248", delta="+12%")
    col2.metric("Entities Extracted", "14,521", delta="+6%")
    col3.metric("Reports Generated", "83", delta="+4")
    col4.metric("Tasks Pending", "17", delta="-3")

    st.markdown("### Recent Activity Feed")
    activity = pd.DataFrame(
        [
            {"time": "08:10", "action": "Ingest local files", "status": "processed", "owner": "automation"},
            {"time": "08:22", "action": "Run deduplication", "status": "complete", "owner": "data-ops"},
            {"time": "08:35", "action": "Extract entities from text", "status": "complete", "owner": "nlp-engine"},
            {"time": "08:48", "action": "Graph statistics", "status": "complete", "owner": "graph-service"},
            {"time": "09:03", "action": "Generate report", "status": "queued", "owner": "reporting"},
        ]
    )
    st.dataframe(activity.head(20), width="stretch")

    st.markdown("### Quick Health Overview")
    with st.expander("Ingestion", expanded=True):
        st.success("Healthy: connectors responsive")
    with st.expander("Cleaning", expanded=False):
        st.info("Healthy: quality checks in expected range")
    with st.expander("Extraction", expanded=False):
        st.warning("Latency elevated for large PDFs")
    with st.expander("Graph", expanded=False):
        st.success("Healthy: relationship index up to date")

