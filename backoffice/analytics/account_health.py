"""Account health scoring."""
from __future__ import annotations
from typing import Any, Dict, List

from backoffice.graph.store import GraphStore


class AccountHealthScorer:
    """Computes account health scores and detects cross-sell/upsell opportunities."""

    def __init__(self, store: GraphStore):
        self._store = store

    def score_client(self, client_id: str) -> Dict[str, Any]:
        client = self._store.get_client(client_id)
        if not client:
            return {"error": f"Client {client_id} not found"}

        sales = [s for s in self._store.get_all_sales() if s.client_id == client_id]
        opps = [o for o in self._store.get_all_opportunities() if o.client_id == client_id]
        offers = [o for o in self._store.get_all_offers() if o.client_id == client_id]

        total_revenue = sum(s.amount_eur or s.amount for s in sales)
        open_opps = sum(1 for o in opps if o.stage not in ("closed_won", "closed_lost"))
        won_opps = sum(1 for o in opps if o.stage == "closed_won")
        total_opps = len(opps)
        win_rate = won_opps / total_opps if total_opps > 0 else 0.0

        # Score components (0–100 each, weighted)
        revenue_score = min(total_revenue / 100_000, 1.0) * 40  # max 40 pts for 100k+ EUR
        win_score = win_rate * 30  # max 30 pts
        activity_score = min(open_opps / 3, 1.0) * 20  # max 20 pts for 3+ open opps
        offer_score = min(len(offers) / 5, 1.0) * 10  # max 10 pts for 5+ offers

        health_score = revenue_score + win_score + activity_score + offer_score

        # Cross-sell/upsell flags
        opportunities = []
        if win_rate > 0.5 and open_opps == 0:
            opportunities.append("upsell: high win rate, no open opportunities")
        if total_revenue > 0 and len(offers) < 2:
            opportunities.append("cross-sell: active buyer, few offers")

        return {
            "client_id": client_id,
            "client_name": client.name,
            "health_score": round(health_score, 1),
            "total_revenue_eur": round(total_revenue, 2),
            "win_rate": round(win_rate, 3),
            "open_opportunities": open_opps,
            "detected_opportunities": opportunities,
            "evidence": {
                "revenue_score": round(revenue_score, 1),
                "win_rate_score": round(win_score, 1),
                "activity_score": round(activity_score, 1),
                "offer_score": round(offer_score, 1),
            },
        }

    def score_all_clients(self) -> List[Dict[str, Any]]:
        results = [self.score_client(c.id) for c in self._store.get_all_clients()]
        results.sort(key=lambda x: x.get("health_score", 0), reverse=True)
        return results
