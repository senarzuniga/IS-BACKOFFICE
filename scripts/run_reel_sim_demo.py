"""Run a short headless demo of the Reel Load Simulator (CorrugatorEngine).

This script runs both scenarios (A: Forklift, B: INGETRANS) for a short
duration and prints KPIs and a small snapshot so you can see how the engine behaves.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Dict


# Ensure repo root is on path when running from scripts/
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def run_demo(duration_min: float = 60.0, seed: int | None = 42, config: Dict = None):
    from core.corrugator_engine import CorrugatorEngine

    cfg = config or {
        "num_tracks": 10,
        "num_forklifts": 1,
        "corrugator_speed_m_min": 250.0,
        "initial_reel_weight_kg": 1000.0,
        "dt_min": 0.5,
    }

    print("Running headless demo — duration: {} min, seed: {}".format(duration_min, seed))

    engines = {
        "A": CorrugatorEngine("A", cfg, seed),
        "B": CorrugatorEngine("B", cfg, seed),
    }

    # run both engines for duration
    for label, eng in engines.items():
        eng.running = True
        steps = int(max(1, duration_min / max(eng.dt, 1e-6)))
        for _ in range(steps):
            eng.step()

    # print results
    for label, eng in engines.items():
        print("\n--- Scenario {} ---".format(label))
        print(json.dumps(eng.get_kpis(), indent=2))
        snap = eng.get_snapshot()
        # print compact snapshot
        compact = {
            "time_min": snap.get("time", 0.0),
            "queue_length": snap.get("queue_length", 0),
            "tracks_occupied": sum(1 for t in snap.get("tracks", []) if t.get("occupied")),
        }
        print("Snapshot:", json.dumps(compact, indent=2))


if __name__ == "__main__":
    run_demo(duration_min=120.0, seed=42)
