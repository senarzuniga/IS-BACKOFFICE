import os
import json
import sys

sys.path.insert(0, os.getcwd())

from core.forklift_simulation_engine import ForkliftSimulationEngine
from core.ingetrans_simulation_engine import IngetransSimulationEngine
from utils.order_generator import generate_orders


def test_headless_short_run():
    root = os.getcwd()
    with open(os.path.join(root, 'assets', 'layout_common.json'), 'r', encoding='utf-8') as f:
        layout_common = json.load(f)

    # Merge minimal layouts
    layout_f = dict(layout_common)
    layout_i = dict(layout_common)

    orders = generate_orders(5, seed=42)

    engine_f = ForkliftSimulationEngine(layout_f, orders.copy(), {'n_forklifts': 1})
    engine_i = IngetransSimulationEngine(layout_i, orders.copy(), {'transfer_speed': 80})

    # Run 1 minute headless
    engine_f.run(1.0)
    engine_i.run(1.0)

    kf = engine_f.get_full_kpis()
    ki = engine_i.get_full_kpis()

    assert 'reel_changes_per_hour' in kf
    assert 'oee' in ki
