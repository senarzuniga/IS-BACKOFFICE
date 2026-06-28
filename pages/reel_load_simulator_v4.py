"""Reel Load Simulator V4 — Streamlit UI page

Provides a professional UI styled like `plant_simulator.py`. Uses the minimal
headless runner in `ingetrans-reel-simulator/scripts/run_simulator.py` to execute
scenarios and visualizes outputs (summary + Sankey + KPI cards).
"""
from __future__ import annotations
import os
import sys
import json
import subprocess
import time
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, Optional

import streamlit as st
import plotly.graph_objects as go
import requests
try:
    from ingetrans_simulator import advanced_charts as charts
except Exception:
    charts = None

# Page config + styling consistent with plant_simulator
st.set_page_config(page_title="Reel Load Simulator V4", page_icon="📦", layout="wide")
st.markdown(
    """
<style>
  [data-testid="stAppViewContainer"]{background:#0d1117!important;}
  [data-testid="stSidebar"]{background:#1a1d24!important;}
  h1,h2,h3{color:#f4f5f7!important}
  .metric-card{background:#1a1d24;border:1px solid #2d2d2d;border-radius:8px;padding:12px;margin:6px}
  .exec-header{display:flex;gap:18px;align-items:center}
</style>
""",
    unsafe_allow_html=True,
)

ROOT = Path(__file__).resolve().parent.parent
SIM_ROOT = ROOT / "ingetrans-reel-simulator"
RUN_SCRIPT = SIM_ROOT / "scripts" / "run_simulator.py"


def _run_headless_simulation(scenario_path: str, duration_s: int = 300, tick: float = 1.0) -> Dict[str, Any]:
    """Submit the simulation as a job to the local Job API and poll for results.

    The UI must remain a consumer of the engine; it does not run the simulation locally.
    Set `SIMULATOR_API_URL` in the environment to change the target (default: http://localhost:8000).
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


def _render_kpi_cards(summary: Dict[str, Any]):
    completed = summary.get('completed_orders', 0)
    tph = summary.get('throughput_rolls_per_hour', 0.0)
    dur = summary.get('run_duration_s', 0)
    col1, col2, col3, col4 = st.columns([2, 2, 2, 2])
    with col1:
        st.markdown('<div class="metric-card"><div class="label">Completed orders</div><div style="font-size:22px;color:#FF6A00">{}</div></div>'.format(completed), unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="metric-card"><div class="label">Throughput (rolls/h)</div><div style="font-size:22px;color:#FF6A00">{:.1f}</div></div>'.format(tph), unsafe_allow_html=True)
    with col3:
        st.markdown('<div class="metric-card"><div class="label">Duration (s)</div><div style="font-size:22px;color:#FF6A00">{}</div></div>'.format(dur), unsafe_allow_html=True)
    with col4:
        st.markdown('<div class="metric-card"><div class="label">Run ID</div><div style="font-size:14px;color:#F4F5F7">{}</div></div>'.format(summary.get('run_id', '—')), unsafe_allow_html=True)


def _render_sankey_placeholder(summary: Optional[Dict[str, Any]] = None, scenario_path: Optional[str] = None):
    # Try to render the full INGECART Sankey if available, otherwise fallback to an empty placeholder
    try:
        scen_name = ""
        if summary and isinstance(summary.get("scenario"), str):
            scen_name = summary.get("scenario")
        elif scenario_path:
            scen_name = Path(scenario_path).name

        scenario_key = "a" if "forklift" in scen_name.lower() else "b"
        if charts is not None:
            fig = charts.build_sankey_flow(scenario=scenario_key)
            st.plotly_chart(fig, use_container_width=True)
            return
    except Exception:
        pass

    fig = go.Figure()
    fig.update_layout(title_text="Sankey preview (use advanced charts module for full diagram)", paper_bgcolor="#1A1D24", plot_bgcolor="#05070B")
    st.plotly_chart(fig, use_container_width=True)


def main():
    st.markdown("<div class='exec-header'><div style='font-size:36px'>📦</div><div><h1 style='margin:0'>Reel Load Simulator V4</h1><div style='color:#7e848e'>Visual runner y dashboard para el simulador V4</div></div></div>", unsafe_allow_html=True)
    st.markdown("---")

    # Scenario selector
    scen_dir = SIM_ROOT / "06_SCENARIOS"
    scenario_files = []
    if scen_dir.exists():
        scenario_files = sorted([str(p) for p in scen_dir.glob('*.yaml')])

    col_s, col_d, col_t = st.columns([4, 2, 2])
    with col_s:
        scenario = st.selectbox("Scenario", options=scenario_files or ["No scenarios found"], format_func=lambda p: Path(p).name if p else p)
    with col_d:
        # Enforce simulation durations of at least one shift (turno).
        shift_minutes = st.number_input("Shift length (min)", value=480, min_value=15, step=15, help="Duración de un turno en minutos. La simulación no ejecutará periodos menores a un turno.")
        shifts = st.number_input("Shifts to simulate", value=1, min_value=1, step=1, help="Número de turnos (enteros) a simular. Duración total = shifts × shift_length.")
        duration = int(shifts * shift_minutes * 60)
        st.caption(f"Duración total de simulación: {duration} s — {shifts} turno(s) × {shift_minutes} min = {duration/3600:.2f} h")
    with col_t:
        tick = st.number_input("Tick (s)", value=1.0, min_value=0.1, step=0.1)

    run_btn = st.button("▶ Ejecutar simulación")
    if run_btn:
        with st.spinner("Ejecutando simulación... esto puede tardar"):
            res = _run_headless_simulation(scenario, duration, tick)
        if res.get('error'):
            st.error(f"Simulación falló: {res.get('error')} — {res.get('stderr','')}")
        else:
            st.success("Simulación completada")
            _render_kpi_cards(res)
            _render_sankey_placeholder(res, scenario)
            # offer to open outputs folder
            out_base = SIM_ROOT / "outputs"
            runs = sorted([p for p in out_base.iterdir() if p.is_dir()], key=lambda p: p.name, reverse=True)
            if runs:
                latest = runs[0]
                st.markdown(f"**Outputs:** {latest} ")
                # show small run_summary
                s_path = latest / 'run_summary.json'
                try:
                    with open(s_path, 'r', encoding='utf-8') as f:
                        js = json.load(f)
                    st.json(js)
                except Exception as e:
                    st.write('No se pudo leer run_summary.json', e)


if __name__ == '__main__':
    main()
