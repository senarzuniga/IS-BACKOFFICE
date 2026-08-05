from __future__ import annotations

import json
import os
from typing import Any, Dict, List

import requests
import streamlit as st


def _api_base() -> str:
    return (os.environ.get("BACKOFFICE_API_URL") or "http://localhost:8000").rstrip("/")


def _safe_get(path: str) -> Dict[str, Any]:
    try:
        res = requests.get(f"{_api_base()}{path}", timeout=20)
        return {"status_code": res.status_code, "body": res.json()}
    except Exception as exc:
        return {"status_code": 0, "body": {"status": "error", "detail": str(exc)}}


def _safe_post(path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    try:
        res = requests.post(f"{_api_base()}{path}", json=payload, timeout=60)
        return {"status_code": res.status_code, "body": res.json()}
    except Exception as exc:
        return {"status_code": 0, "body": {"status": "error", "detail": str(exc)}}


def _render_module_table(modules: List[Dict[str, Any]]) -> None:
    st.subheader("Industrial Engineering Modules")
    if not modules:
        st.warning("No modules received from backend.")
        return
    st.dataframe(modules, use_container_width=True)


def main() -> None:
    st.set_page_config(page_title="Industrial Engineering Platform", page_icon="🏗️", layout="wide")
    st.title("ING_DIGHUB Industrial Engineering Platform")
    st.caption("AI-FACTORY as Cognitive Operating System | API-first integration")

    modules_resp = _safe_get("/ing-dighub/modules")
    modules = modules_resp.get("body", {}).get("modules", [])
    _render_module_table(modules)

    tab1, tab2, tab3 = st.tabs([
        "Mission Manager UI",
        "Engineering Workbench",
        "Executive Dashboards",
    ])

    with tab1:
        st.markdown("### Autonomous Mission Loop")
        mission = st.text_input(
            "Mission",
            value="Continue evolving ING_DIGHUB as the Industrial Engineering Platform",
        )
        col_a, col_b = st.columns(2)
        with col_a:
            max_iterations = st.number_input("Max iterations", min_value=1, max_value=50, value=8, step=1)
        with col_b:
            min_expected_value = st.number_input("Minimum expected value", value=0.0, step=0.1)

        context_txt = st.text_area(
            "Mission context (JSON)",
            value=json.dumps({"portfolio": "industrial", "platform": "ING_DIGHUB"}, indent=2),
            height=180,
        )

        if st.button("Run Hypothesis → Scoring → Selection → Validation", type="primary"):
            try:
                context_payload = json.loads(context_txt or "{}")
            except json.JSONDecodeError as exc:
                st.error(f"Invalid JSON context: {exc}")
                context_payload = None

            if context_payload is not None:
                result = _safe_post(
                    "/ing-dighub/autonomy/run",
                    {
                        "mission": mission,
                        "context": context_payload,
                        "max_iterations": int(max_iterations),
                        "min_expected_value": float(min_expected_value),
                    },
                )
                st.json(result.get("body", {}))

    with tab2:
        st.markdown("### Module Execution")
        module_keys = [m.get("key") for m in modules if m.get("key")]
        selected_module = st.selectbox("Select module", options=module_keys)
        exec_context = st.text_area(
            "Execution context (JSON)",
            value=json.dumps({"request": "sync status and next action"}, indent=2),
            height=160,
        )

        if st.button("Execute Module via AI-FACTORY API"):
            try:
                payload = json.loads(exec_context or "{}")
            except json.JSONDecodeError as exc:
                st.error(f"Invalid JSON context: {exc}")
                payload = None
            if payload is not None and selected_module:
                result = _safe_post(f"/ing-dighub/modules/{selected_module}/execute", {"context": payload})
                st.json(result.get("body", {}))

    with tab3:
        st.markdown("### Executive Dashboards")
        st.info(
            "Dashboard metrics are driven by AI-FACTORY outputs from module executions "
            "and autonomy loop history."
        )
        st.metric("Configured Modules", len(modules))
        st.metric("Backend API", _api_base())


if __name__ == "__main__":
    main()
