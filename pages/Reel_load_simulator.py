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

    # Helper: rich SVG/HTML renderer when build_canvas_html is unavailable
    def _render_rich_canvas(engine: SimulationEngine) -> str:
        st_state = engine.to_canvas_state()
        metrics = st_state.get("metrics", {})

        width = 560
        height = 280
        # layout widths (px)
        w_warehouse = int(width * 0.25)
        w_exchange = int(width * 0.20)
        w_tracks = int(width * 0.40)
        w_corr = width - (w_warehouse + w_exchange + w_tracks)

        x_wh = 0
        x_ex = x_wh + w_warehouse
        x_tr = x_ex + w_exchange
        x_co = x_tr + w_tracks

        # Build SVG elements
        svg_parts: list[str] = []
        svg_parts.append(f"<rect x='{x_wh}' y='0' width='{w_warehouse}' height='{height}' fill='#f0f0f0' stroke='#bbb' />")
        svg_parts.append(f"<rect x='{x_ex}' y='0' width='{w_exchange}' height='{height}' fill='#fff4e6' stroke='#ffbb88' />")
        svg_parts.append(f"<rect x='{x_tr}' y='0' width='{w_tracks}' height='{height}' fill='#f9f9f9' stroke='#ccc' />")
        svg_parts.append(f"<rect x='{x_co}' y='0' width='{w_corr}' height='{height}' fill='#e9e9e9' stroke='#999' />")

        # Racks in warehouse (3 racks)
        rack_w = w_warehouse / 3.0
        rack_h = height - 20
        racks = st_state.get("racks", [1, 1, 1])
        for i in range(3):
            rx = x_wh + int(i * rack_w)
            svg_parts.append(f"<rect x='{rx+6}' y='10' width='{int(rack_w-12)}' height='{int(rack_h)}' fill='#ddd' stroke='#999' />")
            # bobinas circulares
            count = racks[i] if i < len(racks) else 0
            for j in range(count):
                cx = rx + 16 + (j % 3) * 18
                cy = 30 + (j // 3) * 28
                color = '#8B4513' if j % 3 == 0 else ('#D2B48C' if j % 3 == 1 else '#F5F5DC')
                svg_parts.append(f"<circle cx='{cx}' cy='{cy}' r='8' fill='{color}' stroke='#555' />")

        # Tracks (10 lanes)
        lane_w = w_tracks / 10.0
        tracks = st_state.get("tracks", [])
        for i in range(10):
            lx = x_tr + int(i * lane_w) + int(lane_w/2) - 6
            ly = int(height * 0.45)
            svg_parts.append(f"<rect x='{lx}' y='{ly}' width='12' height='{int(height*0.45)}' fill='#eee' stroke='#bbb' />")
            occupied = False
            if i < len(tracks):
                occupied = bool(tracks[i].get("occupied"))
            if occupied:
                svg_parts.append(f"<circle cx='{lx+6}' cy='{ly+18}' r='10' fill='#88cc88' stroke='#336633' />")
            else:
                svg_parts.append(f"<circle cx='{lx+6}' cy='{ly+18}' r='6' fill='#ffffff' stroke='#999' />")

        # Corrugadora icon
        svg_parts.append(f"<text x='{x_co+10}' y='20' font-size='12' fill='#333'>Corrugadora</text>")

        # Dynamic elements: forklifts or transfer
        if st_state.get("scenario") == "A":
            for f in st_state.get("forklifts", []):
                fx = max(0, min(100, float(f.get("x", 25))))
                fy = max(10, min(90, float(f.get("y", 40))))
                px = int((fx / 100.0) * width)
                py = int((fy / 100.0) * height)
                color = '#ff4444' if f.get('carrying') else '#007bff'
                svg_parts.append(f"<rect x='{px-10}' y='{py-8}' width='20' height='14' rx='3' fill='{color}' stroke='#222' />")
                svg_parts.append(f"<text x='{px-8}' y='{py+4}' font-size='9' fill='#fff'>{f.get('id')}</text>")
        else:
            tr = st_state.get("transfer", {"pos": 30, "carrying": []})
            tx = float(tr.get("pos", 30))
            px = int((tx / 100.0) * width)
            py = int(height * 0.2)
            svg_parts.append(f"<rect x='{px-20}' y='{py-12}' width='40' height='24' rx='6' fill='#E84C22' stroke='#b33' />")
            svg_parts.append(f"<text x='{px-14}' y='{py+6}' font-size='10' fill='#fff'>TRANSFER</text>")
            # show carried bobinas
            carrying = tr.get("carrying") or []
            for k, _ in enumerate(carrying):
                svg_parts.append(f"<circle cx='{px + 18 + k*12}' cy='{py}' r='6' fill='#8B4513' stroke='#000' />")

        # KPIs area
        kpi_html = (
            f"<div style='font-family:system-ui;padding:8px 0 0 0;'>"
            f"<strong>Time (min):</strong> {metrics.get('time_min', 0)} &nbsp;"
            f"<strong>Movements:</strong> {metrics.get('movements', 0)} &nbsp;"
            f"<strong>Reel changes:</strong> {metrics.get('reel_changes', 0)} &nbsp;"
            f"<strong>Starv.:</strong> {metrics.get('starvation_events', 0)}"
            f"</div>"
        )

        svg_full = """
        <svg xmlns='http://www.w3.org/2000/svg' width='{}' height='{}' style='background:#ffffff;border:1px solid #ddd;'>
        {}
        </svg>
        """.format(width, height, "\n".join(svg_parts))

        html = f"<div style='font-family:system-ui'>{svg_full}{kpi_html}</div>"
        return html

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
                    with placeholder_a:
                        components.html(html_a, height=300)
                    with placeholder_b:
                        components.html(html_b, height=300)
                except Exception:
                    with placeholder_a:
                        components.html(_render_rich_canvas(engine_A), height=260)
                    with placeholder_b:
                        components.html(_render_rich_canvas(engine_B), height=260)
            else:
                with placeholder_a:
                    components.html(_render_rich_canvas(engine_A), height=260)
                with placeholder_b:
                    components.html(_render_rich_canvas(engine_B), height=260)

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
            with placeholder_a:
                components.html(html_a, height=300)
            with placeholder_b:
                components.html(html_b, height=300)
        except Exception:
            with placeholder_a:
                components.html(_render_rich_canvas(engine_A), height=260)
            with placeholder_b:
                components.html(_render_rich_canvas(engine_B), height=260)
    else:
        with placeholder_a:
            components.html(_render_rich_canvas(engine_A), height=260)
        with placeholder_b:
            components.html(_render_rich_canvas(engine_B), height=260)


if __name__ == "__main__":
    main()
