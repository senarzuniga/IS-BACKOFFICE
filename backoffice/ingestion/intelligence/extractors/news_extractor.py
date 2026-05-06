"""News extractor – keyword-driven impact classifier for industry news."""
from __future__ import annotations

import re


class NewsExtractor:
    _HIGH_IMPACT = ["acquisition", "plant", "expansion", "price increase", "investment", "new line", "capacity"]
    _MED_IMPACT = ["partnership", "launch", "contract", "agreement", "growth"]

    async def extract(self, html: str) -> tuple[dict, float]:
        text = re.sub(r"\s+", " ", html)[:3000].lower()
        if any(k in text for k in self._HIGH_IMPACT):
            impact = "high"
        elif any(k in text for k in self._MED_IMPACT):
            impact = "medium"
        else:
            impact = "low"
        return {
            "headline": text[:180],
            "summary": text[:500],
            "impact_level": impact,
            "commercial_implication": "Review pricing and opportunity targeting.",
        }, 0.6
