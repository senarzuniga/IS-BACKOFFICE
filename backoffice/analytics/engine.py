from __future__ import annotations

from dataclasses import asdict
from typing import Any, Callable


class AIAnalyticsEngine:
    def __init__(self) -> None:
        self.extra_agents: dict[str, Callable[[Any, dict[str, Any]], Any]] = {}

    def register_agent(self, name: str, fn: Callable[[Any, dict[str, Any]], Any]) -> None:
        self.extra_agents[name] = fn

    def analyze(self, bundle: Any) -> dict:
        pipeline_value = sum(o.amount for o in bundle.opportunities)
        won_sales = sum(s.value for s in bundle.sales)
        conversion_probability = min(1.0, won_sales / max(pipeline_value, 1.0))

        anomalies = [
            asdict(offer)
            for offer in bundle.offers
            if offer.price <= 0 or (bundle.sales and offer.price > max(s.value for s in bundle.sales) * 5)
        ]

        account_health = {
            c.name: round(min(100.0, (len(c.contacts) * 20) + (won_sales / max(1, len(bundle.customers))) / 1000 * 10), 2)
            for c in bundle.customers
        }

        insights = {
            "sales_intelligence": {
                "pipeline_analysis": pipeline_value,
                "opportunity_scoring": {o.id: round(min(1.0, o.amount / 100000), 2) for o in bundle.opportunities},
                "deal_probability": conversion_probability,
            },
            "forecasting": {
                "revenue_forecast": round(won_sales + pipeline_value * conversion_probability, 2),
                "conversion_probability": round(conversion_probability, 2),
            },
            "portfolio_analysis": {
                "classification": self._classify_portfolio(bundle),
            },
            "key_account_intelligence": {
                "account_health": account_health,
                "opportunity_detection": [o.description for o in bundle.opportunities if o.amount > 0],
                "cross_sell_upsell": [s.product for s in bundle.sales],
            },
            "offer_validation": {
                "anomalies": anomalies,
                "consistency_ok": len(anomalies) == 0,
            },
        }

        for name, fn in self.extra_agents.items():
            insights[name] = fn(bundle, insights)

        return insights

    @staticmethod
    def _classify_portfolio(bundle: Any) -> dict[str, str]:
        labels: dict[str, str] = {}
        for sale in bundle.sales:
            if sale.value < 1000:
                labels[sale.product] = "commodity"
            elif sale.value < 5000:
                labels[sale.product] = "decline"
            elif sale.value < 20000:
                labels[sale.product] = "growth"
            else:
                labels[sale.product] = "innovation"
        return labels
