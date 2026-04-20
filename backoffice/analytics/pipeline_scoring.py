"""Sales pipeline analysis and opportunity scoring."""
from __future__ import annotations
from typing import Any, Dict, List

from backoffice.graph.store import GraphStore

# Stage → base probability
_STAGE_PROB = {
    "qualification": 0.20,
    "proposal": 0.40,
    "negotiation": 0.65,
    "closed_won": 1.00,
    "closed_lost": 0.00,
}


class PipelineScorer:
    """Scores opportunities and analyses the overall sales pipeline."""

    def __init__(self, store: GraphStore):
        self._store = store

    def score_opportunities(self) -> List[Dict[str, Any]]:
        results = []
        for opp in self._store.get_all_opportunities():
            base_prob = _STAGE_PROB.get(opp.stage, 0.3)
            # Boost if value is set
            value_boost = 0.05 if opp.estimated_value and opp.estimated_value > 0 else 0
            probability = min(base_prob + value_boost, 1.0)
            weighted_value = (opp.estimated_value or 0) * probability
            results.append({
                "opportunity_id": opp.id,
                "title": opp.title,
                "client_id": opp.client_id,
                "stage": opp.stage,
                "estimated_value": opp.estimated_value,
                "probability": probability,
                "weighted_value": round(weighted_value, 2),
                "evidence": f"Stage={opp.stage} → base_prob={base_prob}",
            })
        results.sort(key=lambda x: x["weighted_value"], reverse=True)
        return results

    def pipeline_summary(self) -> Dict[str, Any]:
        scored = self.score_opportunities()
        total_weighted = sum(r["weighted_value"] for r in scored)
        by_stage: Dict[str, int] = {}
        for r in scored:
            by_stage[r["stage"]] = by_stage.get(r["stage"], 0) + 1
        return {
            "total_opportunities": len(scored),
            "total_weighted_pipeline_eur": round(total_weighted, 2),
            "by_stage": by_stage,
            "top_opportunities": scored[:5],
        }
