"""Run headless smoke test from repo root to ensure imports work.
"""
from pathlib import Path
import json

from core.forklift_simulation_engine import ForkliftSimulationEngine
from core.ingetrans_simulation_engine import IngetransSimulationEngine
from utils.order_generator import generate_orders

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

# generate orders
orders = generate_orders(12, seed=42)

# configs
cfg_f = {
    "n_forklifts": 2,
    "forklift_speed_loaded": 70.0,
    "forklift_speed_empty": 100.0,
    "buffer_capacity": 8,
}
cfg_i = {
    "transfer_speed": 80.0,
    "pick_up_s": 6.0,
    "drop_off_s": 6.0,
    "capacity": 1,
}

# instantiate
engine_a = ForkliftSimulationEngine(layout_fork, orders.copy(), cfg_f, seed=1)
engine_b = IngetransSimulationEngine(layout_ing, orders.copy(), cfg_i, seed=2)

# run headless for X minutes
DURATION_MIN = 10.0
print(f"Running headless simulation for {DURATION_MIN} minutes...")
engine_a.run(DURATION_MIN)
engine_b.run(DURATION_MIN)

ka = engine_a.get_full_kpis()
kb = engine_b.get_full_kpis()

print("--- Forklift KPIs ---")
for k, v in ka.items():
    print(k, ":", v)
print("--- Ingetrans KPIs ---")
for k, v in kb.items():
    print(k, ":", v)

# compute simple ROI using utilization minutes from engines.metrics
uf_min = sum(engine_a.metrics.get("utilization_time_min", {}).values())
ui_min = sum(engine_b.metrics.get("utilization_time_min", {}).values())
uf_h = uf_min / 60.0
ui_h = ui_min / 60.0
saved_h = max(0.0, uf_h - ui_h)
lab_cost = 20.0
print("--- Summary ---")
print(f"Forklift vehicle-hours: {uf_h:.2f} h")
print(f"Ingetrans vehicle-hours: {ui_h:.2f} h")
print(f"Saved hours if switching to INGETRANS: {saved_h:.2f} h")
print(f"Estimated saved cost (@{lab_cost} €/h): {saved_h * lab_cost:.2f}")
