#!/usr/bin/env python3
"""Generate UI snapshots from engines using existing render_scene utility.

Produces images in `releases/rc1_evidence/`:
- ui_snapshot_forklift.png
- ui_snapshot_ingetrans.png
"""
from __future__ import annotations

import os
from pathlib import Path
import sys


def main() -> int:
    repo = Path(__file__).resolve().parent.parent
    os.chdir(repo)

    # ensure repo root is on sys.path so imports like `core.*` and `utils.*` work
    repo_root = str(repo)
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)

    out = repo / 'releases' / 'rc1_evidence'
    out.mkdir(parents=True, exist_ok=True)

    try:
        from core.forklift_simulation_engine import ForkliftSimulationEngine
        from core.ingetrans_simulation_engine import IngetransSimulationEngine
        from utils.order_generator import generate_orders
        from utils.canvas_renderer import render_scene
    except Exception as e:
        print('Error importing modules for UI snapshot:', e)
        return 2

    # generate some orders
    orders = generate_orders(12, seed=42)

    # Forklift engine
    cfg_f = {"n_forklifts": 2, "forklift_speed_loaded": 70.0, "forklift_speed_empty": 100.0, "buffer_capacity": 8}
    engine_f = ForkliftSimulationEngine({}, orders.copy(), cfg_f, seed=42)
    # step some iterations
    for _ in range(10):
        try:
            engine_f.step()
        except Exception:
            pass
    s_f = engine_f.get_snapshot()
    img_f = render_scene(s_f, engine_f.layout if hasattr(engine_f, 'layout') else {}, 'forklift')
    img_f.save(out / 'ui_snapshot_forklift.png')
    print('Wrote', out / 'ui_snapshot_forklift.png')

    # Ingetrans engine
    cfg_i = {"transfer_speed": 80.0, "pickup_time": 6.0, "dropoff_time": 6.0, "capacity": 1}
    engine_i = IngetransSimulationEngine({}, orders.copy(), cfg_i, seed=123)
    for _ in range(10):
        try:
            engine_i.step()
        except Exception:
            pass
    s_i = engine_i.get_snapshot()
    img_i = render_scene(s_i, engine_i.layout if hasattr(engine_i, 'layout') else {}, 'ingetrans')
    img_i.save(out / 'ui_snapshot_ingetrans.png')
    print('Wrote', out / 'ui_snapshot_ingetrans.png')

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
