#!/usr/bin/env python3
"""
Headless test runner for Reel_load_simulator.
"""
import sys
import os
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
# Ensure project root is on sys.path
sys.path.insert(0, str(ROOT))

try:
    from core.Reel_load_simulator import SimulationEngine
    from agents.Reel_load_simulator.work_order_agent import WorkOrderAgent
    from agents.Reel_load_simulator.config_agent import ConfigAgent
except Exception as e:
    print("Import error:", e)
    import traceback
    traceback.print_exc()
    sys.exit(2)


def run_test(steps=10):
    cfg = ConfigAgent().load_default()
    orders = WorkOrderAgent().generate_orders(8)
    a = SimulationEngine(cfg, orders, scenario="A")
    b = SimulationEngine(cfg, orders, scenario="B")
    print("Starting headless test for", steps, "steps")
    for i in range(steps):
        a.step()
        b.step()
        print(
            f"Step {i+1}: A time={getattr(a, 'time_min', None)} moves={getattr(a.result, 'movements', None)} reel_changes={getattr(a.result, 'reel_changes', None)} | "
            f"B time={getattr(b, 'time_min', None)} moves={getattr(b.result, 'movements', None)} reel_changes={getattr(b.result, 'reel_changes', None)}"
        )
    print("Final A:", a.result.__dict__)
    print("Final B:", b.result.__dict__)


if __name__ == "__main__":
    run_test(10)
