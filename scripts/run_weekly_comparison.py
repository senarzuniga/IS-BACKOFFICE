#!/usr/bin/env python3
import json
import math
import os
import sys
from datetime import datetime
from pathlib import Path

# ensure repo root on path for direct script execution
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.consumption_engine import CorrugatorEngineV3
from core.kpi_calculator import calculate_kpis


def run_simulation_for_week(config: dict, scenario: str, seed: int = 0):
    # 7 days, 24h/day, 1 minute steps
    minutes = 7 * 24 * 60
    step_min = 1.0
    sample_interval_min = 60  # hourly samples
    engine = CorrugatorEngineV3(config=dict(config), scenario=scenario, seed=seed)

    hourly = []
    last_prod = 0.0
    for minute in range(minutes):
        engine.step(step_min)
        if (minute + 1) % sample_interval_min == 0:
            kpis = calculate_kpis(engine)
            prod = engine.metrics.get("production_meters", 0.0)
            hourly.append({
                "time_min": minute + 1,
                "produced_this_hour": prod - last_prod,
                "total_produced": prod,
                "OEE": kpis.get("OEE", 0.0),
                "LPI": kpis.get("LPI", 0.0),
                "RRI": kpis.get("RRI", 0.0),
                "PSS": kpis.get("PSS", 0.0),
                "track_saturation": kpis.get("track_saturation", 0.0),
                "starvation_count": engine.metrics.get("starvation_count", 0),
                "deliveries_scheduled": engine.metrics.get("deliveries_scheduled", 0),
                "deliveries_successful": engine.metrics.get("deliveries_successful", 0),
            })
            last_prod = prod

    # summarize
    total_prod = engine.metrics.get("production_meters", 0.0)
    starvation = engine.metrics.get("starvation_count", 0)
    scheduled = engine.metrics.get("deliveries_scheduled", 0)
    successful = engine.metrics.get("deliveries_successful", 0)
    avg_oee = sum(h["OEE"] for h in hourly) / max(len(hourly), 1)
    avg_lpi = sum(h["LPI"] for h in hourly) / max(len(hourly), 1)
    avg_rri = sum(h["RRI"] for h in hourly) / max(len(hourly), 1)
    avg_track_sat = sum(h["track_saturation"] for h in hourly) / max(len(hourly), 1)
    avg_pss = sum(h["PSS"] for h in hourly) / max(len(hourly), 1)

    # production per shift (assume 2 shifts/day -> 12h shifts)
    shifts_per_day = 2
    shift_minutes = 24 * 60 / shifts_per_day
    shifts_per_week = shifts_per_day * 7
    prod_per_shift = total_prod / max(shifts_per_week, 1)

    result = {
        "scenario": scenario,
        "total_produced_m": total_prod,
        "starvation_count": starvation,
        "deliveries_scheduled": scheduled,
        "deliveries_successful": successful,
        "PSS_percent": 100.0 * successful / scheduled if scheduled > 0 else 0.0,
        "avg_OEE_percent": avg_oee,
        "avg_LPI": avg_lpi,
        "avg_RRI": avg_rri,
        "avg_track_saturation": avg_track_sat,
        "avg_PSS_percent": avg_pss,
        "prod_per_shift_m": prod_per_shift,
        "hourly_series": hourly,
    }

    return result


def main():
    repo_root = Path(__file__).resolve().parents[1]
    cfg_path = repo_root / "data" / "config_default.json"
    with open(cfg_path, "r", encoding="utf-8") as fh:
        config = json.load(fh)

    # set some reproducible seeds
    seed = 12345

    print("Running weekly simulation for scenario A (Forklift, reactive)...")
    resA = run_simulation_for_week(config, "A", seed=seed)
    print("Running weekly simulation for scenario B (INGETRANS, predictive)...")
    resB = run_simulation_for_week(config, "B", seed=seed)

    # save results
    out_dir = repo_root / "data" / "benchmarks"
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    out_file = out_dir / f"week_compare_{ts}.json"
    with open(out_file, "w", encoding="utf-8") as fh:
        json.dump({"A": resA, "B": resB}, fh, indent=2)

    # print concise comparative summary
    def print_summary(r):
        print(f"Scenario {r['scenario']}")
        print(f"  Total produced (m): {r['total_produced_m']:.1f}")
        print(f"  Avg OEE (%): {r['avg_OEE_percent']:.2f}")
        print(f"  Starvation events: {r['starvation_count']}")
        print(f"  Deliveries scheduled/successful: {r['deliveries_scheduled']}/{r['deliveries_successful']} (PSS avg {r['avg_PSS_percent']:.1f}%)")
        print(f"  Avg Track Saturation (%): {r['avg_track_saturation']:.1f}")
        print(f"  Avg RRI: {r['avg_RRI']:.2f}")
        print(f"  Avg LPI: {r['avg_LPI']:.2f}")
        print(f"  Production per shift (m): {r['prod_per_shift_m']:.1f}")

    print("\n--- Weekly Summary ---")
    print_summary(resA)
    print_summary(resB)

    print(f"\nSaved detailed results to: {out_file}")


if __name__ == "__main__":
    main()
