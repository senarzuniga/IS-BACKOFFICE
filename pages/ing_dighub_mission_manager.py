from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict, List

import streamlit as st

from backoffice.spoe.governance import update_governance_artifacts
from backoffice.spoe.mission_manager import run_ame_iteration


REPO_ROOT = Path(__file__).resolve().parent.parent
RUNTIME_FILE = REPO_ROOT / "reports" / "ing_dighub" / "mission_runtime.json"


def _load_runtime() -> Dict[str, Any]:
    if not RUNTIME_FILE.exists():
        initial = {
            "updated_at": datetime.now(UTC).isoformat(),
            "missions": [
                {
                    "id": "M-001",
                    "name": "SPOE Governance Mission",
                    "status": "completed",
                    "mission_health": 83.56,
                    "mission_score": 88.91,
                    "hypothesis_score": 88.91,
                    "engineering_return": 8.8,
                    "business_return": 8.7,
                    "knowledge_return": 9.0,
                    "last_update": datetime.now(UTC).isoformat(),
                },
                {
                    "id": "M-002",
                    "name": "ING_DIGHUB Capability Sync",
                    "status": "queued",
                    "mission_health": 74.0,
                    "mission_score": 76.0,
                    "hypothesis_score": 72.0,
                    "engineering_return": 7.5,
                    "business_return": 7.2,
                    "knowledge_return": 7.1,
                    "last_update": datetime.now(UTC).isoformat(),
                },
            ],
        }
        RUNTIME_FILE.parent.mkdir(parents=True, exist_ok=True)
        RUNTIME_FILE.write_text(json.dumps(initial, indent=2), encoding="utf-8")
        return initial

    try:
        return json.loads(RUNTIME_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"updated_at": datetime.now(UTC).isoformat(), "missions": []}


def _save_runtime(runtime: Dict[str, Any]) -> None:
    runtime["updated_at"] = datetime.now(UTC).isoformat()
    RUNTIME_FILE.parent.mkdir(parents=True, exist_ok=True)
    RUNTIME_FILE.write_text(json.dumps(runtime, indent=2), encoding="utf-8")


def _counts(missions: List[Dict[str, Any]]) -> Dict[str, int]:
    return {
        "running": sum(1 for m in missions if m.get("status") == "running"),
        "queued": sum(1 for m in missions if m.get("status") == "queued"),
        "completed": sum(1 for m in missions if m.get("status") == "completed"),
    }


def _update_status(runtime: Dict[str, Any], mission_id: str, status: str) -> Dict[str, Any]:
    for mission in runtime.get("missions", []):
        if mission.get("id") == mission_id:
            mission["status"] = status
            mission["last_update"] = datetime.now(UTC).isoformat()
    _save_runtime(runtime)
    return runtime


def main() -> None:
    st.set_page_config(page_title="ING_DIGHUB Mission Manager", page_icon="🎯", layout="wide")
    try:
        from backoffice.theme import inject_theme
        inject_theme()
    except Exception:
        pass
    st.title("🎯 Mission Manager")
    st.caption("Connected to existing AME mission manager and governance modules")

    runtime = _load_runtime()
    missions = runtime.get("missions", [])
    counts = _counts(missions)

    c1, c2, c3 = st.columns(3)
    c1.metric("Running Missions", counts["running"])
    c2.metric("Queued Missions", counts["queued"])
    c3.metric("Completed Missions", counts["completed"])

    st.dataframe(missions, use_container_width=True)

    if not missions:
        st.warning("No missions available.")
        return

    selected_id = st.selectbox("Mission", options=[m["id"] for m in missions])

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("Resume Mission", use_container_width=True):
            runtime = _update_status(runtime, selected_id, "running")
            st.success("Mission resumed")
    with col2:
        if st.button("Pause Mission", use_container_width=True):
            runtime = _update_status(runtime, selected_id, "queued")
            st.success("Mission paused")
    with col3:
        if st.button("Review Mission", use_container_width=True):
            selected = next((m for m in runtime.get("missions", []) if m.get("id") == selected_id), None)
            if selected:
                st.json(selected)
    with col4:
        if st.button("Generate Report", type="primary", use_container_width=True):
            result = run_ame_iteration()
            artifacts = update_governance_artifacts(result)

            selected = next((m for m in runtime.get("missions", []) if m.get("id") == selected_id), None)
            if selected:
                selected["status"] = "completed"
                selected["mission_health"] = result.get("platform_score", {}).get("global_platform_score", selected.get("mission_health"))
                selected["mission_score"] = result.get("hypotheses", {}).get("selected", {}).get("global_engineering_score", selected.get("mission_score"))
                selected["hypothesis_score"] = selected["mission_score"]
                selected["last_update"] = datetime.now(UTC).isoformat()
                _save_runtime(runtime)

            st.success("Mission report generated and governance artifacts updated")
            st.json({"mission_result": result, "artifacts": artifacts})


if __name__ == "__main__":
    main()
