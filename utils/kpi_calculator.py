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
    # estimar horas operador: para forklift sum utilization time de carretillas
    h_fork = sum([v for v in forklift_metrics.get("utilization", {}).values()]) / 60.0
    h_ing = sum([v for v in ingetrans_metrics.get("utilization", {}).values()]) / 60.0
    labor_cost = params.get("labor_cost_per_hour", 20.0)
    saved_hours = max(0.0, h_fork - h_ing)
    saved_cost = saved_hours * labor_cost
    return {"saved_hours": saved_hours, "saved_cost": saved_cost}
