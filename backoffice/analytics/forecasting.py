"""Revenue forecasting using historical sales data."""
from __future__ import annotations
from typing import Any, Dict, List
from collections import defaultdict

from backoffice.graph.store import GraphStore


class Forecaster:
    """Simple trend-based revenue forecaster."""

    def __init__(self, store: GraphStore):
        self._store = store

    def monthly_revenue(self) -> Dict[str, float]:
        """Aggregate sales by YYYY-MM."""
        monthly: Dict[str, float] = defaultdict(float)
        for sale in self._store.get_all_sales():
            if sale.sale_date:
                key = sale.sale_date.strftime("%Y-%m")
                monthly[key] += sale.amount_eur or sale.amount
        return dict(sorted(monthly.items()))

    def forecast_next_period(self, periods: int = 3) -> Dict[str, Any]:
        """Forecast next N months using simple linear trend."""
        monthly = self.monthly_revenue()
        values = list(monthly.values())
        keys = list(monthly.keys())

        if len(values) < 2:
            avg = values[0] if values else 0.0
            forecasted = {f"forecast_{i+1}": round(avg, 2) for i in range(periods)}
            return {"method": "average", "forecasted_periods": forecasted, "evidence": "Insufficient history"}

        # Linear regression: y = a + b*x
        n = len(values)
        x_mean = (n - 1) / 2
        y_mean = sum(values) / n
        b_num = sum((i - x_mean) * (v - y_mean) for i, v in enumerate(values))
        b_den = sum((i - x_mean) ** 2 for i in range(n))
        b = b_num / b_den if b_den != 0 else 0
        a = y_mean - b * x_mean

        forecasted = {}
        for i in range(periods):
            x = n + i
            val = max(0.0, a + b * x)
            forecasted[f"period_{i+1}"] = round(val, 2)

        return {
            "method": "linear_trend",
            "historical_months": keys,
            "trend_slope": round(b, 2),
            "forecasted_periods": forecasted,
            "evidence": f"Linear regression over {n} data points",
        }

    def conversion_probability(self) -> Dict[str, Any]:
        """Estimate lead-to-sale conversion probability."""
        total_opps = len(self._store.get_all_opportunities())
        won = sum(1 for o in self._store.get_all_opportunities() if o.stage == "closed_won")
        lost = sum(1 for o in self._store.get_all_opportunities() if o.stage == "closed_lost")
        total_closed = won + lost
        prob = won / total_closed if total_closed > 0 else None
        return {
            "total_opportunities": total_opps,
            "won": won,
            "lost": lost,
            "conversion_probability": round(prob, 3) if prob is not None else "insufficient_data",
        }
