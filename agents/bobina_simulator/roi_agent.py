"""ROI Agent — calcula ahorros y payback básicos para INGETRANS vs Carretillas."""
from __future__ import annotations

from typing import Dict, Any


class ROIAgent:
    """Cálculo heurístico de ROI. Es una implementación mínima para prototipo."""

    def estimate(self, metrics_a: Dict[str, Any], metrics_b: Dict[str, Any]) -> Dict[str, Any]:
        """Devuelve dict con ahorro anual estimado y payback.

        - metrics_a: escenario A (carretillas)
        - metrics_b: escenario B (ingetrans)
        """
        # heurística: reducir downtime y movimientos reduce coste
        mov_a = metrics_a.get("movements", 100)
        mov_b = metrics_b.get("movements", 80)
        dow_a = metrics_a.get("downtime_min", 60)
        dow_b = metrics_b.get("downtime_min", 10)

        savings_mov = max(0, (mov_a - mov_b) * 12)  # arbitrariedad
        savings_dow = max(0, (dow_a - dow_b) * 50)

        annual_savings = savings_mov + savings_dow
        capex = 800000  # coste de ejemplo
        payback_years = capex / annual_savings if annual_savings > 0 else None

        return {
            "annual_savings_eur": round(annual_savings, 2),
            "capex_eur": capex,
            "payback_years": round(payback_years, 2) if payback_years else None,
        }
