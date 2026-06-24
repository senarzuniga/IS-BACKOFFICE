"""Demo commercial run comparing Forklift vs INGETRANS using Penedès/Covington presets.
Runs headless for a shift (default 480 minutes) and prints KPIs and ROI.
"""
from pathlib import Path
import json

from core.forklift_simulation_engine import ForkliftSimulationEngine
from core.ingetrans_simulation_engine import IngetransSimulationEngine
from utils.order_generator import generate_orders
from utils.kpi_calculator import compute_differential_kpis, compute_roi
from core.commercial_simulator import run_commercial_demo

# presets (from user)
PENEDES_POS = {
    "SF1": 7.5,
    "SF2": 5.8,
    "SF3": 11.5,
    "SF4": 26.0,
    "SF5": 31.5,
}

INGETRANS_COVINGTON = {
    "transfer_speed": 80.0,
    "acceleration_s": 4.5,
    "pick_up_s": 6.0,
    "drop_off_s": 6.0,
    "capacity": 2,
    "track_speed": 24.0,
    "track_length": 12.0,
    "cycle_s": 16.75,
}

FORKLIFT_PENEDES = {
    "pickup_s": 30.0,
    "dropoff_s": 20.0,
    "utilization_pct": 0.95,
    "distance_km_per_shift": (15.0, 25.0),
}

# load layouts
def _load(name: str):
    p = Path("assets") / f"layout_{name}.json"
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {}

layout_common = _load("common")
layout_forklift = _load("forklift")
layout_ingetrans = _load("ingetrans")
layout_fork = {**layout_common, **layout_forklift}
layout_ing = {**layout_common, **layout_ingetrans}

# generate realistic orders: for demo, a busy shift
orders = generate_orders(120, seed=42)

# configure engines
cfg_f = {
    "n_forklifts": 3,
    "forklift_speed_loaded": 70.0,
    "forklift_speed_empty": 100.0,
    "buffer_capacity": 10,
    "pickup_time": FORKLIFT_PENEDES["pickup_s"],
    "dropoff_time": FORKLIFT_PENEDES["dropoff_s"],
}

cfg_i = {
    "transfer_speed": INGETRANS_COVINGTON["transfer_speed"],
    "pick_up_s": INGETRANS_COVINGTON["pick_up_s"],
    "drop_off_s": INGETRANS_COVINGTON["drop_off_s"],
    "capacity": INGETRANS_COVINGTON["capacity"],
}

# run commercial calibrated demo for one shift (minutes)
SHIFT_MIN = 480.0
print(f"Running calibrated commercial demo for {SHIFT_MIN} minutes (one shift)...")
demo = run_commercial_demo(shift_min=SHIFT_MIN, orders_per_shift=120)
kA = demo["forklift"]
kB = demo["ingetrans"]

print("--- FORKLIFT (Penedès) KPIs ---")
for k, v in kA.items():
    print(k, ":", v)
print("--- INGETRANS (Covington) KPIs ---")
for k, v in kB.items():
    print(k, ":", v)

print("--- Differential KPIs ---")
print(compute_differential_kpis(kA, kB))

roi = compute_roi(kA, kB, {"labor_cost_per_hour": 25.0, "workdays_per_year": 250, "capex": 350000.0})
print("--- ROI Estimate ---")
print(roi)
