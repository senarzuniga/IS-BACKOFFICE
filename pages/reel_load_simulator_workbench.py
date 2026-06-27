"""Reel Load Simulator — Engineering Workbench (Presentation Layer)

Minimal, architecture-aligned Presentation Layer skeleton.

This page implements the required top-level tabs: PROJECT, SIMULATION,
ANALYTICS, HISTORY and a hidden ENGINEERING tab. It strictly consumes
outputs produced by the Simulation Engine (via the existing runner)
and does not implement simulation calculations.

Progressive migration: this workbench is a non-invasive UI that reuses
existing engine artifacts (scenario YAMLs and `scripts/run_simulator.py`).
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import streamlit as st
import os
import time
import requests

try:
    from ingetrans_simulator import advanced_charts as charts
except Exception:
    charts = None

# Paths
ROOT = Path(__file__).resolve().parent.parent
SIM_ROOT = ROOT / "ingetrans-reel-simulator"
RUN_SCRIPT = SIM_ROOT / "scripts" / "run_simulator.py"


def _list_scenarios() -> List[str]:
    scen_dir = SIM_ROOT / "06_SCENARIOS"
    if not scen_dir.exists():
        return []
    return sorted([str(p) for p in scen_dir.glob("*.yaml")])


def _run_headless_simulation(scenario_path: str, duration_s: int, tick: float = 1.0) -> Dict[str, Any]:
    """Submit the simulation as a job to the Job API and poll for the run summary.

    The Presentation Layer must not perform simulation calculations locally.
    Uses `SIMULATOR_API_URL` env var (default http://localhost:8000).
    """
    api_url = os.environ.get("SIMULATOR_API_URL", "http://localhost:8000")
    payload = {"scenario": scenario_path, "duration_s": duration_s, "tick_s": tick, "seed": 42}
    try:
        resp = requests.post(f"{api_url}/run", json=payload, timeout=10)
    except requests.RequestException as e:
        return {"error": "api_unreachable", "exc": str(e), "hint": "Start the Job API with: uvicorn api.simulator_api:app --reload --port 8000"}
    if resp.status_code != 200:
        return {"error": "api_error", "status_code": resp.status_code, "text": resp.text}

    job_id = resp.json().get("job_id")
    if not job_id:
        return {"error": "no_job_id", "resp": resp.text}

    start = time.time()
    timeout = duration_s + 120
    with st.spinner(f"Job queued ({job_id}). Esperando resultado..."):
        while True:
            try:
                r = requests.get(f"{api_url}/status/{job_id}", timeout=10)
            except requests.RequestException as e:
                return {"error": "poll_error", "exc": str(e)}
            if r.status_code != 200:
                time.sleep(1)
                if time.time() - start > timeout:
                    return {"error": "timeout", "detail": f"Polling timed out after {timeout}s"}
                continue
            data = r.json()
            status = data.get("status")
            if status == "running":
                time.sleep(1)
                if time.time() - start > timeout:
                    return {"error": "timeout", "detail": f"Polling timed out after {timeout}s"}
                continue
            if status == "finished":
                return data.get("result", {})
            if status == "failed":
                return {"error": "job_failed", "detail": data.get("error")}
            time.sleep(1)


def _read_run_summaries() -> List[Dict[str, Any]]:
    out_base = SIM_ROOT / "outputs"
    if not out_base.exists():
        return []
    runs = sorted([p for p in out_base.iterdir() if p.is_dir()], key=lambda p: p.name, reverse=True)
    summaries = []
    for r in runs:
        p = r / "run_summary.json"
        try:
            summaries.append(json.loads(p.read_text(encoding="utf-8")))
        except Exception:
            continue
    return summaries


def render_project_tab():
    st.header("PROJECT")
    st.markdown("Quick Configuration")
    preset = st.selectbox("Preset", ["Standard EU Factory"], index=0)

    scenario_files = _list_scenarios()
    default_scenario = scenario_files[0] if scenario_files else ""

    st.markdown("**Preset loaded:** Standard EU Factory")
    if default_scenario:
        st.markdown(f"**Scenario:** {Path(default_scenario).name}")
        # Display a minimal summary sourced from the scenario YAML when present.
        try:
            import yaml

            s = yaml.safe_load(Path(default_scenario).read_text(encoding="utf-8")) or {}
            # Only echo values from the scenario; do not compute anything.
            st.write({k: v for k, v in s.items() if k in ("geometry", "corrugator", "warehouse", "forklift", "transfer")})
        except Exception:
            st.write("Scenario summary not available in YAML.")

    st.markdown("---")
    st.markdown("### Start Simulation")
    shift_minutes = st.number_input("Shift length (min)", value=480, min_value=15, step=15)
    shifts = st.number_input("Shifts to simulate", value=1, min_value=1, step=1)
    duration = int(shift_minutes * shifts * 60)
    tick = st.number_input("Tick (s)", value=1.0, min_value=0.1, step=0.1)

    if st.button("▶ START SIMULATION", key="start_sim"):
        with st.spinner("Running simulation (engine)..."):
            res = _run_headless_simulation(default_scenario, duration, tick)
        if res.get("error"):
            st.error(f"Simulation failed: {res.get('error')}")
            st.text(res.get("stderr", ""))
        else:
            st.success("Simulation completed")
            st.json(res)
            st.session_state["last_run_summary"] = res

    st.markdown("---")
    if st.button("Advanced Configuration"):
        # Reuse existing advanced pages instead of duplicating logic
        try:
            st.session_state["nav_to"] = "reel_load_simulator_fixed"
            st.experimental_rerun()
        except Exception:
            st.info("Open Advanced Configuration manually from Pages list.")


def render_simulation_tab():
    st.header("SIMULATION")
    # Toolbar
    col1, col2, col3 = st.columns([1, 4, 2])
    with col1:
        if st.button("Play"):
            st.info("Play pressed — control is visual-only in this skeleton.")
        if st.button("Pause"):
            st.info("Pause pressed")
    with col2:
        speed = st.selectbox("Simulation Speed", ["Real Time", "2x", "5x", "10x", "20x", "100x", "Unlimited"], index=0)
    with col3:
        st.checkbox("Follow Resource", value=False)

    st.markdown("---")
    left, right = st.columns([1, 1])
    with left:
        st.subheader("Forklift Scenario")
        st.info("Visual viewer placeholder — integrate engine renderer here.")
    with right:
        st.subheader("INGETRANS Scenario")
        st.info("Visual viewer placeholder — integrate engine renderer here.")

    st.markdown("---")
    st.subheader("Live KPI Panel")
    rs = st.session_state.get("last_run_summary")
    if rs:
        st.metric("Completed Orders", rs.get("completed_orders", "—"))
        st.metric("Throughput (rolls/h)", f"{rs.get('throughput_rolls_per_hour', '—')}")
    else:
        st.info("No run yet — start a simulation from the Project tab.")


def render_analytics_tab():
    st.header("ANALYTICS")
    st.markdown("Display engine-produced KPIs and reports. The UI must not calculate core metrics.")
    # show latest run summary
    summaries = _read_run_summaries()
    if not summaries:
        st.info("No simulation outputs found. Run a simulation first.")
        return
    latest = summaries[0]
    st.subheader("Latest Run Summary")
    st.json(latest)

    st.markdown("---")
    if charts is not None:
        try:
            # Choose chart type heuristically
            st.plotly_chart(charts.build_sankey_flow(scenario="a"), use_container_width=True)
        except Exception:
            st.info("Advanced charts unavailable for these outputs — extend engine API if needed.")
    else:
        st.info("Advanced charts module not installed. Install or provide engine KPIs for rich analytics.")


def render_history_tab():
    st.header("HISTORY")
    summaries = _read_run_summaries()
    if not summaries:
        st.info("No past runs found.")
        return
    for s in summaries:
        with st.expander(f"{s.get('run_id')} — {s.get('scenario')} — {s.get('run_duration_s')}s"):
            st.json(s)
            if st.button("Replay", key=f"replay_{s.get('run_id')}"):
                st.info("Replay is a future enhancement — will load run for visual replay.")


def main():
    st.set_page_config(page_title="Reel Load Workbench", page_icon="📦", layout="wide")

    st.markdown("# Reel Load Simulator — Workbench")

    # Top-level tabs
    tabs = st.tabs(["PROJECT", "SIMULATION", "ANALYTICS", "HISTORY"])  # ENGINEERING hidden by default
    with tabs[0]:
        render_project_tab()
    with tabs[1]:
        render_simulation_tab()
    with tabs[2]:
        render_analytics_tab()
    with tabs[3]:
        render_history_tab()


if __name__ == "__main__":
    main()
