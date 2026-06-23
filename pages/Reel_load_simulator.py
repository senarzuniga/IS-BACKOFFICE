"""REEL LOAD SIMULATOR — Panel Streamlit

Panel independiente para comparar dos escenarios de carga de Reels:
- ESCENARIO A: Carretillas (convencional)
- ESCENARIO B: INGETRANS (transfer + tracks)

Este archivo crea la UI, gestiona configuración y órdenes, y conecta con
el motor de simulación en `core/Reel_load_simulator.py` y los agentes
en `agents/Reel_load_simulator/`.

Nota: el simulador es step-based (avanza por minutos) y está pensado como
un prototipo extensible que reutiliza componentes del `plant_simulator` si
están disponibles.
"""
from __future__ import annotations

import json
import os
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

import streamlit as st
import streamlit.components.v1 as components

# Rutas
ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "Reel_load_simulator"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Intentar importar componentes reutilizables del Plant Simulator si existen
try:
    from plant_simulator.canvas_builder import build_canvas_html  # type: ignore
except Exception:
    build_canvas_html = None

from core.Reel_load_simulator import SimulationEngine
from agents.Reel_load_simulator.config_agent import ConfigAgent
from agents.Reel_load_simulator.work_order_agent import WorkOrderAgent
from agents.Reel_load_simulator.roi_agent import ROIAgent


def _save_run(sim_result: Dict[str, Any]) -> Path:
    """Guarda los resultados de una simulación en `data/Reel_load_simulator/completed_runs/`.

    También intenta integrar con un Knowledge Hub si existe (fallback silencioso).
    """
    out_dir = DATA_DIR / "completed_runs"
    out_dir.mkdir(parents=True, exist_ok=True)
    fname = f"run_{sim_result.get('sim_id', uuid.uuid4())}.json"
    outp = out_dir / fname
    with open(outp, "w", encoding="utf-8") as f:
        json.dump(sim_result, f, indent=2, ensure_ascii=False)

    # Intento de integración con Knowledge Hub (si existe)
    try:
        from utils import knowledge_hub  # type: ignore

        if hasattr(knowledge_hub, "save_simulation"):
            knowledge_hub.save_simulation(sim_result)
    except Exception:
        # integración opcional — no bloquear
        pass

    return outp


def main() -> None:
    st.set_page_config(page_title="REEL LOAD SIMULATOR", layout="wide")

    st.title("REEL LOAD SIMULATOR — Carretillas vs INGETRANS")

    # Sidebar: carga/guardado configuración
    config_agent = ConfigAgent()
    cfg = config_agent.load_default()

    with st.sidebar.expander("Configuración de Planta", expanded=True):
        st.markdown("**Parámetros principales (edítalos y guarda)**")
        # Muestra algunos parámetros editables
        corrug_length = st.number_input("Wet End Length (m)", value=cfg.get("corrugator_wet_end_m", 60))
        num_portareels = st.number_input("PortaReels (n)", value=cfg.get("num_spindles", 10))
        num_forklifts = st.number_input("Nº carretilleros", value=cfg.get("conventional_num_forklifts", 2))
        transfer_speed = st.number_input("Transfer speed (m/min)", value=cfg.get("ingetrans_transfer_speed", 80))

        if st.button("Guardar configuración"):
            cfg["corrugator_wet_end_m"] = corrug_length
            cfg["num_spindles"] = int(num_portareels)
            cfg["conventional_num_forklifts"] = int(num_forklifts)
            cfg["ingetrans_transfer_speed"] = float(transfer_speed)
            config_agent.save_default(cfg)
            st.success("Configuración guardada en data/Reel_load_simulator/config_default.json")

    # Panel principal — controles y generación de órdenes
    col_ctrl, col_orders = st.columns([2, 1])

    with col_orders:
        st.markdown("### Órdenes de Fabricación")
        wo_agent = WorkOrderAgent()
        if "orders" not in st.session_state:
            st.session_state["orders"] = wo_agent.generate_orders(8)

        if st.button("Generar órdenes aleatorias"):
            st.session_state["orders"] = wo_agent.generate_orders(8)

        st.dataframe(st.session_state["orders"])  # simple view

    with col_ctrl:
        st.markdown("### Controles de Simulación")
        # velocidad: tiempo de sueño entre pasos para 'Run'
        speed = st.selectbox("Velocidad (escala)", options=["1x", "2x", "5x", "10x"], index=0)
        sleep_map = {"1x": 0.35, "2x": 0.2, "5x": 0.09, "10x": 0.02}
        sleep_s = sleep_map.get(speed, 0.2)

        steps_to_run = st.number_input("Pasos a ejecutar (minutos)", min_value=1, value=30)
        step_button = st.button("▶ Step (1 minuto)")
        run_button = st.button("▶ Run")
        stop_button = st.button("⏹ Stop")

    # Inicializar motores de ambos escenarios si no existen en sesión
    if "engine_A" not in st.session_state:
        st.session_state["engine_A"] = SimulationEngine(cfg, st.session_state["orders"], scenario="A")
    if "engine_B" not in st.session_state:
        st.session_state["engine_B"] = SimulationEngine(cfg, st.session_state["orders"], scenario="B")

    engine_A: SimulationEngine = st.session_state["engine_A"]
    engine_B: SimulationEngine = st.session_state["engine_B"]

    # Display: dos columnas con canvas/estado
    left, right = st.columns(2)

    with left:
        st.subheader("Escenario A — Carretillas")
        st.markdown(f"**Movimientos:** {engine_A.result.movements}  •  **Reel changes:** {engine_A.result.reel_changes}")
        placeholder_a = st.empty()

    with right:
        st.subheader("Escenario B — INGETRANS")
        st.markdown(f"**Movimientos:** {engine_B.result.movements}  •  **Reel changes:** {engine_B.result.reel_changes}")
        placeholder_b = st.empty()

    # Helper to render simple canvas HTML when build_canvas_html is unavailable
    def _render_simple_canvas(engine: SimulationEngine) -> str:
        return (
            f"<div style='font-family:system-ui;padding:12px;'>"
            f"<strong>Time (min):</strong> {engine.time_min}<br/>"
            f"<strong>Movements:</strong> {engine.result.movements}<br/>"
            f"<strong>Reel changes:</strong> {engine.result.reel_changes}<br/>"
            f"</div>"
        )

    # Single step
    if step_button:
        engine_A.step()
        engine_B.step()

    # Run N steps blocking loop (small runs recommended)
    if run_button:
        n = int(steps_to_run)
        progress_placeholder = st.empty()
        for i in range(n):
            engine_A.step()
            engine_B.step()
            progress_placeholder.progress((i + 1) / n)
            # render intermediate
            if build_canvas_html:
                try:
                    html_a = build_canvas_html({"engine": "A"}, height=300)
                    html_b = build_canvas_html({"engine": "B"}, height=300)
                    placeholder_a.components.html(html_a, height=300)
                    placeholder_b.components.html(html_b, height=300)
                except Exception:
                    placeholder_a.components.html(_render_simple_canvas(engine_A), height=200)
                    placeholder_b.components.html(_render_simple_canvas(engine_B), height=200)
            else:
                placeholder_a.components.html(_render_simple_canvas(engine_A), height=200)
                placeholder_b.components.html(_render_simple_canvas(engine_B), height=200)

            time.sleep(sleep_s)

        progress_placeholder.empty()

    # Stop: export results and save
    if stop_button:
        res_a = engine_A.result.__dict__ if hasattr(engine_A, "result") else {}
        res_b = engine_B.result.__dict__ if hasattr(engine_B, "result") else {}
        out_a = _save_run({"sim_id": res_a.get("sim_id", str(uuid.uuid4())), "scenario": "A", "metrics": res_a})
        out_b = _save_run({"sim_id": res_b.get("sim_id", str(uuid.uuid4())), "scenario": "B", "metrics": res_b})
        st.success(f"Simulaciones guardadas: {out_a.name}, {out_b.name}")

    # Always render current canvas
    if build_canvas_html:
        try:
            html_a = build_canvas_html({"engine": "A"}, height=300)
            html_b = build_canvas_html({"engine": "B"}, height=300)
            placeholder_a.components.html(html_a, height=300)
            placeholder_b.components.html(html_b, height=300)
        except Exception:
            placeholder_a.components.html(_render_simple_canvas(engine_A), height=200)
            placeholder_b.components.html(_render_simple_canvas(engine_B), height=200)
    else:
        placeholder_a.components.html(_render_simple_canvas(engine_A), height=200)
        placeholder_b.components.html(_render_simple_canvas(engine_B), height=200)


if __name__ == "__main__":
    main()
