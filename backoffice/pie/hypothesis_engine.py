from __future__ import annotations

from dataclasses import asdict

from .models import DecisionRecord, Hypothesis


def _score(h: Hypothesis) -> float:
    # Weighted score: confidence and impact dominate, effort and risk are still considered.
    return (h.confidence * 0.35) + (h.impact * 0.35) + (h.effort * 0.10) + (h.risk_inverse * 0.20)


def evaluate_hypotheses(candidates: list[Hypothesis]) -> list[dict]:
    scored = []
    for item in candidates:
        scored.append({"hypothesis": asdict(item), "score": round(_score(item), 4)})
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored


def resolve_uncertainty(uncertainty: str, candidates: list[Hypothesis]) -> DecisionRecord:
    if not candidates:
        fallback = Hypothesis(
            key="AUTO-FALLBACK",
            strategy="Use conservative semantic reconstruction with design-system defaults",
            confidence=7.0,
            impact=7.0,
            effort=8.0,
            risk_inverse=8.0,
            notes="Fallback generated because no candidates were supplied.",
        )
        return DecisionRecord(uncertainty=uncertainty, selected_hypothesis=fallback, score=round(_score(fallback), 4))

    ranking = evaluate_hypotheses(candidates)
    top = ranking[0]
    h = Hypothesis(**top["hypothesis"])
    return DecisionRecord(uncertainty=uncertainty, selected_hypothesis=h, score=top["score"])
