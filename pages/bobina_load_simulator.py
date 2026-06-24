"""Panel Streamlit para el simulador comparativo Forklift vs INGETRANS.
"""
import streamlit as st
import time
import json
import threading
import io
import csv
import base64

from core.simulation_engine import BaseSimulationEngine
from core.forklift_simulation_engine import ForkliftSimulationEngine
from core.ingetrans_simulation_engine import IngetransSimulationEngine
from utils.renderer import render_scene
from utils.kpi_calculator import compute_differential_kpis, compute_roi
import streamlit.components.v1 as components

st.set_page_config(layout="wide")

# Cargar layouts
with open("assets/layout_common.json", "r", encoding="utf-8") as f:
    layout_common = json.load(f)

with open("assets/layout_forklift.json", "r", encoding="utf-8") as f:
    layout_forklift = json.load(f)

with open("assets/layout_ingetrans.json", "r", encoding="utf-8") as f:
    layout_ingetrans = json.load(f)

# Merge layouts
layout_fork = {**layout_common, **layout_forklift}
layout_ing = {**layout_common, **layout_ingetrans}

# Controles
st.title("Bobina Load Simulator — Forklift vs INGETRANS")
col1, col2 = st.columns([1, 1])

with st.sidebar:
    scenario_sel = st.selectbox("Escenario", ["Both", "Forklift", "INGETRANS"]) 
    n_forklifts = st.slider("N carretillas", 1, 4, 2)
    speed = st.selectbox("Velocidad de simulación", [1, 2, 5, 10], index=0)
    start_btn = st.button("Start")
    stop_btn = st.button("Stop")
    pause_btn = st.button("Pause")

# Crear órdenes de prueba
orders = []
for i in range(10):
    orders.append({"reel_id": f"R{i+1}", "track_id": "RS3_A"})

# Instanciar motores
config_f = {"n_forklifts": n_forklifts, "forklift_speed_loaded": 60.0, "forklift_speed_empty": 80.0, "buffer_capacity": 8}
config_i = {"transfer_speed": 80.0, "pick_up_s": 6, "drop_off_s": 6, "capacity": 2}

# Persist engines in session state so they survive reruns
if "engine_f" not in st.session_state:
    st.session_state["engine_f"] = ForkliftSimulationEngine(layout_fork, orders.copy(), config_f)
if "engine_i" not in st.session_state:
    st.session_state["engine_i"] = IngetransSimulationEngine(layout_ing, orders.copy(), config_i)

engine_f = st.session_state["engine_f"]
engine_i = st.session_state["engine_i"]

# Global sim controller (module-level ephemeral)
if "_SIM" not in st.session_state:
    st.session_state["_SIM"] = {"thread": None, "stop_event": None, "running": False, "lock": threading.RLock(), "img_f": None, "img_i": None, "kf": None, "ki": None}

SIM = st.session_state["_SIM"]

# Lugar para render y KPIs
left_canvas = st.empty()
right_canvas = st.empty()
left_kpi = st.empty()
right_kpi = st.empty()

running = SIM.get("running", False)
if start_btn:
    SIM["running"] = True
    running = True
if stop_btn:
    # signal thread to stop
    if SIM.get("stop_event"):
        SIM["stop_event"].set()
    SIM["running"] = False
    running = False

# Event injection + engine reset
with st.sidebar:
    st.write("Eventos")
    if st.button("forklift_blocked"):
        engine_f.inject_event("forklift_blocked")
    if st.button("transfer_delay"):
        engine_i.inject_event("transfer_delay", {"extra_s": 12})
    if st.button("Reset engines"):
        # stop running thread and recreate engines with current config
        if SIM.get("stop_event"):
            SIM["stop_event"].set()
        st.session_state["engine_f"] = ForkliftSimulationEngine(layout_fork, orders.copy(), config_f)
        st.session_state["engine_i"] = IngetransSimulationEngine(layout_ing, orders.copy(), config_i)
        SIM.update({"img_f": None, "img_i": None, "kf": None, "ki": None})

def _safe_get_kpis(engine):
    if hasattr(engine, "get_full_kpis"):
        return engine.get_full_kpis()
    if hasattr(engine, "get_kpis"):
        return engine.get_kpis()
    return {}


def _kpis_to_csv(kf, ki):
    # Flatten and align keys
    keys = set(kf.keys()) | set(ki.keys())
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(["metric", "forklift", "ingetrans"])
    for key in sorted(keys):
        v1 = kf.get(key, "")
        v2 = ki.get(key, "")
        # stringify nested dicts
        if isinstance(v1, dict):
            v1 = ";".join(f"{kk}={vv}" for kk, vv in v1.items())
        if isinstance(v2, dict):
            v2 = ";".join(f"{kk}={vv}" for kk, vv in v2.items())
        writer.writerow([key, v1, v2])
    return out.getvalue()


def _worker(engine_f, engine_i, layout_fork, layout_ing, speed, sim_ctrl):
    stop_evt = threading.Event()
    sim_ctrl["stop_event"] = stop_evt
    try:
        while not stop_evt.is_set():
            if sim_ctrl.get("running"):
                try:
                    engine_f.step()
                    engine_i.step()
                except Exception:
                    pass

                try:
                    state_f = engine_f.get_state()
                    state_i = engine_i.get_state()
                    img_f = render_scene(state_f, layout_fork, "forklift")
                    img_i = render_scene(state_i, layout_ing, "ingetrans")
                    sim_ctrl["img_f"] = img_f
                    sim_ctrl["img_i"] = img_i
                except Exception:
                    pass

                try:
                    sim_ctrl["kf"] = _safe_get_kpis(engine_f)
                    sim_ctrl["ki"] = _safe_get_kpis(engine_i)
                except Exception:
                    pass

            # sleep a resolution pequeña para responder a stop/pause rápidamente
            time.sleep(max(0.05, 0.1 / float(speed)))
    finally:
        sim_ctrl["running"] = False
        sim_ctrl["thread"] = None
        sim_ctrl["stop_event"] = None


# Start worker thread if requested
if start_btn:
    # if there's already a running thread, just set running
    if SIM.get("thread") and SIM["thread"].is_alive():
        SIM["running"] = True
    else:
        SIM["running"] = True
        SIM["stop_event"] = None
        t = threading.Thread(target=_worker, args=(engine_f, engine_i, layout_fork, layout_ing, speed, SIM), daemon=True)
        SIM["thread"] = t
        t.start()

if pause_btn:
    SIM["running"] = not SIM.get("running", False)

if stop_btn:
    # stop handled above
    pass

# Display current images and KPIs from sim controller
try:
    img_f = SIM.get("img_f")
    img_i = SIM.get("img_i")
    if img_f:
        left_canvas.image(img_f, use_column_width=True)
    else:
        left_canvas.write("(no image yet)")
    if img_i:
        right_canvas.image(img_i, use_column_width=True)
    else:
        right_canvas.write("(no image yet)")

    kf = SIM.get("kf") or _safe_get_kpis(engine_f)
    ki = SIM.get("ki") or _safe_get_kpis(engine_i)

    left_kpi.metric("Reel changes/h", round(float(kf.get("reel_changes_per_hour", kf.get("reel_changes_hour", 0))), 2) if kf else 0)
    right_kpi.metric("Reel changes/h", round(float(ki.get("reel_changes_per_hour", ki.get("reel_changes_hour", 0))), 2) if ki else 0)

except Exception as e:
    st.error(f"Error mostrando estado: {e}")

# Mostrar resumen
st.header("Resumen comparativo")
colA, colB = st.columns(2)
with colA:
    st.write("Forklift KPIs")
    st.json(kf)
with colB:
    st.write("INGETRANS KPIs")
    st.json(ki)

st.write("Diferencias")
st.json(compute_differential_kpis(kf, ki))

st.write("ROI estimado")
st.json(compute_roi(kf, ki, {"labor_cost_per_hour": 20.0}))

# Export CSV / JSON
st.markdown("---")
cold1, cold2 = st.columns([1, 1])
with cold1:
    csv_data = _kpis_to_csv(kf or {}, ki or {})
    st.download_button("Download KPIs CSV", data=csv_data, file_name="bobina_kpis.csv", mime="text/csv")
with cold2:
    import json as _json
    st.download_button("Download KPIs JSON", data=_json.dumps({"forklift": kf, "ingetrans": ki}, indent=2), file_name="bobina_kpis.json", mime="application/json")

# Live refresh option (client-side reload) to see images updating without blocking server
with st.sidebar:
    live = st.checkbox("Live updates (auto-reload)", value=False)
    refresh_s = st.number_input("Refresh interval (s)", min_value=1, max_value=10, value=1)
    if live:
        # inject small JS to reload page periodically
        components.html(f"""
            <script>
            if (!window._bobinaRefresh) {{
                window._bobinaRefresh = true;
                setInterval(()=>{{ window.location.reload(); }}, {int(refresh_s * 1000)});
            }}
            </script>
        """, height=0)
