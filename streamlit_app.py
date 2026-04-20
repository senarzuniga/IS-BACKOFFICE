from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any

import streamlit as st

from backoffice import CommercialIntelligenceOS
from backoffice.exceptions import InvalidValueError, UnsupportedSourceTypeError


def _to_jsonable(value: Any) -> Any:
    if is_dataclass(value):
        return {k: _to_jsonable(v) for k, v in asdict(value).items()}
    if isinstance(value, dict):
        return {str(k): _to_jsonable(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_to_jsonable(item) for item in value]
    return value


def main() -> None:
    st.set_page_config(page_title="IS Backoffice", page_icon="📊", layout="wide")
    st.title("IS Backoffice")
    st.caption("Run one closed-loop cycle with the Backoffice orchestration engine.")

    with st.sidebar:
        st.header("Input")
        source_type = st.selectbox(
            "Source type",
            options=sorted(CommercialIntelligenceOS().ingestion.SUPPORTED),
            index=0,
        )
        source_id = st.text_input("Source ID", value="streamlit-001")
        classification = st.selectbox("Classification", options=["", "offer", "sale"], index=0)
        content = st.text_area(
            "Record content",
            value="client=ACME contact=ana@acme.com offer=Digital Roadmap price=25000 opportunity=Plant modernization value=80000 date=2026-01-10",
            height=180,
            help="Use key=value pairs separated by spaces or semicolons.",
        )
        run_cycle = st.button("Run cycle", type="primary")

    if not run_cycle:
        st.info("Configure the input and click **Run cycle**.")
        return

    osys = CommercialIntelligenceOS()
    try:
        metadata: dict[str, str] = {}
        if classification:
            metadata["classification"] = classification
        record = osys.ingestion.ingest_record(
            source_type=source_type,
            content=content,
            source_id=source_id.strip() or "streamlit-001",
            **metadata,
        )
        result = osys.run_cycle([record])
    except (UnsupportedSourceTypeError, InvalidValueError, ValueError) as error:
        st.error(str(error))
        return

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Graph nodes", result["knowledge_graph_nodes"])
    with col2:
        st.metric("Graph edges", result["knowledge_graph_edges"])
    with col3:
        st.metric("Dropped duplicates", result["processing"]["dropped_duplicates"])

    st.subheader("Cycle result")
    st.json(_to_jsonable(result), expanded=False)


if __name__ == "__main__":
    main()
