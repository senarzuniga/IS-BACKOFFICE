"""Corrugated Plant Simulator — Main Streamlit Page.

Entry point: pages/plant_simulator.py (Streamlit multipage)

Tabs:
  1. 🏭 Configurar  — AI-guided wizard
  2. ▶ Simulación  — Live 2D canvas
  3. 📊 Analytics  — Plotly dashboard
  4. 📋 Reportes   — PDF/Excel export
  5. 📚 Biblioteca — Equipment catalog
  6. 📁 Historial  — Saved simulations
"""
from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

# --- Project root on path ---
ROOT = Path(__file__).resolve().parent.parent
# Locate the ingecart marketing kit package in common locations
_candidates = [
    ROOT / "ingecart-marketing-kit",
    ROOT / "informes" / "ingecart-marketing-kit" / "ingecart-marketing-kit",
    ROOT / "informes" / "ingecart-marketing-kit",
]
MKT_KIT = None
for _p in _candidates:
    try:
        if _p.exists():
            MKT_KIT = _p
            break
    except Exception:
        # permission or path issues — ignore and continue
        continue

# Insert MKT_KIT first (if found) so its `plant_simulator` package takes precedence,
# then ensure project root is also on sys.path.
if MKT_KIT and str(MKT_KIT) not in sys.path:
    # place marketing kit path first so its `plant_simulator` package is preferred
    sys.path.insert(0, str(MKT_KIT))
if str(ROOT) not in sys.path:
    # insert ROOT after MKT_KIT if MKT_KIT exists, otherwise at front
    if MKT_KIT and str(MKT_KIT) in sys.path:
        sys.path.insert(1, str(ROOT))
    else:
        sys.path.insert(0, str(ROOT))

import logging
from logging.handlers import RotatingFileHandler

# Defensive imports: try to import the marketing-kit `plant_simulator` package
IMPORT_ERROR = None
try:
    from plant_simulator.models import PlantConfig, PlantType
    from plant_simulator.config_agent import ConfigAgent, STEPS
    from plant_simulator.simulation_engine import SimulationEngine, ScenarioOptimizer
    from plant_simulator.canvas_builder import build_canvas_html
    from plant_simulator.report_generator import generate_excel_report, generate_pdf_report
    from plant_simulator.equipment_library import (
        CORRUGATOR_CATALOG, CONVERTER_CATALOG, TRANSPORT_CATALOG, SECTOR_BENCHMARKS
    )
    logging.getLogger(__name__).info('Imported plant_simulator package successfully')
except Exception as e:
    IMPORT_ERROR = e
    _LAST_ERROR = e
    # Provide safe placeholders and fallbacks so the Streamlit page doesn't crash
    PlantConfig = None
    PlantType = None
    ConfigAgent = None
    STEPS = []
    SimulationEngine = None
    ScenarioOptimizer = None
    build_canvas_html = None
    generate_excel_report = None
    generate_pdf_report = None
    # Safe defaults: empty catalogs and minimal sector benchmarks to avoid crashes
    CORRUGATOR_CATALOG = []
    CONVERTER_CATALOG = []
    TRANSPORT_CATALOG = []
    SECTOR_BENCHMARKS = {"corrugator_oee": 0.8, "world_class_oee": 0.85}

    logging.getLogger(__name__).warning('plant_simulator import failed; entering fallback mode: %s', e)

# If build_canvas_html isn't available, provide a minimal fallback that returns safe HTML
def _fallback_build_canvas_html(canvas_cfg, height=600):
    info = ''
    try:
        if isinstance(canvas_cfg, dict):
            info = f"Keys: {', '.join(list(canvas_cfg.keys())[:8])}"
        else:
            info = str(type(canvas_cfg))
    except Exception:
        info = 'unavailable'
    return f"<div style='padding:18px;font-family:system-ui'>Canvas unavailable (fallback). {info}</div>"

if build_canvas_html is None:
    build_canvas_html = _fallback_build_canvas_html

# --- Runtime logging (file) and global error capture ---
try:
    LOG_DIR = ROOT / "logs"
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_file_path = LOG_DIR / "plant_simulator.log"
    logger = logging.getLogger("plant_simulator_page")
    if not logger.handlers:
        handler = RotatingFileHandler(str(log_file_path), maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8")
        formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    logger.info("Plant simulator page loaded; sys.path top: %s", sys.path[:6])
except Exception as e:
    logging.basicConfig(level=logging.INFO)
    logging.getLogger(__name__).exception("Failed to initialize file logging: %s", e)

try:
    _LAST_ERROR
except NameError:
    _LAST_ERROR = None

def _handle_uncaught(exc_type, exc_value, exc_tb):
    global _LAST_ERROR
    _LAST_ERROR = exc_value
    try:
        logging.getLogger("plant_simulator_page").exception("Uncaught exception", exc_info=(exc_type, exc_value, exc_tb))
    except Exception:
        logging.getLogger(__name__).exception("Uncaught exception (failed to log)")

sys.excepthook = _handle_uncaught

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="CPS — Corrugated Plant Simulator",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ============================================================
# STYLES
# ============================================================
st.markdown(
    """
<style>
  /* Dark industrial theme */
  [data-testid="stAppViewContainer"]{background:#0d1117!important;}
  [data-testid="stSidebar"]{background:#1a1d24!important;}
  .stTabs [data-baseweb="tab-list"]{background:#1a1d24;border-radius:8px;padding:4px;}
  .stTabs [data-baseweb="tab"]{color:#7e848e;font-weight:600;font-size:13px;padding:6px 18px;}
  .stTabs [aria-selected="true"]{color:#FF6A00!important;border-bottom:2px solid #FF6A00!important;}
  .metric-card{background:#1a1d24;border:1px solid #2d2d2d;border-radius:8px;
               padding:14px 18px;margin:4px 0;}
  .metric-card .label{font-size:11px;color:#7e848e;text-transform:uppercase;letter-spacing:.8px;}
  .metric-card .value{font-size:22px;font-weight:700;color:#FF6A00;margin-top:2px;}
  .metric-card .delta{font-size:10px;color:#4fc17b;margin-top:2px;}
  .step-card{background:#1a1d24;border-left:3px solid #FF6A00;border-radius:0 6px 6px 0;
             padding:12px 16px;margin:8px 0;}
  .hint-box{background:#0d1117;border:1px solid #333;border-radius:6px;
            padding:10px 14px;font-size:12px;color:#7e848e;margin:6px 0;}
  .equipment-card{background:#1a1d24;border:1px solid #2a2a3a;border-radius:8px;
                  padding:12px;margin:6px 0;}
  .equipment-card h4{color:#FF6A00;margin:0 0 6px 0;font-size:13px;}
  .bottleneck-chip{display:inline-block;background:#3d1a1a;border:1px solid #e05555;
                   color:#e05555;border-radius:12px;padding:2px 10px;
                   font-size:11px;margin:2px;}
  div[data-testid="stMetricValue"]{color:#FF6A00!important;font-size:20px!important;}
  div[data-testid="stMetricDelta"]{font-size:11px!important;}
  h1,h2,h3{color:#f4f5f7!important;}
  .stMarkdown p,li{color:#c9cdd2;}
</style>
""",
    unsafe_allow_html=True,
)

# ============================================================
# SESSION STATE INIT
# ============================================================
def _init_state() -> None:
    defaults: Dict[str, Any] = {
        "cps_answers": {},
        "cps_config": None,           # PlantConfig
        "cps_results": None,          # SimulationResults
        "cps_scenario_results": None,  # List[SimulationResults]
        "cps_sim_running": False,
        "cps_history": [],            # List[dict] saved simulations
        "cps_tab": 0,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init_state()

# ============================================================
# HELPERS
# ============================================================
# Instantiate agent, with fallback behavior if ConfigAgent is missing
if ConfigAgent is not None:
    try:
        agent = ConfigAgent()
    except Exception as e:
        logging.getLogger(__name__).warning('ConfigAgent instantiation failed, using fallback agent: %s', e)
        ConfigAgent = None
        agent = None
else:
    agent = None

# Minimal fallback agent implementation to keep UI responsive when the real agent is missing
class _FallbackAgent:
    def demo_scenarios(self):
        return [("Demo (fallback)", {"plant_name": "Demo Plant"})]

    def get_visible_steps(self, answers):
        return []

    def get_hint(self, sid, answers):
        return ""

    def get_ai_recommendation(self, answers):
        return "AI agent unavailable — install the marketing kit for full features."

    def build_config(self, answers):
        class _Cfg:
            name = answers.get("plant_name", "Demo Plant") if isinstance(answers, dict) else "Demo Plant"
            plant_type = type("PT", (), {"value": "Demo"})
            converters = []
            transport = type("T", (), {"num_forklifts": 0})
            simulation_duration_hours = 1
            simulation_speed = 1

            def to_canvas_config(self):
                return {}

        return _Cfg()

if agent is None:
    agent = _FallbackAgent()

def _color_oee(val: float) -> str:
    if val >= 85: return "#4fc17b"
    if val >= 75: return "#f0c040"
    return "#e05555"

def _fmt_hms(sec: float) -> str:
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = int(sec % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"

# ============================================================
# HEADER
# ============================================================
col_logo, col_title = st.columns([1, 9])
with col_logo:
    st.markdown("<div style='font-size:42px;margin-top:8px'>🏭</div>", unsafe_allow_html=True)
with col_title:
    st.markdown(
        "<h1 style='margin:0;padding-top:4px;font-size:26px;'>Corrugated Plant Simulator</h1>"
        "<p style='color:#7e848e;margin:0;font-size:12px;'>Digital Twin 2D · INGECART Intelligence Suite · "
        "Simulación de flujos productivos en tiempo real</p>",
        unsafe_allow_html=True,
    )

st.markdown("---")

# Developer tools in sidebar
with st.sidebar.expander("Developer", expanded=False):
    try:
        dev_mode = st.checkbox("Developer mode (show logs & sys.path)", value=False)
    except Exception:
        dev_mode = False

    if dev_mode:
        st.markdown("**Import error**")
        st.write(str(IMPORT_ERROR) if IMPORT_ERROR else "None")
        st.markdown("**Last error**")
        st.write(str(_LAST_ERROR) if _LAST_ERROR else "None")
        st.markdown("**sys.path (top)**")
        st.code("\n".join(sys.path[:12]))
        try:
            if 'log_file_path' in globals() and log_file_path.exists():
                with open(str(log_file_path), 'r', encoding='utf-8') as _f:
                    txt = _f.read()[-20000:]
                st.text_area("Recent logs", txt, height=300)
                with open(str(log_file_path), 'rb') as _bf:
                    st.download_button(label="📥 Download logs", data=_bf.read(), file_name=log_file_path.name)
        except Exception as e:
            st.error(f"Cannot read log file: {e}")

# ============================================================
# TABS
# ============================================================
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🏭 Configurar",
    "▶ Simulación 2D",
    "📊 Analytics",
    "📋 Reportes",
    "📚 Biblioteca",
    "📁 Historial",
])

# ============================================================
# TAB 1 — CONFIGURAR
# ============================================================
with tab1:
    st.markdown("### 🤖 Configuración Guiada por IA")
    st.markdown(
        '<p style="color:#7e848e;font-size:12px;">'
        "El agente generará preguntas adaptadas al tipo de planta seleccionado. "
        "Responde paso a paso para construir el modelo de simulación.</p>",
        unsafe_allow_html=True,
    )

    # Quick-start scenarios
    with st.expander("⚡ Inicio rápido — escenarios predefinidos", expanded=False):
        try:
            scenarios = agent.demo_scenarios()
        except Exception as e:
            logging.getLogger(__name__).warning('demo_scenarios() failed: %s', e)
            _LAST_ERROR = e
            scenarios = [("Demo (fallback)", {})]

        cols_sc = st.columns(max(1, len(scenarios)))
        for i, (label, ans) in enumerate(scenarios):
            # guard against mismatched column counts
            col_index = i % len(cols_sc)
            with cols_sc[col_index]:
                if st.button(label, key=f"scenario_{i}", use_container_width=True):
                    st.session_state.cps_answers = dict(ans)
                    try:
                        st.session_state.cps_config = agent.build_config(ans)
                    except Exception as e:
                        st.error('Failed to build config from scenario.')
                        st.exception(e)
                        logging.getLogger(__name__).exception('Failed to build config from scenario: %s', e)
                        _LAST_ERROR = e
                        st.session_state.cps_config = None
                    st.rerun()

    st.markdown("---")

    answers = st.session_state.cps_answers
    visible_steps = agent.get_visible_steps(answers)
    total_steps = len(visible_steps)
    completed_steps = sum(1 for s in visible_steps if s["key"] in answers)

    # Progress bar
    prog = completed_steps / max(total_steps, 1)
    st.markdown(
        f"**Progreso:** {completed_steps}/{total_steps} pasos completados",
        unsafe_allow_html=True,
    )
    st.progress(prog)

    # Render steps in two columns
    col_form, col_info = st.columns([3, 2])

    with col_form:
        for step in visible_steps:
            key = step["key"]
            sid = step["id"]
            current_val = answers.get(key)

            with st.container():
                st.markdown(
                    f'<div class="step-card"><strong style="color:#f4f5f7;">{step["question"]}</strong></div>',
                    unsafe_allow_html=True,
                )

                # Render input by type
                if step["type"] == "select":
                    opts = step["options"]
                    labels = [o[1] for o in opts]
                    values = [o[0] for o in opts]
                    default_idx = 0
                    if current_val in values:
                        default_idx = values.index(current_val)
                    elif "default" in step and step["default"] in values:
                        default_idx = values.index(step["default"])
                    selected_label = st.selectbox(
                        "", labels, index=default_idx,
                        key=f"inp_{sid}", label_visibility="collapsed"
                    )
                    answers[key] = values[labels.index(selected_label)]

                elif step["type"] == "number":
                    default = step.get("default", step.get("min", 0))
                    val = st.number_input(
                        f"_{step.get('unit','')}_",
                        min_value=step.get("min", 0),
                        max_value=step.get("max", 9999),
                        value=int(current_val) if current_val is not None else int(default),
                        step=step.get("step", 1),
                        key=f"inp_{sid}",
                        label_visibility="collapsed",
                    )
                    answers[key] = val

                elif step["type"] == "text":
                    val = st.text_input(
                        "",
                        value=current_val or step.get("default", ""),
                        key=f"inp_{sid}",
                        label_visibility="collapsed",
                    )
                    answers[key] = val

                # Hint
                hint = agent.get_hint(sid, answers)
                if hint:
                    st.markdown(
                        f'<div class="hint-box">{hint}</div>',
                        unsafe_allow_html=True,
                    )

    with col_info:
        st.markdown("#### 🔍 Análisis previo")
        if len(answers) >= 3:
            rec = agent.get_ai_recommendation(answers)
            st.markdown(rec)
        else:
            st.markdown(
                '<p style="color:#7e848e;">Completa al menos 3 pasos para ver el análisis previo.</p>',
                unsafe_allow_html=True,
            )

        st.markdown("#### 📐 Vista previa del modelo")
        if answers:
            pt = answers.get("plant_type", "—")
            nc = answers.get("num_converters", "—")
            speed = answers.get("corrug_speed", "—")
            st.markdown(
                f"- **Tipo:** `{pt}`\n"
                f"- **Convertidoras:** {nc}\n"
                f"- **Vel. corrugadora:** {speed} m/min\n"
                f"- **Transporte:** {answers.get('transport_type','—')}\n"
                f"- **Carretillas:** {answers.get('num_forklifts','—')}\n"
                f"- **Buffer:** {answers.get('buffer_capacity','—')} palets\n"
                f"- **Simulación:** {answers.get('sim_duration','—')}h @ {answers.get('sim_speed','—')}×"
            )

    st.markdown("---")

    col_btn1, col_btn2, col_btn3 = st.columns([2, 2, 4])
    with col_btn1:
        if st.button("🔄 Limpiar configuración", use_container_width=True):
            st.session_state.cps_answers = {}
            st.session_state.cps_config = None
            st.rerun()
    with col_btn2:
        if st.button("💾 Guardar como plantilla", use_container_width=True):
            ts = datetime.now().strftime("%H:%M")
            name = answers.get("plant_name", "Planta") + f" ({ts})"
            st.session_state.cps_history.append({
                "name": name,
                "answers": dict(answers),
                "timestamp": datetime.now().isoformat(),
                "results": None,
            })
            st.success(f"Guardado: {name}")
    with col_btn3:
        launch_disabled = len(answers) < 5
        if st.button(
            "🚀 Generar Modelo y Lanzar Simulación",
            type="primary",
            use_container_width=True,
            disabled=launch_disabled,
        ):
            config = agent.build_config(answers)
            st.session_state.cps_config = config
            st.success(
                f"✅ Modelo generado: **{config.name}** · {config.plant_type.value} · "
                f"{len(config.converters)} convertidoras"
            )
            st.info("👆 Ve a la pestaña **▶ Simulación 2D** para verlo en acción")

    if launch_disabled:
        st.caption("⚠️ Completa al menos los pasos básicos antes de lanzar la simulación.")


# ============================================================
# TAB 2 — SIMULACIÓN 2D
# ============================================================
with tab2:
    cfg: Optional[PlantConfig] = st.session_state.cps_config

    if cfg is None:
        st.info(
            "🏭 No hay modelo configurado. Ve a **🏭 Configurar** y pulsa "
            "**Generar Modelo y Lanzar Simulación**, o usa un escenario de inicio rápido."
        )
        # Show default demo (safe fallback)
        st.markdown("#### Demo rápida — Planta completa con 3 convertidoras")
        try:
            demo_ans = agent.demo_scenarios()[0][1]
            demo_cfg = agent.build_config(demo_ans)
            canvas_cfg = demo_cfg.to_canvas_config()
        except Exception as e:
            logging.getLogger(__name__).warning('Failed to build demo canvas config: %s', e)
            _LAST_ERROR = e
            # fallback empty canvas config
            canvas_cfg = {}
    else:
        canvas_cfg = cfg.to_canvas_config()
        st.markdown(
            f"#### 🏭 {cfg.name} &nbsp;·&nbsp; "
            f"<span style='color:#7e848e;font-size:13px'>{cfg.plant_type.value} &nbsp;·&nbsp; "
            f"{len(cfg.converters)} convertidoras &nbsp;·&nbsp; "
            f"{cfg.transport.num_forklifts} carretillas &nbsp;·&nbsp; "
            f"Sim: {cfg.simulation_duration_hours:.0f}h @ {cfg.simulation_speed:.0f}×</span>",
            unsafe_allow_html=True,
        )

    # Render canvas with protection against rendering errors
    try:
        html = build_canvas_html(canvas_cfg, height=600)
        components.html(html, height=620, scrolling=False)
    except Exception as e:
        logging.getLogger(__name__).exception('Canvas rendering failed: %s', e)
        _LAST_ERROR = e
        fallback_html = _fallback_build_canvas_html({"error": str(e)})
        components.html(fallback_html, height=400, scrolling=True)

    # Legend
    col_l1, col_l2, col_l3, col_l4, col_l5 = st.columns(5)
    with col_l1:
        st.markdown("🟢 **Running** — operando")
    with col_l2:
        st.markdown("🔴 **Blocked** — bloqueado")
    with col_l3:
        st.markdown("🟡 **Setup** — cambio de orden")
    with col_l4:
        st.markdown("🔵 **Idle** — sin demanda")
    with col_l5:
        st.markdown("🟠 **Carretilla** — activa")

    st.caption(
        "💡 Pasa el cursor sobre cualquier máquina o almacén para ver detalles. "
        "Usa los botones de velocidad para acelerar/pausar la simulación."
    )


# ============================================================
# TAB 3 — ANALYTICS
# ============================================================
with tab3:
    st.markdown("### 📊 Motor de Análisis — Simulación Python")

    cfg: Optional[PlantConfig] = st.session_state.cps_config

    if cfg is None:
        st.info("Configura y genera un modelo primero en la pestaña 🏭 Configurar.")
    else:
        col_run1, col_run2 = st.columns([3, 1])
        with col_run1:
            st.markdown(
                f"**{cfg.name}** · {cfg.plant_type.value} · "
                f"Duración: {cfg.simulation_duration_hours:.0f}h"
            )
        with col_run2:
            run_sim = st.button(
                "▶ Ejecutar Simulación Analítica",
                type="primary",
                use_container_width=True,
                disabled=(SimulationEngine is None),
            )

        if run_sim:
            with st.spinner("⚙️ Ejecutando simulación…"):
                prog_bar = st.progress(0, text="Simulando…")
                engine = SimulationEngine(cfg)
                results = engine.run(progress_callback=lambda p: prog_bar.progress(p, text=f"Simulando… {p*100:.0f}%"))
                prog_bar.progress(1.0, text="✅ Completado")
                st.session_state.cps_results = results
                # Save to history
                if st.session_state.cps_history:
                    st.session_state.cps_history[-1]["results"] = results
                st.success(f"✅ Simulación completada: {results.m2_produced:,.0f} m² producidos · OEE: {results.average_oee:.1f}%")

        results = st.session_state.cps_results

        if results is None:
            st.info("Pulsa **▶ Ejecutar Simulación Analítica** para calcular KPIs.")
        else:
            # ---- KPI Cards ----
            st.markdown("#### KPIs Clave")
            kc1, kc2, kc3, kc4, kc5, kc6 = st.columns(6)
            with kc1:
                st.metric("m² Producidos", f"{results.m2_produced/1000:.1f}k")
            with kc2:
                st.metric("Uds. Convertidas", f"{results.total_units_converted/1000:.1f}k")
            with kc3:
                st.metric(
                    "OEE Medio",
                    f"{results.average_oee:.1f}%",
                    delta=f"{results.average_oee - SECTOR_BENCHMARKS['corrugator_oee']*100:.1f}% vs sector",
                )
            with kc4:
                st.metric("Efic. Corrugadora", f"{results.corrugator_efficiency:.1f}%")
            with kc5:
                st.metric("Buffer Medio", f"{results.buffer_avg_occupancy:.1f}%")
            with kc6:
                st.metric("Transporte", f"{results.transport_utilization:.1f}%")

            st.markdown("---")

            # ---- Timeline Charts ----
            if results.timeline:
                df_t = pd.DataFrame(results.timeline)

                col_c1, col_c2 = st.columns(2)

                with col_c1:
                    st.markdown("##### Evolución de Producción")
                    prod_cols = [c for c in df_t.columns if "_produced" in c]
                    if prod_cols:
                        fig_prod = px.line(
                            df_t, x="time_min", y=prod_cols,
                            labels={"time_min": "Tiempo (min)", "value": "Producción"},
                            color_discrete_sequence=["#FF6A00", "#4A90D9", "#4FC17B", "#F0C040"],
                            template="plotly_dark",
                        )
                        fig_prod.update_layout(
                            plot_bgcolor="#1a1d24", paper_bgcolor="#1a1d24",
                            legend_title="Máquina", margin=dict(t=10, b=10, l=10, r=10)
                        )
                        st.plotly_chart(fig_prod, use_container_width=True)

                with col_c2:
                    st.markdown("##### Ocupación de Buffer")
                    occ_cols = [c for c in df_t.columns if "occupancy" in c]
                    if occ_cols:
                        fig_occ = px.area(
                            df_t, x="time_min", y=occ_cols,
                            labels={"time_min": "Tiempo (min)", "value": "Ocupación %"},
                            color_discrete_sequence=["#4A90D9", "#FF6A00", "#4FC17B"],
                            template="plotly_dark",
                        )
                        fig_occ.update_layout(
                            plot_bgcolor="#1a1d24", paper_bgcolor="#1a1d24",
                            legend_title="Almacén", margin=dict(t=10, b=10, l=10, r=10)
                        )
                        st.plotly_chart(fig_occ, use_container_width=True)

            # ---- Machine OEE Breakdown ----
            st.markdown("#### OEE por Máquina — Desglose A×P×Q")
            if results.machine_metrics:
                df_mm = pd.DataFrame([
                    {
                        "Máquina": m.machine_id,
                        "Disponibilidad": m.availability,
                        "Rendimiento": m.performance,
                        "Calidad": m.quality,
                        "OEE": m.oee,
                        "Producción": m.units_produced,
                    }
                    for m in results.machine_metrics
                ])

                col_oee1, col_oee2 = st.columns(2)
                with col_oee1:
                    fig_oee = go.Figure()
                    for comp, color in [
                        ("Disponibilidad", "#4A90D9"),
                        ("Rendimiento", "#F0C040"),
                        ("Calidad", "#4FC17B"),
                    ]:
                        fig_oee.add_trace(go.Bar(
                            name=comp, x=df_mm["Máquina"], y=df_mm[comp],
                            marker_color=color,
                        ))
                    fig_oee.add_trace(go.Scatter(
                        name="OEE", x=df_mm["Máquina"], y=df_mm["OEE"],
                        mode="markers+lines", marker=dict(color="#FF6A00", size=10),
                        line=dict(color="#FF6A00", width=2),
                    ))
                    fig_oee.add_hline(
                        y=SECTOR_BENCHMARKS["world_class_oee"] * 100,
                        line_dash="dash", line_color="#888",
                        annotation_text="World Class 85%",
                    )
                    fig_oee.update_layout(
                        barmode="group", template="plotly_dark",
                        plot_bgcolor="#1a1d24", paper_bgcolor="#1a1d24",
                        legend=dict(orientation="h"),
                        margin=dict(t=10, b=10),
                        yaxis=dict(range=[0, 105]),
                    )
                    st.plotly_chart(fig_oee, use_container_width=True)

                with col_oee2:
                    fig_prod = px.bar(
                        df_mm, x="Máquina", y="Producción",
                        color="OEE",
                        color_continuous_scale=["#e05555", "#f0c040", "#4fc17b"],
                        range_color=[60, 100],
                        labels={"Producción": "Unidades / m²"},
                        template="plotly_dark",
                        title="Producción total por máquina",
                    )
                    fig_prod.update_layout(
                        plot_bgcolor="#1a1d24", paper_bgcolor="#1a1d24",
                        margin=dict(t=30, b=10),
                    )
                    st.plotly_chart(fig_prod, use_container_width=True)

                st.dataframe(
                    df_mm.style.format(
                        {"Disponibilidad": "{:.1f}%", "Rendimiento": "{:.1f}%",
                         "Calidad": "{:.1f}%", "OEE": "{:.1f}%", "Producción": "{:,.0f}"}
                    ),
                    use_container_width=True, hide_index=True,
                )

            # ---- Bottlenecks ----
            st.markdown("#### 🔴 Cuellos de Botella Detectados")
            if results.bottlenecks:
                bt_df = pd.DataFrame([
                    {
                        "Ubicación": b.location,
                        "Tipo": b.type,
                        "Espera media (s)": b.avg_wait_s,
                        "Espera máxima (s)": b.max_wait_s,
                        "Frecuencia": b.frequency,
                    }
                    for b in results.bottlenecks
                ])
                fig_bt = px.bar(
                    bt_df, x="Ubicación", y="Espera media (s)",
                    color="Frecuencia",
                    color_continuous_scale=["#f0c040", "#e05555"],
                    template="plotly_dark",
                )
                fig_bt.update_layout(
                    plot_bgcolor="#1a1d24", paper_bgcolor="#1a1d24",
                    margin=dict(t=10, b=10),
                )
                st.plotly_chart(fig_bt, use_container_width=True)
            else:
                st.success("✅ No se detectaron cuellos de botella significativos con esta configuración.")

            # ---- Recommendations ----
            st.markdown("#### 💡 Recomendaciones de Optimización")
            for rec in results.recommendations:
                st.markdown(f"- {rec}")

            # ---- Multi-Scenario Analysis ----
            st.markdown("---")
            st.markdown("#### 🔬 Análisis Multi-Escenario")
            st.markdown(
                '<p style="color:#7e848e;font-size:12px;">Compara automáticamente 5 variantes de la '
                "planta (base, +carretilla, +convertidora, tracks, buffer ampliado).</p>",
                unsafe_allow_html=True,
            )

            if st.button(
                "▶ Ejecutar Optimización Multi-Escenario (5 variantes)",
                type="secondary",
                disabled=(ScenarioOptimizer is None),
            ):
                with st.spinner("Ejecutando 5 escenarios…"):
                    pb_sc = st.progress(0)
                    optimizer = ScenarioOptimizer()
                    sc_results = optimizer.run_all(cfg, progress_callback=lambda p: pb_sc.progress(p))
                    st.session_state.cps_scenario_results = sc_results
                    st.success("✅ Todos los escenarios completados")

            sc_results = st.session_state.cps_scenario_results
            if sc_results:
                sc_df = pd.DataFrame([
                    {
                        "Escenario": r.scenario_label,
                        "m² Producidos": r.m2_produced,
                        "Uds. Convertidas": r.total_units_converted,
                        "OEE %": r.average_oee,
                        "Efic. Corrug. %": r.corrugator_efficiency,
                        "Buffer Medio %": r.buffer_avg_occupancy,
                        "Transport %": r.transport_utilization,
                    }
                    for r in sc_results
                ])

                fig_sc = go.Figure()
                for col, color in [
                    ("OEE %", "#FF6A00"),
                    ("Efic. Corrug. %", "#4A90D9"),
                    ("Buffer Medio %", "#4FC17B"),
                    ("Transport %", "#F0C040"),
                ]:
                    fig_sc.add_trace(go.Bar(
                        name=col, x=sc_df["Escenario"], y=sc_df[col],
                        marker_color=color,
                    ))
                fig_sc.update_layout(
                    barmode="group", template="plotly_dark",
                    plot_bgcolor="#1a1d24", paper_bgcolor="#1a1d24",
                    title="Comparativa de Escenarios — KPIs principales",
                    legend=dict(orientation="h"),
                    margin=dict(t=40, b=10),
                )
                st.plotly_chart(fig_sc, use_container_width=True)

                best = max(sc_results, key=lambda r: r.average_oee)
                st.success(
                    f"🏆 Mejor escenario: **{best.scenario_label}** → OEE: {best.average_oee:.1f}% · "
                    f"m²: {best.m2_produced:,.0f}"
                )
                st.dataframe(sc_df.style.format({
                    "m² Producidos": "{:,.0f}",
                    "Uds. Convertidas": "{:,.0f}",
                    "OEE %": "{:.1f}",
                    "Efic. Corrug. %": "{:.1f}",
                    "Buffer Medio %": "{:.1f}",
                    "Transport %": "{:.1f}",
                }), use_container_width=True, hide_index=True)


# ============================================================
# TAB 4 — REPORTES
# ============================================================
with tab4:
    st.markdown("### 📋 Generación de Reportes")

    results = st.session_state.cps_results

    if results is None:
        st.info(
            "Ejecuta primero la **Simulación Analítica** desde la pestaña 📊 Analytics "
            "para generar reportes con datos reales."
        )
    else:
        st.markdown(
            f"**Simulación:** {results.plant_name} · {results.plant_type} · "
            f"{results.duration_hours:.0f}h simuladas · Completado: {results.completed_at}"
        )
        st.markdown("---")

        col_r1, col_r2 = st.columns(2)

        with col_r1:
            st.markdown("#### 📄 Reporte PDF Ejecutivo")
            st.markdown(
                '<p style="color:#7e848e;font-size:12px;">'
                "Informe de 1-2 páginas con KPIs, análisis de máquinas, cuellos de botella "
                "y recomendaciones de optimización. Ideal para presentaciones de cliente.</p>",
                unsafe_allow_html=True,
            )
            if st.button("⬇️ Descargar PDF", type="primary", use_container_width=True, disabled=(generate_pdf_report is None)):
                with st.spinner("Generando PDF…"):
                    try:
                        pdf_bytes = generate_pdf_report(results)
                        fname = f"CPS_{results.plant_name.replace(' ','_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
                        st.download_button(
                            label="📄 Descargar PDF ahora",
                            data=pdf_bytes,
                            file_name=fname,
                            mime="application/pdf",
                            use_container_width=True,
                        )
                    except Exception as e:
                        _LAST_ERROR = e
                        logging.getLogger(__name__).exception('Error generating PDF: %s', e)
                        st.error(f"Error generando PDF: {e}")

        with col_r2:
            st.markdown("#### 📊 Reporte Excel Completo")
            st.markdown(
                '<p style="color:#7e848e;font-size:12px;">'
                "Workbook con 4 hojas: Resumen ejecutivo, métricas por máquina, "
                "timeline por minuto y cuellos de botella. Listo para análisis externo.</p>",
                unsafe_allow_html=True,
            )
            if st.button("⬇️ Descargar Excel", type="primary", use_container_width=True, disabled=(generate_excel_report is None)):
                with st.spinner("Generando Excel…"):
                    try:
                        xl_bytes = generate_excel_report(results)
                        fname = f"CPS_{results.plant_name.replace(' ','_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
                        st.download_button(
                            label="📊 Descargar Excel ahora",
                            data=xl_bytes,
                            file_name=fname,
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True,
                        )
                    except Exception as e:
                        _LAST_ERROR = e
                        logging.getLogger(__name__).exception('Error generating Excel: %s', e)
                        st.error(f"Error generando Excel: {e}")

        st.markdown("---")
        st.markdown("#### 📋 Vista previa — Recomendaciones")
        for rec in results.recommendations:
            st.markdown(f"- {rec}")

        st.markdown("#### 🔢 Métricas exportadas")
        mm_df = pd.DataFrame([
            {
                "Máquina": m.machine_id,
                "Disponibilidad": f"{m.availability:.1f}%",
                "Rendimiento": f"{m.performance:.1f}%",
                "Calidad": f"{m.quality:.1f}%",
                "OEE": f"{m.oee:.1f}%",
                "Producción": f"{m.units_produced:,.0f}",
                "Bloqueado (s)": f"{m.blocked_time_s:.0f}",
                "Setup (s)": f"{m.setup_time_s:.0f}",
            }
            for m in results.machine_metrics
        ])
        st.dataframe(mm_df, use_container_width=True, hide_index=True)

        # Export timeline CSV
        if results.timeline:
            df_t = pd.DataFrame(results.timeline)
            csv_bytes = df_t.to_csv(index=False).encode()
            st.download_button(
                label="📥 Descargar Timeline CSV (todos los minutos)",
                data=csv_bytes,
                file_name=f"CPS_timeline_{results.sim_id}.csv",
                mime="text/csv",
            )


# ============================================================
# TAB 5 — BIBLIOTECA
# ============================================================
with tab5:
    st.markdown("### 📚 Biblioteca de Equipos — Catálogo de Referencia")

    lib_tab1, lib_tab2, lib_tab3 = st.tabs(["🏭 Corrugadoras", "✂️ Convertidoras", "🚛 Transporte"])

    with lib_tab1:
        st.markdown("#### Corrugadoras disponibles en el catálogo")
        for eq in CORRUGATOR_CATALOG:
            with st.expander(f"**{eq['brand']} {eq['model']}** — {eq['width_mm']}mm · {eq['speed_m_min']}m/min"):
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.metric("Ancho útil", f"{eq['width_mm']} mm")
                    st.metric("Velocidad", f"{eq['speed_m_min']} m/min")
                with c2:
                    m2_shift = eq['m2_per_shift_estimate']
                    st.metric("m²/turno estimado", f"{m2_shift:,}")
                    st.metric("m²/mes (2 turnos)", f"{m2_shift*22*2/1e6:.1f}M")
                with c3:
                    st.markdown(f"**Descripción:** {eq['description']}")
                    st.markdown(f"**Notas:** {eq['notes']}")

    with lib_tab2:
        st.markdown("#### Convertidoras disponibles en el catálogo")
        for eq in CONVERTER_CATALOG:
            with st.expander(
                f"**{eq['brand']} {eq['model']}** — {eq['type']} · {eq['speed_uds_per_hour']} uds/h"
            ):
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.metric("Velocidad", f"{eq['speed_uds_per_hour']} uds/h")
                    st.metric("Disponibilidad", f"{eq['availability']*100:.0f}%")
                with c2:
                    st.metric("Formato máx.", f"{eq['format_max_mm'][0]}×{eq['format_max_mm'][1]} mm")
                    st.metric("Setup", f"{eq['setup_time_min']} min")
                with c3:
                    st.markdown(f"**Tipo:** {eq['type']}")
                    st.markdown(f"**Descripción:** {eq['description']}")

    with lib_tab3:
        st.markdown("#### Equipos de transporte y manutención")
        for eq in TRANSPORT_CATALOG:
            with st.expander(
                f"**{eq['brand']} {eq['model']}** — {eq['type']} · {eq.get('speed_ms', '—')} m/s"
            ):
                c1, c2 = st.columns(2)
                with c1:
                    st.metric("Velocidad", f"{eq.get('speed_ms','—')} m/s")
                    if "capacity_kg" in eq:
                        st.metric("Capacidad", f"{eq['capacity_kg']} kg")
                    st.metric("Ciclo estimado", f"{eq.get('cycle_time_min','—')} min")
                with c2:
                    st.markdown(f"**Descripción:** {eq['description']}")

    st.markdown("---")
    st.markdown("#### 📊 Benchmarks Sectoriales")
    bench_df = pd.DataFrame([
        {"KPI": k.replace("_", " ").title(), "Referencia": f"{v*100:.0f}%"}
        for k, v in SECTOR_BENCHMARKS.items()
    ])
    st.dataframe(bench_df, use_container_width=True, hide_index=True)


# ============================================================
# TAB 6 — HISTORIAL
# ============================================================
with tab6:
    st.markdown("### 📁 Historial de Simulaciones")

    history = st.session_state.cps_history

    if not history:
        st.info(
            "No hay simulaciones guardadas en esta sesión. "
            "Usa **💾 Guardar como plantilla** al configurar una planta."
        )
    else:
        for i, entry in enumerate(reversed(history)):
            idx = len(history) - 1 - i
            with st.expander(
                f"**{entry['name']}** — {entry['timestamp'][:16]}",
                expanded=(i == 0),
            ):
                col_h1, col_h2, col_h3 = st.columns([3, 2, 2])
                with col_h1:
                    pt = entry["answers"].get("plant_type", "—")
                    nc = entry["answers"].get("num_converters", "—")
                    st.markdown(
                        f"- **Tipo:** {pt}\n"
                        f"- **Convertidoras:** {nc}\n"
                        f"- **Velocidad corrug.:** {entry['answers'].get('corrug_speed','—')} m/min\n"
                        f"- **Transporte:** {entry['answers'].get('transport_type','—')}"
                    )
                if entry.get("results"):
                    r = entry["results"]
                    with col_h2:
                        st.metric("m² Producidos", f"{r.m2_produced/1000:.1f}k")
                        st.metric("OEE Medio", f"{r.average_oee:.1f}%")
                    with col_h3:
                        st.metric("Uds. Convertidas", f"{r.total_units_converted/1000:.1f}k")
                        st.metric("Efic. Corrug.", f"{r.corrugator_efficiency:.1f}%")
                else:
                    with col_h2:
                        st.caption("Sin datos de simulación analítica")
                with st.container():
                    col_btn_h1, col_btn_h2 = st.columns(2)
                    with col_btn_h1:
                        if st.button(f"📂 Cargar esta configuración", key=f"load_{idx}"):
                            st.session_state.cps_answers = dict(entry["answers"])
                            try:
                                st.session_state.cps_config = agent.build_config(entry["answers"])
                                st.success(f"✅ Cargado: {entry['name']}")
                            except Exception as e:
                                _LAST_ERROR = e
                                logging.getLogger(__name__).exception('Failed to load saved configuration: %s', e)
                                st.error('Failed to load saved configuration.')
                    with col_btn_h2:
                        if st.button(f"🗑️ Eliminar", key=f"del_{idx}"):
                            st.session_state.cps_history.pop(idx)
                            st.rerun()

    # Export history as JSON
    if history:
        st.markdown("---")
        hist_export = [
            {"name": h["name"], "timestamp": h["timestamp"], "answers": h["answers"]}
            for h in history
        ]
        st.download_button(
            label="📥 Exportar historial (JSON)",
            data=json.dumps(hist_export, indent=2, ensure_ascii=False),
            file_name=f"CPS_historial_{datetime.now().strftime('%Y%m%d')}.json",
            mime="application/json",
        )
