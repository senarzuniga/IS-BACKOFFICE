import json
from typing import Dict, Any, List
from .base_agent import BaseAgent


class BenchmarkAgent(BaseAgent):
    DIMENSIONS = [
        "Engineering",
        "Automation",
        "Digitalization",
        "AI",
        "Service",
        "Speed",
        "Flexibility",
        "CostValue",
        "ROI",
        "Innovation",
    ]

    def score_dimension(self, profile: Dict[str, Any], dim: str) -> Dict[str, Any]:
        text = " ".join([str(profile.get(k, "")) for k in ("description", "products", "tech_signals", "news_signals")])
        text = text.lower()
        base = 1
        if any(k in text for k in ["automation", "pilot", "retrofit", "robot", "palletiz"]):
            base = 4
        if any(k in text for k in ["ia", "ai", "predict", "dashboard", "digital"]):
            base = max(base, 3)
        # simple heuristics
        return {"dimension": dim, "score": base, "justification": f"Evidence mentions: {', '.join(profile.get('tech_signals', [])[:3])}"}

    def run(self, competitor_profile: Dict[str, Any], baseline_profile: Dict[str, Any]) -> Dict[str, Any]:
        results: List[Dict[str, Any]] = []
        for d in self.DIMENSIONS:
            results.append(self.score_dimension(competitor_profile, d))
        # produce markdown table
        md = "| Dimension | Score | Justification |\n|---|---:|---|\n"
        for r in results:
            md += f"| {r['dimension']} | {r['score']} | {r['justification']} |\n"

        return {"scores": results, "markdown": md}
