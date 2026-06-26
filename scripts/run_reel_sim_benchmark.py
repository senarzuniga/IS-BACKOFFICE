"""Batch benchmark for the Reel Load Simulator.

Runs scenarios A (Forklift) and B (INGETRANS) across multiple seeds
and configuration variants, aggregates KPI statistics and writes a
comparative JSON report to `data/benchmarks`.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
import time
import statistics
from typing import Dict, List


# ensure repo root on path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def run_one(cfg: Dict, scenario: str, seed: int, duration_min: float):
    from core.corrugator_engine import CorrugatorEngine

    eng = CorrugatorEngine(scenario, cfg.copy(), seed)
    eng.running = True
    steps = int(max(1, duration_min / max(eng.dt, 1e-9)))
    for _ in range(steps):
        eng.step()
    return eng.get_kpis(), eng.get_snapshot()


def mean_metrics(list_of_dicts: List[Dict]) -> Dict:
    if not list_of_dicts:
        return {}
    keys = set()
    for d in list_of_dicts:
        keys.update(d.keys())
    out = {}
    for k in sorted(keys):
        vals = []
        for d in list_of_dicts:
            v = d.get(k)
            try:
                vals.append(float(v))
            except Exception:
                pass
        out[k] = statistics.mean(vals) if vals else 0.0
    return out


def summarize_runs(list_of_dicts: List[Dict], keys=None) -> Dict:
    keys = keys or ["oee", "meters_produced", "starvation_time", "reels_changed", "downtime_min", "utilization"]
    summary = {}
    for k in keys:
        vals = []
        for d in list_of_dicts:
            try:
                vals.append(float(d.get(k, 0.0) or 0.0))
            except Exception:
                pass
        if not vals:
            summary[k] = {"mean": None, "stdev": None}
        else:
            summary[k] = {"mean": statistics.mean(vals), "stdev": statistics.stdev(vals) if len(vals) > 1 else 0.0}
    return summary


def calculate_roi(cfg: Dict, metrics_A: Dict, metrics_B: Dict) -> Dict:
    meters_A = float(metrics_A.get("meters_produced", 0.0))
    meters_B = float(metrics_B.get("meters_produced", 0.0))
    extra_meters = meters_B - meters_A
    starvation_A = float(metrics_A.get("starvation_time", 0.0))
    starvation_B = float(metrics_B.get("starvation_time", 0.0))
    saved_starvation_min = max(0.0, starvation_A - starvation_B)
    value_per_meter = float(cfg.get("value_per_meter", 0.5))
    lost_value = extra_meters * value_per_meter
    corrugator_cost_hour = float(cfg.get("corrugator_cost_hour", 500.0))
    saved_cost = (saved_starvation_min / 60.0) * corrugator_cost_hour
    labor_cost_hour = float(cfg.get("labor_cost_hour", 35.0))
    labor_saved = ((float(metrics_A.get("utilization", 0.0)) - float(metrics_B.get("utilization", 0.0))) / 100.0) * labor_cost_hour
    # annualize labor_saved: 8h * 330 working days
    total_savings = lost_value + saved_cost + labor_saved * 8.0 * 330.0
    capex = float(cfg.get("capex_eur", 350000.0))
    payback = capex / total_savings if total_savings > 0 else None
    return {"extra_meters": extra_meters, "total_savings_eur": total_savings, "payback_years": payback}


def main():
    configs = [
        {
            "name": "baseline",
            "num_tracks": 10,
            "num_forklifts": 1,
            "forklift_speed_loaded": 60.0,
            "transfer_speed": 80.0,
            "corrugator_speed_m_min": 250.0,
            "initial_reel_weight_kg": 1000.0,
            "dt_min": 0.5,
        },
        {
            "name": "more_tracks",
            "num_tracks": 20,
            "num_forklifts": 1,
            "forklift_speed_loaded": 60.0,
            "transfer_speed": 80.0,
            "corrugator_speed_m_min": 250.0,
            "initial_reel_weight_kg": 1000.0,
            "dt_min": 0.5,
        },
        {
            "name": "more_forklifts",
            "num_tracks": 10,
            "num_forklifts": 3,
            "forklift_speed_loaded": 60.0,
            "transfer_speed": 80.0,
            "corrugator_speed_m_min": 250.0,
            "initial_reel_weight_kg": 1000.0,
            "dt_min": 0.5,
        },
        {
            "name": "faster_transfer",
            "num_tracks": 10,
            "num_forklifts": 1,
            "forklift_speed_loaded": 60.0,
            "transfer_speed": 100.0,
            "corrugator_speed_m_min": 250.0,
            "initial_reel_weight_kg": 1000.0,
            "dt_min": 0.5,
        },
    ]

    seeds = [1, 2, 3, 42]
    duration_min = 480.0  # 8 hours

    out_dir = Path(ROOT) / "data" / "benchmarks"
    out_dir.mkdir(parents=True, exist_ok=True)

    report = {"meta": {"duration_min": duration_min, "seeds": seeds, "timestamp": time.time()}, "configs": {}}

    for cfg in configs:
        name = cfg["name"]
        print(f"\n=== Running config: {name} (tracks={cfg['num_tracks']}, forklifts={cfg['num_forklifts']}, transfer_speed={cfg['transfer_speed']}) ===")
        results_A = []
        results_B = []
        for seed in seeds:
            print(f"Running seed={seed} scenario=A ...", end=" ")
            kA, _ = run_one(cfg, "A", seed, duration_min)
            print(f"done (meters={kA.get('meters_produced'):.1f}, oee={kA.get('oee'):.2f})")
            results_A.append(kA)

            print(f"Running seed={seed} scenario=B ...", end=" ")
            kB, _ = run_one(cfg, "B", seed, duration_min)
            print(f"done (meters={kB.get('meters_produced'):.1f}, oee={kB.get('oee'):.2f})")
            results_B.append(kB)

        meanA = mean_metrics(results_A)
        meanB = mean_metrics(results_B)
        summaryA = summarize_runs(results_A)
        summaryB = summarize_runs(results_B)
        roi = calculate_roi(cfg, meanA, meanB)

        report["configs"][name] = {
            "config": cfg,
            "summary_A": summaryA,
            "summary_B": summaryB,
            "mean_A": meanA,
            "mean_B": meanB,
            "roi": roi,
        }

    # write JSON report
    fname = out_dir / f"reel_sim_benchmark_{int(time.time())}.json"
    with open(fname, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    # print compact report
    print(f"\nBenchmark complete — report saved to: {fname}")
    for name, r in report["configs"].items():
        meanA = r["mean_A"]
        meanB = r["mean_B"]
        print(f"\n{name}: avg meters A={meanA.get('meters_produced',0):.1f} | B={meanB.get('meters_produced',0):.1f} | extra_meters={r['roi']['extra_meters']:.1f} | payback={r['roi']['payback_years']}")


if __name__ == "__main__":
    main()
