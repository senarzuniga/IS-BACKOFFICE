"""Scoring utilities for Competitive Intelligence (heuristic).

These functions compute simple normalized scores used for prototypes and
testing. Replace with domain-tuned models in production.
"""

from typing import Dict


def _norm(x: float, denom: float) -> float:
    if denom <= 0:
        return 0.0
    return max(0.0, min(1.0, x / denom))


def compute_scores(profile: Dict) -> Dict[str, float]:
    """Compute a set of heuristic scores (0..1) for a company profile.

    profile keys used (optional): `capabilities`, `technologies`, `markets`.
    """
    caps = profile.get('capabilities') or []
    tech = profile.get('technologies') or []
    markets = profile.get('markets') or []

    market_strength = _norm(len(markets), 5.0)
    technology_level = _norm(len(tech), 5.0)
    service_capability = _norm(len(caps), 5.0)

    # composite metrics
    threat_level = max(0.0, min(1.0, (technology_level + market_strength) / 2.0))
    opportunity_level = max(0.0, min(1.0, 1.0 - threat_level))

    return {
        'market_strength': round(market_strength, 3),
        'technology_level': round(technology_level, 3),
        'service_capability': round(service_capability, 3),
        'threat_level': round(threat_level, 3),
        'opportunity_level': round(opportunity_level, 3),
    }
