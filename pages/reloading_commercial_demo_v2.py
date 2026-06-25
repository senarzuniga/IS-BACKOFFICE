"""
Reel Load Simulator — Commercial Demo V2

Interfaz Streamlit minimalista para ejecutar el nuevo `CorrugatorEngine`
en dos escenarios (Forklift vs INGETRANS) de forma determinista.
"""
from __future__ import annotations

import importlib.util
import sys
import time
from pathlib import Path
from typing import Any, Dict

import streamlit as st


# --- ensure repo on sys.path (robust for Streamlit temp copy) ---
def _ensure_repo_on_path():
    p = Path(__file__).resolve()
    root = None
    for parent in [p] + list(p.parents):
        if (parent / "core").is_dir() and (parent / "utils").is_dir():
            root = parent
            break
    if root is None:
        cwd = Path.cwd()
        for parent in [cwd] + list(cwd.parents):
            if (parent / "core").is_dir() and (parent / "utils").is_dir():
                root = parent
                break
    if root is None:
        root = p.parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))


_ensure_repo_on_path()


# Try importing the new engine; if Streamlit moved file, fallback to file loader
def _import_from_repo(rel_path: str, mod_name: str):
    repo_root = Path(sys.path[0])
    p = repo_root / rel_path
    spec = importlib.util.spec_from_file_location(mod_name, str(p))
    m = importlib.util.module_from_spec(spec)
    loader = spec.loader
    if loader is None:
        raise ImportError("no loader")
    loader.exec_module(m)
    return m


try:
    from core.corrugator_engine import CorrugatorEngine
except Exception:
    mod = _import_from_repo("core/corrugator_engine.py", "core.corrugator_engine")
    CorrugatorEngine = getattr(mod, "CorrugatorEngine")

try:
    from utils.renderer_svg import render_svg_scene
except Exception:
    mod_r = _import_from_repo("utils/renderer_svg.py", "utils.renderer_svg")
    render_svg_scene = getattr(mod_r, "render_svg_scene")


st.set_page_config(page_title="Reel Load Simulator — Commercial Demo v2", layout="wide")


def _build_snapshot_for_renderer(engine: Any) -> Dict[str, Any]:
    snap = engine.get_snapshot()
    kpis = engine.get_kpis()
    # resources -> entities
    entities = []
    for i, r in enumerate(engine.resources):
        entities.append({
            "id": r.id,
            "state": r.state,
            "loaded": r.loaded,
            "pos": (i * 3 + 2, 0),
            "type": "transfer" if "INGETRANS" in r.id else "forklift",
        })

    # reels: dict by track id
    reels = {}
    try:
        for t in engine.tracks:
            tid = t.get("id")
            reels[tid] = {
                "status": "on_track" if t.get("occupied") else "empty",
                "type": t.get("reel_type"),
                "weight": t.get("reel_weight", 0),
            }
    except Exception:
        pass

    metrics = {"num_tracks": len(engine.tracks), "buffer_capacity": engine.flow.buffer_capacity}

    return {
        "time": snap.get("time", 0.0),
        "entities": entities,
        "reels": reels,
        "metrics": metrics,
        "kpis": kpis,
        "queue_len": snap.get("queue_length", 0),
    }


def init_engines(config: Dict, seed: int | None = None):
    st.session_state.engineA = CorrugatorEngine("A", config, seed)
    st.session_state.engineB = CorrugatorEngine("B", config, seed)
    st.session_state.last_run = None


def run_both(duration_min: float, progress_callback=None):
    eA = st.session_state.engineA
    eB = st.session_state.engineB
    steps = int(max(1, duration_min / eA.dt))
    report_every = max(1, steps // 30)
    for i in range(steps):
        eA.step()
        eB.step()
        if progress_callback and (i % report_every == 0):
            progress_callback((i + 1) / steps)


def calculate_roi_real(engine_A: Any, engine_B: Any, config: Dict) -> Dict:
    kpis_A = engine_A.get_kpis()
    kpis_B = engine_B.get_kpis()
    meters_A = kpis_A["meters_produced"]
    meters_B = kpis_B["meters_produced"]
    extra_meters = meters_B - meters_A
    starvation_A = kpis_A["starvation_time"]
    starvation_B = kpis_B["starvation_time"]
    saved_starvation = starvation_A - starvation_B
    value_per_meter = config.get("value_per_meter", 0.5)
    lost_value = extra_meters * value_per_meter
    corrugator_cost_hour = config.get("corrugator_cost_hour", 500)
    saved_cost = (saved_starvation / 60.0) * corrugator_cost_hour
    labor_cost_hour = config.get("labor_cost_hour", 35)
    labor_saved = ((kpis_A.get("utilization", 0) - kpis_B.get("utilization", 0)) / 100.0) * labor_cost_hour
    total_savings = lost_value + saved_cost + labor_saved * 8 * 330
    capex = config.get("capex_eur", 350000)
    payback = capex / total_savings if total_savings > 0 else 999
    return {"extra_meters": extra_meters, "saved_starvation_h": saved_starvation / 60.0, "total_savings_eur": total_savings, "payback_years": payback}


### UI
st.title("Reel Load Simulator — Commercial Demo v2")

with st.sidebar:
    st.header("Configuración")
    seed = st.number_input("Seed (deja 0 para aleatorio)", value=42, step=1)
    duration_min = st.slider("Duración (min)", min_value=1, max_value=480, value=60)
    num_forklifts = st.number_input("Num Forklifts", min_value=1, max_value=5, value=1)
    num_tracks = st.number_input("Num Tracks", min_value=2, max_value=24, value=10)
    buffer_capacity = st.number_input("Buffer capacity", min_value=1, max_value=200, value=12)
    run_button = st.button("Inicializar y ejecutar")

config = {
    "num_forklifts": int(num_forklifts),
    "num_tracks": int(num_tracks),
    "buffer_capacity": int(buffer_capacity),
    "corrugator_speed_m_min": 250.0,
}

if "engineA" not in st.session_state or st.session_state.get("cfg") != config or (seed and st.session_state.get("seed") != seed):
    init_engines(config, None if seed == 0 else int(seed))
    st.session_state["cfg"] = config
    st.session_state["seed"] = seed

if run_button:
    progress = st.sidebar.progress(0)
    run_both(duration_min, lambda p: progress.progress(int(p * 100)))
    st.sidebar.success("Run complete")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Escenario A — Forklift (humano)")
    snapA = _build_snapshot_for_renderer(st.session_state.engineA)
    svgA = render_svg_scene(snapA, "A")
    st.components.v1.html(svgA, height=560)
    st.write(st.session_state.engineA.get_kpis())

with col2:
    st.subheader("Escenario B — INGETRANS (automático)")
    snapB = _build_snapshot_for_renderer(st.session_state.engineB)
    svgB = render_svg_scene(snapB, "B")
    st.components.v1.html(svgB, height=560)
    st.write(st.session_state.engineB.get_kpis())

st.markdown("---")
if st.button("Calcular ROI comparativo"):
    roi = calculate_roi_real(st.session_state.engineA, st.session_state.engineB, config)
    st.json(roi)
