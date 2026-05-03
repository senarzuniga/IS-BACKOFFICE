from __future__ import annotations

import traceback
from datetime import datetime
from typing import Any

import streamlit as st

st.set_page_config(layout="wide", page_title="Virtual Back Office", page_icon="🏢")

from backoffice.ui.components.results import render_main_content
from backoffice.ui.components.sidebar import render_sidebar


def _initialize_state() -> None:
    defaults: dict[str, Any] = {
        "current_section": "",
        "current_action": "",
        "last_result": None,
        "last_payload": {},
        "processing_queue": [],
        "settings": {"theme": "light", "timezone": "UTC", "notifications": True},
        "last_activity": datetime.now().isoformat(timespec="seconds"),
        "memory_usage": 87,
        "status_logs": ["UI initialized"],
        "last_error": None,
        "module_health": {
            "ingestion": True,
            "cleaning": True,
            "extraction": True,
            "graph": True,
            "analytics": True,
            "reporting": True,
        },
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _append_log(message: str) -> None:
    ts = datetime.now().strftime("%H:%M:%S")
    st.session_state["status_logs"].append(f"[{ts}] {message}")
    st.session_state["last_activity"] = datetime.now().isoformat(timespec="seconds")


def _run_placeholder_operation(section: str, action: str, payload: dict[str, Any]) -> dict[str, Any]:
    _append_log(f"Queued operation: {section} / {action}")

    with st.status("Processing...", expanded=True) as status:
        st.write("Step 1: Loading data...")
        st.write("Step 2: Cleaning...")
        st.write("Step 3: Computing outputs...")
        status.update(label="Complete!", state="complete")

    return {
        "section": section,
        "action": action,
        "status": "complete",
        "payload": payload,
        "completed_at": datetime.now().isoformat(timespec="seconds"),
        "message": f"Placeholder execution completed for {action}.",
    }


def _render_error_state() -> None:
    error = st.session_state.get("last_error")
    if not error:
        return

    st.error(f"{error['type']}: {error['message']}")
    with st.expander("Stack trace", expanded=False):
        st.code(error["trace"], language="text")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Retry", key="retry_error"):
            st.session_state["last_error"] = None
            st.rerun()
    with c2:
        if st.button("Report bug", key="report_error"):
            _append_log("Bug report requested from UI")
            st.info("Bug report logged to status panel.")


def _handle_quick_action(label: str) -> None:
    if label == "Document Analysis":
        st.switch_page("pages/document_analysis.py")
        return
    if label == "Instruction Panel":
        st.switch_page("pages/instruction_panel.py")
        return

    _QUICK_ACTION_MAP: dict[str, tuple[str, str]] = {
        "Process All New Files": ("📥 INGESTION", "Bulk import"),
        "Today's Dashboard": ("", ""),
        "Ask AI Assistant": ("📊 ANALYTICS", "Natural language query"),
        "Create Summary": ("📑 REPORTING", "Generate report"),
        "Settings": ("📑 REPORTING", "View report history"),
    }

    if label not in _QUICK_ACTION_MAP:
        return

    section, action = _QUICK_ACTION_MAP[label]
    st.session_state["current_section"] = section
    st.session_state["current_action"] = action

    # Set a completed result immediately so render_main_content shows the correct
    # panel on the next render cycle (without requiring a separate "Run" click).
    if section and action:
        st.session_state["last_result"] = {
            "section": section,
            "action": action,
            "status": "complete",
            "payload": {},
            "completed_at": datetime.now().isoformat(timespec="seconds"),
            "message": f"Quick action triggered: {label}. Adjust options and click "
                       "Run Selected Action to re-execute with custom settings.",
        }
    else:
        # Dashboard — reset result to show the default view
        st.session_state["last_result"] = None

    _append_log(f"Quick action: {label}")
    st.rerun()


def _run_selected_action(sidebar_state: dict[str, Any]) -> None:
    section = sidebar_state.get("section", "")
    action = sidebar_state.get("action", "")
    payload = sidebar_state.get("payload", {})

    if not section or not action:
        return

    try:
        result = _run_placeholder_operation(section, action, payload)
        st.session_state["current_section"] = section
        st.session_state["current_action"] = action
        st.session_state["last_payload"] = payload
        st.session_state["last_result"] = result
        st.session_state["processing_queue"].append(
            {
                "section": section,
                "action": action,
                "status": result.get("status", "complete"),
                "time": result.get("completed_at", datetime.now().isoformat(timespec="seconds")),
            }
        )
        st.session_state["last_error"] = None
        _append_log(f"Completed operation: {section} / {action}")
        st.rerun()
    except Exception as exc:  # noqa: BLE001
        st.session_state["last_error"] = {
            "type": type(exc).__name__,
            "message": str(exc),
            "trace": traceback.format_exc(),
        }
        _append_log(f"Operation failed: {section} / {action} -> {type(exc).__name__}")


def _render_status_bar() -> None:
    st.markdown("---")
    with st.expander("Status Bar", expanded=True):
        queue = st.session_state.get("processing_queue", [])
        st.caption(f"Pending tasks: {len([item for item in queue if item.get('status') != 'complete'])}")
        for line in st.session_state.get("status_logs", [])[-12:]:
            st.write(line)


def main() -> None:
    _initialize_state()

    st.markdown("# Virtual Back Office Human Interface")
    st.write("Hello World")

    sidebar_state = render_sidebar()

    quick_action = sidebar_state.get("quick_action")
    if quick_action:
        _handle_quick_action(quick_action)

    if sidebar_state.get("run_action"):
        _run_selected_action(sidebar_state)

    _render_error_state()

    render_main_content()
    _render_status_bar()


if __name__ == "__main__":
    main()
