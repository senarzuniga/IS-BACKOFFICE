from __future__ import annotations

import os

import requests
import streamlit as st

API_URL = os.getenv("IS_BACKOFFICE_API_URL", "http://localhost:8000")


def _safe_get(path: str):
    try:
        response = requests.get(f"{API_URL}{path}", timeout=20)
        response.raise_for_status()
        return response.json(), None
    except Exception as exc:  # noqa: BLE001
        return None, str(exc)


def _safe_post(path: str, payload: dict):
    try:
        response = requests.post(f"{API_URL}{path}", json=payload, timeout=30)
        response.raise_for_status()
        return response.json(), None
    except Exception as exc:  # noqa: BLE001
        return None, str(exc)


def main() -> None:
    st.set_page_config(page_title="IS Backoffice Control Tower", page_icon="📈", layout="wide")
    st.title("IS Backoffice Control Tower")
    st.caption("Streamlit UI calling FastAPI endpoints only.")

    health, health_err = _safe_get("/health")
    if health_err:
        st.error(f"Backend unavailable at {API_URL}: {health_err}")
        st.stop()
    st.success(f"Backend healthy at {API_URL}: {health}")

    st.subheader("Quick Analytics")
    if st.button("Get Pipeline"):
        data, err = _safe_get("/analytics/pipeline")
        if err:
            st.error(err)
        else:
            st.json(data)

    if st.button("Get Forecast"):
        data, err = _safe_get("/analytics/forecast")
        if err:
            st.error(err)
        else:
            st.json(data)

    st.subheader("Run Multi-Agent Cycle")
    source_type = st.selectbox("Source type", ["txt", "pdf", "word", "excel", "crm", "outlook_email", "folder_scan"])
    source_id = st.text_input("Source ID", value="streamlit-control-001")
    classification = st.selectbox("Classification", ["", "offer", "sale"])
    content = st.text_area(
        "Record content",
        value="client=ACME contact=ana@acme.com offer=Digital Roadmap price=25000 opportunity=Plant modernization value=80000 date=2026-01-10",
        height=150,
    )
    proactive_mode = st.checkbox("Proactive mode", value=True)
    autolearning_mode = st.checkbox("Autolearning mode", value=True)
    strict_mode = st.checkbox("Strict mode", value=False)

    if st.button("Run Agent Pipeline", type="primary"):
        payload = {
            "source_type": source_type,
            "source_id": source_id,
            "content": content,
            "classification": classification or None,
            "proactive_mode": proactive_mode,
            "autolearning_mode": autolearning_mode,
            "strict_mode": strict_mode,
        }
        data, err = _safe_post("/orchestration/agents/run", payload)
        if err:
            st.error(err)
        else:
            st.json(data)


if __name__ == "__main__":
    main()
