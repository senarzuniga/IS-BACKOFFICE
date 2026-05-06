"""Pricing intelligence – classifies competitor pricing into market bands."""
from __future__ import annotations


# Pricing bands for corrugated machinery (EUR)
_PREMIUM_THRESHOLD = 350_000
_MIDRANGE_THRESHOLD = 120_000


def build_pricing_insight(payload: dict) -> dict | None:
    price = payload.get("price_estimated") if isinstance(payload.get("price_estimated"), dict) else None
    if not price or price.get("value") is None:
        return None
    value = float(price["value"])
    if value > _PREMIUM_THRESHOLD:
        impact = "high"
        message = (
            "Competitor premium pricing detected (>{:,.0f} EUR). "
            "Reinforce value-selling and service differentiation.".format(_PREMIUM_THRESHOLD)
        )
    elif value > _MIDRANGE_THRESHOLD:
        impact = "medium"
        message = (
            "Mid-range pricing band detected ({:,.0f}–{:,.0f} EUR). "
            "Opportunity for bundle optimisation.".format(_MIDRANGE_THRESHOLD, _PREMIUM_THRESHOLD)
        )
    else:
        impact = "low"
        message = (
            "Lower pricing tier detected (<{:,.0f} EUR). "
            "Prepare cost-plus fallback strategy.".format(_MIDRANGE_THRESHOLD)
        )
    return {"impact": impact, "message": message, "price_eur": value}
