"""Run quick bottleneck experiments to reveal differences between Forklift and INGETRANS.

Runs several constrained configs across a few seeds and prints aggregated KPIs.
"""
from __future__ import annotations

import json
import os
import sys
from statistics import mean
from typing import Dict, List

# ensure repo root on path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.corrugator_engine import CorrugatorEngine


def run_one(cfg: Dict, scenario: str, seed: int, duration_min: float):
    eng = CorrugatorEngine(scenario, cfg.copy(), seed)
    eng.running = True
    steps = int(max(1, duration_min / max(eng.dt, 1e-9)))
    for _ in range(steps):
        eng.step()
    return eng.get_kpis()


def main():
    duration_min = 240.0
    seeds = [1, 2, 42]

    experiments = [
        ("tight_tracks", {"num_tracks": 1, "num_forklifts": 1, "dt_min": 0.5}),
        ("limited_buffer", {"buffer_capacity": 1, "num_forklifts": 1, "num_tracks": 5, "dt_min": 0.5}),
        ("slow_forklift", {"num_tracks": 5, "num_forklifts": 1, "forklift_speed_loaded": 30.0, "dt_min": 0.5}),
        ("fast_ingetrans", {"num_tracks": 5, "num_forklifts": 1, "transfer_speed": 120.0, "dt_min": 0.5}),
    ]

    print(f"Running bottleneck experiments: duration={duration_min} min, seeds={seeds}")

    report = {}
    for name, cfg in experiments:
        print(f"\n--- Experiment: {name} ---")
        metrics_A = []
        metrics_B = []
        for seed in seeds:
            print(f"Seed {seed} scenario A...", end=' ')
            kA = run_one(cfg, "A", seed, duration_min)
            print(f"done (meters={kA.get('meters_produced'):.1f}, oee={kA.get('oee'):.2f})")
            metrics_A.append(kA)

            print(f"Seed {seed} scenario B...", end=' ')
            kB = run_one(cfg, "B", seed, duration_min)
            print(f"done (meters={kB.get('meters_produced'):.1f}, oee={kB.get('oee'):.2f})")
            metrics_B.append(kB)

        # aggregate
        def agg(key):
            valsA = [m.get(key, 0.0) for m in metrics_A]
            valsB = [m.get(key, 0.0) for m in metrics_B]
            return {"A_mean": mean(valsA), "B_mean": mean(valsB)}

        summary = {
            "meters": agg("meters_produced"),
            "oee": agg("oee"),
            "starvation_time": agg("starvation_time"),
        }
        report[name] = {"cfg": cfg, "summary": summary}
        print(f"Summary {name}: meters A={summary['meters']['A_mean']:.1f} | B={summary['meters']['B_mean']:.1f}")

    # save report
    out_dir = os.path.join(ROOT, "data", "benchmarks")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "bottleneck_experiments.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"\nSaved report to: {out_path}")


if __name__ == "__main__":
    main()
