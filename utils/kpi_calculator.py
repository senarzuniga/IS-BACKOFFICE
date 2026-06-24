"""Cálculo de KPIs y métricas diferenciales entre dos motores.
"""
from typing import Dict, Any


def compute_differential_kpis(kpi_a: Dict[str, Any], kpi_b: Dict[str, Any]) -> Dict[str, Any]:
    # A - B (por ejemplo, forklift minus ingetrans)
    dk = {}
    dk["reel_changes_diff"] = kpi_a.get("reel_changes_hour", 0) - kpi_b.get("reel_changes_hour", 0)
    dk["distance_m_diff"] = kpi_a.get("distance_m", 0) - kpi_b.get("distance_m", 0)
    dk["collisions_diff"] = kpi_a.get("collisions", 0) - kpi_b.get("collisions", 0)
    dk["starvations_diff"] = kpi_a.get("starvations", 0) - kpi_b.get("starvations", 0)
    # Riesgo de colisión heurístico
    def risk(c):
        if c > 10:
            return "Alto"
        if c > 3:
            return "Medio"
        return "Bajo"

    dk["collision_risk_a"] = risk(kpi_a.get("collisions", 0))
    dk["collision_risk_b"] = risk(kpi_b.get("collisions", 0))
    return dk


def compute_roi(forklift_metrics: Dict[str, Any], ingetrans_metrics: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
    """Cálculo simplificado de ROI basado en diferencial de horas de operador y costes.
    params: {'labor_cost_per_hour': float}
    """
    # Expected keys: 'utilization_minutes' or 'total_vehicle_minutes' and 'time_min'
    labor_cost = float(params.get("labor_cost_per_hour", 20.0))
    workdays = int(params.get("workdays_per_year", 250))
    shifts_per_day = float(params.get("shifts_per_day", 1.0))
    capex = float(params.get("capex", 350000.0))

    # compute total vehicle hours during the measured period
    uf_min = float(forklift_metrics.get("total_vehicle_minutes", sum([v for v in forklift_metrics.get("utilization_minutes", {}).values()])) if forklift_metrics else 0.0)
    ui_min = float(ingetrans_metrics.get("total_vehicle_minutes", sum([v for v in ingetrans_metrics.get("utilization_minutes", {}).values()])) if ingetrans_metrics else 0.0)
    # duration of the run in minutes
    duration_min = float(forklift_metrics.get("time_min", ingetrans_metrics.get("time_min", 60.0)))
    # normalize to hours per shift
    uf_h_per_shift = (uf_min / 60.0) * (1.0 if duration_min >= 1e-6 else 0.0) * (480.0 / duration_min) if duration_min > 0 else uf_min / 60.0
    ui_h_per_shift = (ui_min / 60.0) * (1.0 if duration_min >= 1e-6 else 0.0) * (480.0 / duration_min) if duration_min > 0 else ui_min / 60.0

    # saved operator hours per shift
    saved_hours_per_shift = max(0.0, uf_h_per_shift - ui_h_per_shift)
    # annualize
    saved_hours_per_year = saved_hours_per_shift * shifts_per_day * workdays
    saved_cost_per_year = saved_hours_per_year * labor_cost

    # simple payback estimation
    payback_years = capex / saved_cost_per_year if saved_cost_per_year > 0 else float("inf")

    return {
        "saved_hours_per_shift": saved_hours_per_shift,
        "saved_hours_per_year": saved_hours_per_year,
        "saved_cost_per_year": saved_cost_per_year,
        "estimated_payback_years": payback_years,
        "capex": capex,
    }
