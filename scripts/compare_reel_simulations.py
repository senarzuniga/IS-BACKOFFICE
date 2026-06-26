"""Compare Reel Load Simulator across multiple configs and seeds.

Produces a JSON report under `reports/` and prints a concise table to stdout.
"""
from __future__ import annotations

import json
import os
import sys
import time
from collections import defaultdict
from statistics import mean, stdev
from typing import Dict, List


# ensure repo root on path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def run_one(cfg: Dict, scenario: str, duration_min: float, seed: int) -> Dict:
    from core.corrugator_engine import CorrugatorEngine

    eng = CorrugatorEngine(scenario, cfg, seed)
    # run headless
    eng.run(duration_min)
    k = eng.get_kpis()
    # attach time and snapshot basics
    snap = eng.get_snapshot()
    return {"kpis": k, "snapshot": {"time": snap.get("time", 0.0), "queue_len": snap.get("queue_length", 0), "tracks_occupied": sum(1 for t in snap.get("tracks", []) if t.get("occupied"))}}


def calculate_roi(kA: Dict, kB: Dict, cfg: Dict) -> Dict:
    # similar heuristic to demo
    meters_A = kA.get("meters_produced", 0)
    meters_B = kB.get("meters_produced", 0)
    extra_meters = meters_B - meters_A
    starvation_A = kA.get("starvation_time", 0)
    starvation_B = kB.get("starvation_time", 0)
    saved_starvation = max(0.0, starvation_A - starvation_B)
    value_per_meter = float(cfg.get("value_per_meter", 0.5))
    lost_value = extra_meters * value_per_meter
    corrugator_cost_hour = float(cfg.get("corrugator_cost_hour", 500))
    saved_cost = (saved_starvation / 60.0) * corrugator_cost_hour
    labor_cost_hour = float(cfg.get("labor_cost_hour", 35))
    labor_saved = ((kA.get("utilization", 0) - kB.get("utilization", 0)) / 100.0) * labor_cost_hour
    # annualize: assume 8h shifts, 330 working days
    total_savings = lost_value + saved_cost + labor_saved * 8 * 330
    capex = float(cfg.get("capex_eur", 350000))
    payback = capex / total_savings if total_savings > 0 else None
    return {"extra_meters": extra_meters, "total_savings_eur": total_savings, "payback_years": round(payback, 2) if payback else None}


def run_benchmarks(duration_min: float = 480.0, seeds: List[int] = None):
    seeds = seeds or [42, 43, 44, 45, 46]

    baseline = {
        "num_tracks": 10,
        "num_forklifts": 1,
        "corrugator_speed_m_min": 250.0,
        "initial_reel_weight_kg": 1000.0,
        "dt_min": 0.5,
    }

    experiments = [
        ("baseline", dict(baseline)),
        ("more_forklifts", dict({**baseline, "num_forklifts": 3})),
        ("more_tracks", dict({**baseline, "num_tracks": 20, "buffer_capacity": 20})),
        ("fast_ingetrans", dict({**baseline, "transfer_speed": 120.0, "transfer_capacity": 2})),
        ("fast_forklifts", dict({**baseline, "forklift_speed_loaded": 120.0})),
    ]

    results = {}

    total_runs = len(experiments) * len(seeds) * 2
    cur_run = 0
    start_time = time.time()

    for name, cfg in experiments:
        results[name] = {"cfg": cfg, "runs": []}
        for seed in seeds:
            cur_run += 1
            print(f"Run {cur_run}/{total_runs}: exp={name} seed={seed} scenario=A")
            rA = run_one(cfg, "A", duration_min, seed)
            print(f"Run {cur_run}/{total_runs}: exp={name} seed={seed} scenario=B")
            rB = run_one(cfg, "B", duration_min, seed)

            roi = calculate_roi(rA["kpis"], rB["kpis"], cfg)

            results[name]["runs"].append({"seed": seed, "A": rA, "B": rB, "roi": roi})

    # aggregate
    summary = {}
    for name, data in results.items():
        metrics_by_seed = defaultdict(list)
        for run in data["runs"]:
            kA = run["A"]["kpis"]
            kB = run["B"]["kpis"]
            metrics_by_seed["A_meters"].append(kA.get("meters_produced", 0))
            metrics_by_seed["B_meters"].append(kB.get("meters_produced", 0))
            metrics_by_seed["A_oee"].append(kA.get("oee", 0))
            metrics_by_seed["B_oee"].append(kB.get("oee", 0))
            metrics_by_seed["A_starvation_time"].append(kA.get("starvation_time", 0))
            metrics_by_seed["B_starvation_time"].append(kB.get("starvation_time", 0))
            metrics_by_seed["payback"].append(run["roi"].get("payback_years"))

        def agg(lst):
            return {"mean": mean(lst), "stdev": stdev(lst) if len(lst) > 1 else 0.0}

        summary[name] = {
            "A_meters": agg(metrics_by_seed["A_meters"]),
            "B_meters": agg(metrics_by_seed["B_meters"]),
            "A_oee": agg(metrics_by_seed["A_oee"]),
            "B_oee": agg(metrics_by_seed["B_oee"]),
            "A_starvation_time": agg(metrics_by_seed["A_starvation_time"]),
            "B_starvation_time": agg(metrics_by_seed["B_starvation_time"]),
            "payback_years": agg([p for p in metrics_by_seed["payback"] if p is not None]),
        }

    duration = time.time() - start_time
    report = {"duration_min": duration_min, "seeds": seeds, "experiments": results, "summary": summary, "wall_time_s": duration}

    out_dir = os.path.join(ROOT, "reports")
    os.makedirs(out_dir, exist_ok=True)
    ts = int(time.time())
    out_path = os.path.join(out_dir, f"reel_sim_comparison_{ts}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    # print brief summary
    print("\nBenchmark complete. Report saved to:", out_path)
    for name, s in summary.items():
        print(f"\nExperiment: {name}")
        print(f"  A meters mean: {s['A_meters']['mean']:.1f} ± {s['A_meters']['stdev']:.1f}")
        print(f"  B meters mean: {s['B_meters']['mean']:.1f} ± {s['B_meters']['stdev']:.1f}")
        print(f"  Extra meters mean: {(s['B_meters']['mean'] - s['A_meters']['mean']):.1f}")
        print(f"  A OEE mean: {s['A_oee']['mean']:.2f}%  B OEE mean: {s['B_oee']['mean']:.2f}%")
        print(f"  Payback mean (years): {s['payback_years']['mean']:.2f}")

    return out_path


if __name__ == "__main__":
    # run default bench
    run_benchmarks(duration_min=480.0, seeds=[42, 43, 44, 45, 46])
