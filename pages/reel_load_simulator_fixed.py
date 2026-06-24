"""Reel Load Simulator — Fixed and improved Streamlit panel

This page replaces the previous `pages/Reel_load_simulator.py` with a
cleaner, safer and better-tested implementation that reuses the existing
core engines and renderer utilities.

Principles followed:
- Use the existing `ForkliftSimulationEngine` and `IngetransSimulationEngine`.
- Use `utils.order_generator.generate_orders` and `utils.canvas_renderer.render_scene`.
- Robust session-state + worker thread management to avoid orphan threads.
- Defensive KPI mapping and user-friendly formatting (percent handling).
- Export KPIs (CSV/JSON) and simple run save (JSON) for reproducibility.

This file is intentionally self-contained and conservative: it avoids
calling non-existent helpers and provides clear fallbacks.
"""

from __future__ import annotations

import json
import threading
import time
import io
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
import importlib.util

import pandas as pd
import streamlit as st

# Ensure repo root is on sys.path so `core` and `utils` import reliably.
# Streamlit may copy scripts to a temp folder; prefer robust detection:
# 1) look for a parent containing both `core/` and `utils/` next to this file
# 2) fallback to the current working directory
# 3) fallback to the original heuristic
def _ensure_repo_on_path():
    p = Path(__file__).resolve()
    tried: list[str] = []
    root = None
    # 1) search parents of this file for markers
    for parent in [p] + list(p.parents):
        tried.append(str(parent))
        if (parent / "core").is_dir() and (parent / "utils").is_dir():
            root = parent
            break
    else:
        # 2) try cwd
        cwd = Path.cwd()
        tried.append(f"cwd:{cwd}")
        if (cwd / "core").is_dir() and (cwd / "utils").is_dir():
            root = cwd
        else:
            # 3) walk cwd parents
            for parent in [cwd] + list(cwd.parents):
                tried.append(f"cwd_parent:{parent}")
                if (parent / "core").is_dir() and (parent / "utils").is_dir():
                    root = parent
                    break
            else:
                # 4) best-effort fallback: parent[1]
                root = p.parents[1]

    # write debug to repo root (best-effort) so we can inspect what was chosen
    try:
        debug_file = Path.cwd() / "streamlit_import_debug.txt"
        debug_text = "tried:\n" + "\n".join(tried) + "\nselected:\n" + str(root) + "\nsys.path (head):\n" + "\n".join(sys.path[:10])
        debug_file.write_text(debug_text, encoding="utf-8")
    except Exception:
        pass

    if str(root) not in sys.path:
        sys.path.insert(0, str(root))


_REPO_ROOT = _ensure_repo_on_path()


def _import_from_repo(module_rel_path: str, module_name: str):
    """Load a module from a relative path inside the repo root."""
    p = Path(_REPO_ROOT) / module_rel_path
    if not p.exists():
        raise FileNotFoundError(p)
    spec = importlib.util.spec_from_file_location(module_name, str(p))
    module = importlib.util.module_from_spec(spec)
    loader = spec.loader
    if loader is None:
        raise ImportError(f"No loader for {module_name}")
    loader.exec_module(module)
    return module

try:
    from core.forklift_simulation_engine import ForkliftSimulationEngine
    from core.ingetrans_simulation_engine import IngetransSimulationEngine
    from utils.order_generator import generate_orders
    from utils.canvas_renderer import render_scene
    from utils.kpi_calculator import compute_differential_kpis, compute_roi
    from core.commercial_simulator import run_commercial_demo
except Exception:
    # Fallback: import modules directly from repo files
    try:
        mod_a = _import_from_repo("core/forklift_simulation_engine.py", "core.forklift_simulation_engine")
        ForkliftSimulationEngine = getattr(mod_a, "ForkliftSimulationEngine")
    except Exception as e:  # pragma: no cover - fallback safety
        raise
    try:
        mod_b = _import_from_repo("core/ingetrans_simulation_engine.py", "core.ingetrans_simulation_engine")
        IngetransSimulationEngine = getattr(mod_b, "IngetransSimulationEngine")
    except Exception:
        raise
    try:
        mod_o = _import_from_repo("utils/order_generator.py", "utils.order_generator")
        generate_orders = getattr(mod_o, "generate_orders")
    except Exception:
        raise
    try:
        mod_r = _import_from_repo("utils/canvas_renderer.py", "utils.canvas_renderer")
        render_scene = getattr(mod_r, "render_scene")
    except Exception:
        raise
    try:
        mod_k = _import_from_repo("utils/kpi_calculator.py", "utils.kpi_calculator")
        compute_differential_kpis = getattr(mod_k, "compute_differential_kpis")
        compute_roi = getattr(mod_k, "compute_roi")
    except Exception:
        raise


# Page config
st.set_page_config(page_title="Reel Load Simulator — Fixed", layout="wide", page_icon="📦")


# Load layouts (reuse existing assets)
def _load_layout(name: str) -> Dict[str, Any]:
    p = Path("assets") / f"layout_{name}.json"
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


layout_common = _load_layout("common")
layout_forklift = _load_layout("forklift")
layout_ingetrans = _load_layout("ingetrans")

# Merge layouts (forklift/ingetrans extend common)
layout_fork = {**layout_common, **layout_forklift}
layout_ing = {**layout_common, **layout_ingetrans}


# Preset scenarios for order generation
SCENARIOS = {
    "Mixto (recomendado)": {"n": 12, "seed": 42},
    "Alta producción": {"n": 20, "seed": 42, "dist": (0.1, 0.4, 0.5)},
    "Corto intensivo": {"n": 10, "seed": 42, "dist": (1.0, 0.0, 0.0)},
    "Personalizado": {"n": 12, "seed": None},
}


def _safe_get_kpis(engine: Any) -> Dict[str, Any]:
    if engine is None:
        return {}
    for fn in ("get_full_kpis", "get_kpis", "getKPIs"):
        fnc = getattr(engine, fn, None)
        if callable(fnc):
            try:
                return fnc()
            except Exception:
                continue
    return {}


def _avg_utilization_pct(kpis: Dict[str, Any]) -> float:
    """Return the mean utilization percent across vehicles (0..100)."""
    util = kpis.get("utilization") or kpis.get("utilization_pct") or {}
    if isinstance(util, dict):
        vals = [v for v in util.values() if isinstance(v, (int, float))]
        if not vals:
            return 0.0
        avg = sum(vals) / len(vals)
        # Some implementations return 0..1, normalize if needed
        if avg <= 1.1:
            return avg * 100.0
        return avg
    # if it's a number, assume percent
    try:
        v = float(util)
        if v <= 1.1:
            return v * 100.0
        return v
    except Exception:
        return 0.0


def _format_percent(v: Optional[float]) -> str:
    if v is None:
        return "N/A"
    try:
        f = float(v)
    except Exception:
        return str(v)
    if f <= 1.1:
        f = f * 100.0
    return f"{f:.1f}%"


# Session-scope controller: keep single dict in session_state
if "reel_fixed_sim" not in st.session_state:
    st.session_state.reel_fixed_sim = {
        "thread": None,
        "stop_event": None,
        "running": False,
        "engine_A": None,
        "engine_B": None,
        "img_A": None,
        "img_B": None,
        "k_A": None,
        "k_B": None,
        "orders": None,
    }

SIM = st.session_state.reel_fixed_sim


def init_engines(config: Dict[str, Any], orders: Optional[list] = None, seed_a: Optional[int] = 1, seed_b: Optional[int] = 2) -> None:
    """Create and persist engine instances in session state.

    Uses safe, explicit config mappings so engines receive expected keys.
    """
    orders = list(orders) if orders else []

    cfg_f = {
        "n_forklifts": int(config.get("num_forklifts", 2)),
        "forklift_speed_loaded": float(config.get("forklift_speed_loaded", 60.0)),
        "forklift_speed_empty": float(config.get("forklift_speed_empty", 80.0)),
        "buffer_capacity": int(config.get("buffer_capacity", 8)),
    }

    cfg_i = {
        "transfer_speed": float(config.get("transfer_speed", 80.0)),
        "pick_up_s": float(config.get("pickup_time", 6.0)),
        "drop_off_s": float(config.get("dropoff_time", 6.0)),
        "capacity": int(config.get("transfer_capacity", 1)),
    }

    # instantiate engines
    engine_A = ForkliftSimulationEngine(layout_fork, orders.copy(), cfg_f, seed_a)
    engine_B = IngetransSimulationEngine(layout_ing, orders.copy(), cfg_i, seed_b)

    # store
    SIM["engine_A"] = engine_A
    SIM["engine_B"] = engine_B
    SIM["k_A"] = _safe_get_kpis(engine_A)
    SIM["k_B"] = _safe_get_kpis(engine_B)
    SIM["img_A"] = None
    SIM["img_B"] = None
    SIM["orders"] = orders


def _worker(engine_A: Any, engine_B: Any, speed_ctrl: Dict[str, Any]):
    stop_evt = threading.Event()
    speed = float(speed_ctrl.get("speed", 2))
    speed_ctrl["stop_event"] = stop_evt
    try:
        while not stop_evt.is_set():
            if speed_ctrl.get("running"):
                try:
                    engine_A.step()
                except Exception:
                    pass
                try:
                    engine_B.step()
                except Exception:
                    pass

                # snapshots and kpis (best-effort)
                try:
                    sA = engine_A.get_snapshot()
                    imgA = render_scene(sA, layout_fork, "forklift")
                    speed_ctrl["img_A"] = imgA
                    speed_ctrl["k_A"] = _safe_get_kpis(engine_A)
                except Exception:
                    pass
                try:
                    sB = engine_B.get_snapshot()
                    imgB = render_scene(sB, layout_ing, "ingetrans")
                    speed_ctrl["img_B"] = imgB
                    speed_ctrl["k_B"] = _safe_get_kpis(engine_B)
                except Exception:
                    pass

            # sleep scaled by requested speed (higher speed -> smaller sleep)
            time.sleep(max(0.02, 0.12 / max(1.0, float(speed_ctrl.get("speed", 2)))))
    finally:
        speed_ctrl["running"] = False
        speed_ctrl["thread"] = None
        speed_ctrl["stop_event"] = None


def start_worker_if_needed(speed: int = 2) -> None:
    # safety: if thread exists but not alive, clean it
    if SIM.get("thread") and SIM["thread"].is_alive():
        SIM["running"] = True
        SIM["speed"] = speed
        return

    # need engines
    if not SIM.get("engine_A") or not SIM.get("engine_B"):
        st.error("Engines not initialized — call Init before Start")
        return

    SIM["running"] = True
    SIM["speed"] = speed
    t = threading.Thread(target=_worker, args=(SIM["engine_A"], SIM["engine_B"], SIM), daemon=True)
    SIM["thread"] = t
    t.start()


def stop_worker() -> None:
    if SIM.get("stop_event"):
        try:
            SIM["stop_event"].set()
        except Exception:
            pass
    SIM["running"] = False


# -----------------------
# UI: Setup
# -----------------------

def render_setup():
    st.title("⚙️ Reel Load Simulator (Fixed)")
    st.markdown("Ajusta parámetros y genera órdenes para comparar Carretillas vs INGETRANS.")

    # sensible defaults chosen conservatively after reviewing codebase
    default_cfg = {
        "num_forklifts": 2,
        "num_tracks": 10,
        "buffer_capacity": 8,
        "forklift_speed_loaded": 70.0,
        "forklift_speed_empty": 100.0,
        "transfer_speed": 80.0,
        "pickup_time": 6.0,
        "dropoff_time": 6.0,
        "transfer_capacity": 1,
        # Demo / ROI params
        "orders_per_shift": 120,
        "shift_minutes": 480.0,
        "capex": 350000.0,
        "labor_cost_per_hour": 25.0,
        "workdays_per_year": 250,
        "shifts_per_day": 1.0,
    }

    if "config" not in st.session_state:
        st.session_state.config = default_cfg.copy()

    cfg = st.session_state.config

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📐 Parámetros de Planta")
        cfg["num_forklifts"] = st.slider("Nº Carretilleros", 1, 6, int(cfg.get("num_forklifts", 2)))
        cfg["num_tracks"] = st.slider("Nº Tracks", 4, 16, int(cfg.get("num_tracks", 10)))
        cfg["buffer_capacity"] = st.slider("Capacidad Buffer", 2, 20, int(cfg.get("buffer_capacity", 8)))
        st.markdown("**Velocidades (m/min)**")
        cfg["forklift_speed_loaded"] = st.number_input(
            "Carretilla cargada (m/min)", min_value=30.0, max_value=150.0, value=float(cfg.get("forklift_speed_loaded", 70.0))
        )
        cfg["forklift_speed_empty"] = st.number_input(
            "Carretilla vacía (m/min)", min_value=40.0, max_value=200.0, value=float(cfg.get("forklift_speed_empty", 100.0))
        )
        cfg["transfer_speed"] = st.number_input(
            "Transfer INGETRANS (m/min)", min_value=40.0, max_value=200.0, value=float(cfg.get("transfer_speed", 80.0))
        )

    with col2:
        st.subheader("📋 Órdenes de Producción")
        scenario = st.selectbox("Escenario de órdenes", list(SCENARIOS.keys()))
        custom_n = st.number_input("N órdenes (solo Personalizado)", min_value=1.0, max_value=200.0, value=float(12))
        if st.button("🎲 Generar órdenes"):
            params = SCENARIOS.get(scenario, {"n": 12, "seed": 42}).copy()
            if scenario == "Personalizado":
                params["n"] = int(custom_n)
            n = int(params.get("n", 12))
            seed = params.get("seed")
            dist = params.get("dist")
            if dist is None:
                orders = generate_orders(n, seed=seed)
            else:
                orders = generate_orders(n, seed=seed, dist=dist)
            st.session_state.generated_orders = orders
            SIM["orders"] = orders
            st.success(f"Generadas {len(orders)} órdenes ({scenario})")

        # Demo / ROI controls
        st.markdown("---")
        st.subheader("📈 Demo Comercial y ROI")
        cfg["orders_per_shift"] = int(st.number_input("Órdenes por turno (para demo)", min_value=1.0, max_value=2000.0, value=float(cfg.get("orders_per_shift", 120))))
        cfg["shift_minutes"] = float(st.number_input("Minutos por turno", min_value=60.0, max_value=1440.0, value=float(cfg.get("shift_minutes", 480.0))))
        cfg["capex"] = float(st.number_input("CapEx estimado (EUR)", min_value=10000.0, max_value=5000000.0, value=float(cfg.get("capex", 350000.0)), step=1000.0))
        cfg["labor_cost_per_hour"] = float(st.number_input("Coste laboral (EUR/h)", min_value=5.0, max_value=200.0, value=float(cfg.get("labor_cost_per_hour", 25.0)), step=0.5))
        cfg["workdays_per_year"] = int(st.number_input("Días laborales/año", min_value=100.0, max_value=365.0, value=float(cfg.get("workdays_per_year", 250))))
        cfg["shifts_per_day"] = float(st.number_input("Turnos/día", min_value=0.5, max_value=3.0, value=float(cfg.get("shifts_per_day", 1.0)), step=0.5))

        # preset save/load
        presets_file = Path("config") / "sim_presets.json"
        presets = {}
        if presets_file.exists():
            try:
                presets = json.loads(presets_file.read_text(encoding="utf-8"))
            except Exception:
                presets = {}

        preset_names = ["(none)"] + list(presets.keys())
        sel = st.selectbox("Cargar preset", preset_names, index=0)
        if sel and sel != "(none)":
            p = presets.get(sel, {})
            for k, v in p.items():
                cfg[k] = v
            st.success(f"Preset '{sel}' cargado.")

        preset_name = st.text_input("Guardar preset como (nombre)", value="")
        if st.button("💾 Guardar preset") and preset_name:
            presets[preset_name] = {
                k: cfg.get(k) for k in ("orders_per_shift", "shift_minutes", "capex", "labor_cost_per_hour", "workdays_per_year", "shifts_per_day")
            }
            presets_file.parent.mkdir(parents=True, exist_ok=True)
            presets_file.write_text(json.dumps(presets, indent=2), encoding="utf-8")
            st.success(f"Preset '{preset_name}' guardado en config/sim_presets.json")

        orders = st.session_state.get("generated_orders") or SIM.get("orders")
        if orders:
            df = pd.DataFrame(orders)
            st.dataframe(df, use_container_width=True)

    col_btn = st.columns([1, 1, 1])
    if col_btn[1].button("▶ Inicializar motores y preparar simulación"):
        # ensure we have orders
        orders = orders or generate_orders(12, seed=42)
        init_engines(st.session_state.config, orders)
        st.success("Motores inicializados. Haz Start para ejecutar la simulación.")

    # Quick commercial demo button
    if st.button("📈 Correr Demo Comercial (Penedès / Covington)"):
        orders_n = int(st.session_state.config.get("orders_per_shift", 120))
        shift_min = float(st.session_state.config.get("shift_minutes", 480.0))
        demo = run_commercial_demo(shift_min=shift_min, orders_per_shift=orders_n)
        # store along with ROI params used
        st.session_state.commercial_demo = demo
        st.session_state.commercial_demo_params = {
            "capex": float(st.session_state.config.get("capex", 350000.0)),
            "labor_cost_per_hour": float(st.session_state.config.get("labor_cost_per_hour", 25.0)),
            "workdays_per_year": int(st.session_state.config.get("workdays_per_year", 250)),
            "shifts_per_day": float(st.session_state.config.get("shifts_per_day", 1.0)),
        }
        SIM.update({"engine_A": None, "engine_B": None})
        st.success("Demo comercial ejecutada. Ve a Results para ver KPIs y ROI.")


# -----------------------
# UI: Simulation
# -----------------------

def render_simulation():
    st.title("🔄 Simulación en Curso — Reel Load (Fixed)")

    col_controls = st.columns([1, 1, 1, 2])
    if col_controls[0].button("⏸ Pausar"):
        SIM["running"] = False
    if col_controls[1].button("▶ Reanudar"):
        start_worker_if_needed(SIM.get("speed", 2))
    if col_controls[2].button("⏹ Detener"):
        stop_worker()

    speed = col_controls[3].select_slider("Velocidad", options=[1, 2, 5, 10], value=SIM.get("speed", 2))
    SIM["speed"] = speed

    # Auto-start worker if engines are present and running flag is true
    if SIM.get("engine_A") and SIM.get("engine_B") and SIM.get("running") and (not SIM.get("thread") or not SIM.get("thread").is_alive()):
        start_worker_if_needed(speed)

    # Display canvases side-by-side (SVG animation preferred)
    colA, colB = st.columns(2)

    # Attempt to import SVG renderer (graceful fallback to image renderer)
    try:
        from utils.renderer_svg import render_svg_scene
    except Exception:
        try:
            mod_svg = _import_from_repo("utils/renderer_svg.py", "utils.renderer_svg")
            render_svg_scene = getattr(mod_svg, "render_svg_scene")
        except Exception:
            render_svg_scene = None

    with colA:
        st.subheader("🚜 Escenario A — Carretillas")
        placeholder_A = st.empty()
        kpi_A_box = st.empty()
        lpi_A_box = st.empty()
        # fallback: show last produced image
        if not render_svg_scene:
            if SIM.get("img_A"):
                st.image(SIM["img_A"], use_column_width=True)
            else:
                st.write("(imagen no disponible todavía)")
            kA = SIM.get("k_A") or _safe_get_kpis(SIM.get("engine_A"))
            st.markdown("**KPIs (A)**")
            st.write({
                "OEE": _format_percent(kA.get("oee")),
                "Reel/h": round(kA.get("reel_changes_per_hour", kA.get("reel_changes_hour", 0)), 2),
                "Utilización (media)": _format_percent(_avg_utilization_pct(kA)),
                "Cola (órdenes)": kA.get("queue_length", "N/A"),
            })

    with colB:
        st.subheader("🤖 Escenario B — INGETRANS")
        placeholder_B = st.empty()
        kpi_B_box = st.empty()
        lpi_B_box = st.empty()
        if not render_svg_scene:
            if SIM.get("img_B"):
                st.image(SIM["img_B"], use_column_width=True)
            else:
                st.write("(imagen no disponible todavía)")
            kB = SIM.get("k_B") or _safe_get_kpis(SIM.get("engine_B"))
            st.markdown("**KPIs (B)**")
            st.write({
                "OEE": _format_percent(kB.get("oee")),
                "Reel/h": round(kB.get("reel_changes_per_hour", kB.get("reel_changes_hour", 0)), 2),
                "Utilización (media)": _format_percent(_avg_utilization_pct(kB)),
                "Cola (órdenes)": kB.get("queue_length", "N/A"),
            })

    # If SVG renderer and Streamlit fragment are available, switch to animated loop
    has_fragment = hasattr(st, "fragment")
    if render_svg_scene and has_fragment:
        # prefer fragment-based stepping; stop background worker if running
        if SIM.get("thread"):
            stop_worker()

        @st.fragment(run_every=0.1)
        def animation_loop():
            if not SIM.get("running"):
                return

            # Engine A
            if SIM.get("engine_A"):
                try:
                    SIM["engine_A"].step()
                    snapA = SIM["engine_A"].get_snapshot()
                    svgA = render_svg_scene(snapA, "A")
                    try:
                        placeholder_A.components.v1.html(svgA, height=520)
                    except Exception:
                        placeholder_A.write("(error rendering SVG)")
                    try:
                        kpisA = SIM["engine_A"].get_full_kpis()
                    except Exception:
                        kpisA = _safe_get_kpis(SIM.get("engine_A"))
                    kpi_A_box.json(kpisA)
                    lpi_A_box.metric("LPI A", f"{kpisA.get('lpi', 50):.0f}/100")
                    SIM["k_A"] = kpisA
                except Exception:
                    pass

            # Engine B
            if SIM.get("engine_B"):
                try:
                    SIM["engine_B"].step()
                    snapB = SIM["engine_B"].get_snapshot()
                    svgB = render_svg_scene(snapB, "B")
                    try:
                        placeholder_B.components.v1.html(svgB, height=520)
                    except Exception:
                        placeholder_B.write("(error rendering SVG)")
                    try:
                        kpisB = SIM["engine_B"].get_full_kpis()
                    except Exception:
                        kpisB = _safe_get_kpis(SIM.get("engine_B"))
                    kpi_B_box.json(kpisB)
                    lpi_B_box.metric("LPI B", f"{kpisB.get('lpi', 50):.0f}/100")
                    SIM["k_B"] = kpisB
                except Exception:
                    pass

        # iniciar el fragment (se ejecutará periódicamente)
        animation_loop()

    # Comparative chart
    st.markdown("---")
    st.subheader("📊 Comparativa rápida")
    kA = SIM.get("k_A") or _safe_get_kpis(SIM.get("engine_A"))
    kB = SIM.get("k_B") or _safe_get_kpis(SIM.get("engine_B"))
    if kA and kB:
        metrics = [
            ("OEE", lambda k: (_avg_utilization_pct(k) if k.get("oee") is None else (k.get("oee") * 100.0 if k.get("oee") <= 1.1 else k.get("oee")))),
            ("Reel/h", lambda k: k.get("reel_changes_per_hour", k.get("reel_changes_hour", 0))),
            ("Collisions", lambda k: k.get("collisions", 0)),
            ("Queue", lambda k: k.get("queue_length", 0)),
        ]
        rows = []
        for label, fn in metrics:
            try:
                a = fn(kA) or 0
                b = fn(kB) or 0
            except Exception:
                a = 0
                b = 0
            rows.append({"Metric": label, "Carretillas": a, "INGETRANS": b})
        st.table(pd.DataFrame(rows))

    # Event log and controls
    with st.expander("📜 Log de eventos (últimos)"):
        if SIM.get("engine_A"):
            evs = getattr(SIM["engine_A"], "event_log", [])[-10:]
            st.write("**A — Carretillas**")
            for e in evs:
                st.write(e)
        if SIM.get("engine_B"):
            evs = getattr(SIM["engine_B"], "event_log", [])[-10:]
            st.write("**B — INGETRANS**")
            for e in evs:
                st.write(e)


# -----------------------
# UI: Results
# -----------------------

def render_results():
    st.title("📊 Resultados y ROI")
    # allow viewing calibrated commercial demo stored in session_state
    if st.session_state.get("commercial_demo"):
        demo = st.session_state.get("commercial_demo")
        kA = demo.get("forklift")
        kB = demo.get("ingetrans")
    else:
        if not SIM.get("engine_A") or not SIM.get("engine_B"):
            st.warning("No hay datos de simulación. Inicializa y ejecuta la simulación primero.")
            return
        kA = SIM.get("k_A") or _safe_get_kpis(SIM.get("engine_A"))
        kB = SIM.get("k_B") or _safe_get_kpis(SIM.get("engine_B"))

    st.subheader("KPIs principales")
    df = pd.DataFrame([
        {"Métrica": "OEE (%)", "Carretillas": _format_percent(kA.get("oee")), "INGETRANS": _format_percent(kB.get("oee"))},
        {"Métrica": "Reel/h", "Carretillas": round(kA.get("reel_changes_per_hour", 0), 2), "INGETRANS": round(kB.get("reel_changes_per_hour", 0), 2)},
        {"Métrica": "Utilización media (%)", "Carretillas": _format_percent(_avg_utilization_pct(kA)), "INGETRANS": _format_percent(_avg_utilization_pct(kB))},
        {"Métrica": "Colisiones", "Carretillas": kA.get("collisions", 0), "INGETRANS": kB.get("collisions", 0)},
        {"Métrica": "Downtime (min)", "Carretillas": round(kA.get("downtime_min", 0), 1), "INGETRANS": round(kB.get("downtime_min", 0), 1)},
    ])
    st.dataframe(df, use_container_width=True)

    st.subheader("Diferencias y ROI estimado")
    diff = compute_differential_kpis(kA, kB)
    roi_params = st.session_state.get("commercial_demo_params") or {
        "labor_cost_per_hour": float(st.session_state.config.get("labor_cost_per_hour", 25.0)),
        "workdays_per_year": int(st.session_state.config.get("workdays_per_year", 250)),
        "capex": float(st.session_state.config.get("capex", 350000.0)),
        "shifts_per_day": float(st.session_state.config.get("shifts_per_day", 1.0)),
    }
    roi = compute_roi(kA, kB, roi_params)
    st.json({"differential": diff, "roi": roi})

    # Export options
    col1, col2 = st.columns(2)
    with col1:
        csv_io = io.StringIO()
        pd.DataFrame({"forklift": kA, "ingetrans": kB}).to_csv(csv_io)
        st.download_button("📥 Descargar KPIs CSV", data=csv_io.getvalue(), file_name="reel_kpis.csv", mime="text/csv")
    with col2:
        st.download_button("📥 Descargar KPIs JSON", data=json.dumps({"forklift": kA, "ingetrans": kB}, default=str, indent=2), file_name="reel_kpis.json", mime="application/json")

    # Text summary and download
    try:
        saved_cost = roi.get("saved_cost_per_year") if isinstance(roi, dict) else None
        payback = roi.get("estimated_payback_years") if isinstance(roi, dict) else None
    except Exception:
        saved_cost = None
        payback = None

    summary_lines = [
        "Reel Load Commercial Demo Summary",
        "---------------------------------",
        f"Forklift (Penedès): OEE={_format_percent(kA.get('oee'))}, Utilización promedio={_format_percent(_avg_utilization_pct(kA))}, Starvations={kA.get('starvations', 'N/A')}, Distancia_km={round(kA.get('distance_m',0)/1000.0,1)}",
        f"INGETRANS (Covington): OEE={_format_percent(kB.get('oee'))}, Utilización promedio={_format_percent(_avg_utilization_pct(kB))}, Starvations={kB.get('starvations', 'N/A')}, Distancia_km={round(kB.get('distance_m',0)/1000.0,1)}",
        "",
        f"Diferencial Reel/h: Forklift={kA.get('reel_changes_per_hour')} vs INGETRANS={kB.get('reel_changes_per_hour')}",
        f"Ahorro estimado anual (EUR): {saved_cost}",
        f"Payback estimado (años): {payback}",
    ]
    summary_text = "\n".join(summary_lines)
    st.download_button("📥 Descargar resumen TXT", data=summary_text, file_name="reel_demo_summary.txt", mime="text/plain")

    if st.button("🔄 Nueva simulación"):
        # stop worker and clear engines
        stop_worker()
        SIM.update({"engine_A": None, "engine_B": None, "img_A": None, "img_B": None, "k_A": None, "k_B": None, "orders": None})
        st.experimental_rerun()


# -----------------------
# Router
# -----------------------

def main():
    tab = st.sidebar.radio("Vista", ["Setup", "Simulation", "Results"], index=1 if SIM.get("running") else 0)
    if tab == "Setup":
        render_setup()
    elif tab == "Simulation":
        render_simulation()
    else:
        render_results()


if __name__ == "__main__":
    main()
