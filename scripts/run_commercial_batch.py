#!/usr/bin/env python3
"""Run batch commercial demo runs and export CSV for analysis.

Generates `reports/reel_demo_batch_results.csv` with one row per parameter
combination containing KPIs for Forklift and INGETRANS plus ROI estimates.
"""
import csv
import os
import sys
from typing import Dict, Any


def _ensure_repo_on_path():
    # ensure repo root is on sys.path when running from scripts/
    here = os.path.dirname(os.path.abspath(__file__))
    repo = os.path.abspath(os.path.join(here, os.pardir))
    if repo not in sys.path:
        sys.path.insert(0, repo)


def avg_utilization_pct(metrics: Dict[str, Any]) -> float:
    vals = []
    u = metrics.get("utilization_pct") or metrics.get("utilization") or {}
    if isinstance(u, dict):
        for v in u.values():
            try:
                vals.append(float(v))
            except Exception:
                pass
    return sum(vals) / len(vals) if vals else 0.0


def run():
    _ensure_repo_on_path()
    from core.commercial_simulator import run_commercial_demo
    from utils.kpi_calculator import compute_roi

    # Parameter grid (reasonable defaults for exploratory analysis)
    orders_grid = [80, 100, 120, 140, 160]
    shift_minutes_grid = [480]
    labor_cost_grid = [20.0, 25.0, 30.0]
    capex_grid = [250000.0, 350000.0, 450000.0]
    workdays_grid = [220, 250]
    shifts_grid = [1.0, 2.0]

    out_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "reports")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "reel_demo_batch_results.csv")

    fieldnames = [
        "orders_per_shift",
        "shift_minutes",
        "capex",
        "labor_cost_per_hour",
        "workdays_per_year",
        "shifts_per_day",

        # Forklift KPIs
        "forklift_reel_changes_per_hour",
        "forklift_oee",
        "forklift_utilization_pct_avg",
        "forklift_starvations",
        "forklift_distance_km",
        "forklift_completed_orders",
        "forklift_total_vehicle_minutes",

        # INGETRANS KPIs
        "ingetrans_reel_changes_per_hour",
        "ingetrans_oee",
        "ingetrans_utilization_pct_avg",
        "ingetrans_starvations",
        "ingetrans_distance_km",
        "ingetrans_completed_orders",
        "ingetrans_total_vehicle_minutes",

        # Differential / ROI
        "delta_reel_changes_per_hour",
        "delta_completed_orders",
        "saved_hours_per_shift",
        "saved_hours_per_year",
        "saved_cost_per_year",
        "estimated_payback_years",
    ]

    rows = []
    for orders in orders_grid:
        for shift_min in shift_minutes_grid:
            demo = run_commercial_demo(shift_min=shift_min, orders_per_shift=orders)
            kA = demo.get("forklift", {})
            kB = demo.get("ingetrans", {})

            for capex in capex_grid:
                for labor_cost in labor_cost_grid:
                    for workdays in workdays_grid:
                        for shifts in shifts_grid:
                            roi = compute_roi(kA, kB, {
                                "labor_cost_per_hour": labor_cost,
                                "workdays_per_year": workdays,
                                "shifts_per_day": shifts,
                                "capex": capex,
                            })

                            row = {
                                "orders_per_shift": orders,
                                "shift_minutes": shift_min,
                                "capex": capex,
                                "labor_cost_per_hour": labor_cost,
                                "workdays_per_year": workdays,
                                "shifts_per_day": shifts,

                                "forklift_reel_changes_per_hour": kA.get("reel_changes_per_hour"),
                                "forklift_oee": kA.get("oee"),
                                "forklift_utilization_pct_avg": avg_utilization_pct(kA),
                                "forklift_starvations": kA.get("starvations"),
                                "forklift_distance_km": round(float(kA.get("distance_m", 0.0)) / 1000.0, 3),
                                "forklift_completed_orders": kA.get("completed_orders"),
                                "forklift_total_vehicle_minutes": kA.get("total_vehicle_minutes"),

                                "ingetrans_reel_changes_per_hour": kB.get("reel_changes_per_hour"),
                                "ingetrans_oee": kB.get("oee"),
                                "ingetrans_utilization_pct_avg": avg_utilization_pct(kB),
                                "ingetrans_starvations": kB.get("starvations"),
                                "ingetrans_distance_km": round(float(kB.get("distance_m", 0.0)) / 1000.0, 3),
                                "ingetrans_completed_orders": kB.get("completed_orders"),
                                "ingetrans_total_vehicle_minutes": kB.get("total_vehicle_minutes"),

                                "delta_reel_changes_per_hour": (kA.get("reel_changes_per_hour", 0) - kB.get("reel_changes_per_hour", 0)),
                                "delta_completed_orders": (kA.get("completed_orders", 0) - kB.get("completed_orders", 0)),

                                "saved_hours_per_shift": roi.get("saved_hours_per_shift"),
                                "saved_hours_per_year": roi.get("saved_hours_per_year"),
                                "saved_cost_per_year": roi.get("saved_cost_per_year"),
                                "estimated_payback_years": roi.get("estimated_payback_years"),
                            }
                            rows.append(row)

    # write CSV
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

    print(f"Wrote {len(rows)} rows to {out_path}")


if __name__ == "__main__":
    run()
