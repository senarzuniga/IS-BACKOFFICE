"""KPI computations for Reel Load Simulator.

Provides a small helper to compute KPIs from the engine state.
"""
from __future__ import annotations

from typing import Dict, Any


def compute_kpis(state: Dict[str, Any]) -> Dict[str, Any]:
    metrics = state.get("metrics", {})
    time_min = metrics.get("time_min", 0.0) or 0.0
    movements = metrics.get("movements", 0) or 0
    reel_changes = metrics.get("reel_changes", 0) or 0

    hours = (time_min / 60.0) if time_min > 0 else 0.0
    reel_changes_per_hour = (reel_changes / hours) if hours > 0 else 0.0

    avg_time_per_task = (time_min / movements) if movements > 0 else None

    return {
        "time_min": time_min,
        "movements": movements,
        "reel_changes": reel_changes,
        "reel_changes_per_hour": round(reel_changes_per_hour, 2),
        "avg_time_per_task_min": round(avg_time_per_task, 2) if avg_time_per_task else None,
        "utilization_pct": metrics.get("utilization_pct", 0.0),
        "total_distance_m": metrics.get("total_distance_m", 0.0),
    }
