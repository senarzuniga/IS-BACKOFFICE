"""Offer anomaly detection and pricing validation."""
from __future__ import annotations
from typing import Any, Dict, List

from backoffice.graph.store import GraphStore


class OfferValidator:
    """Detects pricing anomalies by comparing offers to historical sale prices."""

    def __init__(self, store: GraphStore):
        self._store = store

    def validate_offer(self, offer_id: str) -> Dict[str, Any]:
        offer = self._store._offers.get(offer_id)
        if not offer:
            return {"error": f"Offer {offer_id} not found"}

        # Gather historical prices for same client
        client_sales = [
            s for s in self._store.get_all_sales()
            if s.client_id == offer.client_id
        ]
        historical_amounts = [s.amount_eur or s.amount for s in client_sales]

        anomalies = []
        if offer.total_value is None:
            anomalies.append("missing_price: offer has no total value")

        if historical_amounts and offer.total_value is not None:
            avg = sum(historical_amounts) / len(historical_amounts)
            stddev = (sum((x - avg) ** 2 for x in historical_amounts) / len(historical_amounts)) ** 0.5
            if stddev > 0 and abs(offer.total_value - avg) > 3 * stddev:
                anomalies.append(
                    f"price_outlier: {offer.total_value:.2f} vs avg {avg:.2f} (±{stddev:.2f})"
                )

        is_valid = len(anomalies) == 0
        return {
            "offer_id": offer_id,
            "title": offer.title,
            "total_value": offer.total_value,
            "is_valid": is_valid,
            "anomalies": anomalies,
            "historical_avg": round(sum(historical_amounts) / len(historical_amounts), 2) if historical_amounts else None,
        }

    def validate_all_offers(self) -> List[Dict[str, Any]]:
        return [self.validate_offer(o.id) for o in self._store.get_all_offers()]
