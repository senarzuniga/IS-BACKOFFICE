from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Dict, List

from backoffice.ui.workbench_framework.scoring import global_score, normalize_scores


METRICS = [
    "Strategic Alignment",
    "Engineering Quality",
    "Architecture Quality",
    "Knowledge Gain",
    "Maintainability",
    "Scalability",
    "Industrial Applicability",
    "Reuse Potential",
    "Coordinator Integration",
    "Knowledge Hub Integration",
    "Enterprise Digital Twin Integration",
    "Mission Graph Impact",
    "Capability Graph Impact",
    "Future Mission Unlock",
    "Technical Debt Reduction",
    "Testing Impact",
    "Documentation Impact",
    "Business Value",
    "Confidence",
    "Risk Inverse",
]


@dataclass
class Hypothesis:
    key: str
    architecture: str
    implementation_strategy: str
    expected_engineering_value: str
    knowledge_gain: str
    business_value: str
    reuse: str
    scalability: str
    technical_risk: str
    dependencies: List[str]
    future_unlock: str
    metrics_0_10: Dict[str, float]


def _weights() -> Dict[str, float]:
    return {
        "Strategic Alignment": 1.2,
        "Engineering Quality": 1.2,
        "Architecture Quality": 1.2,
        "Knowledge Gain": 1.0,
        "Maintainability": 1.1,
        "Scalability": 1.1,
        "Industrial Applicability": 1.0,
        "Reuse Potential": 1.1,
        "Coordinator Integration": 1.1,
        "Knowledge Hub Integration": 1.0,
        "Enterprise Digital Twin Integration": 1.0,
        "Mission Graph Impact": 1.0,
        "Capability Graph Impact": 1.0,
        "Future Mission Unlock": 1.1,
        "Technical Debt Reduction": 1.0,
        "Testing Impact": 1.0,
        "Documentation Impact": 0.9,
        "Business Value": 1.2,
        "Confidence": 1.1,
        "Risk Inverse": 1.2,
    }


def evaluate_hypotheses(hypotheses: List[Hypothesis]) -> Dict:
    scored = []
    weights = _weights()
    for hyp in hypotheses:
        normalized = normalize_scores(hyp.metrics_0_10)
        score = global_score(normalized, weights)
        scored.append(
            {
                **asdict(hyp),
                "normalized_0_100": normalized,
                "global_engineering_score": score,
            }
        )
    scored.sort(key=lambda x: x["global_engineering_score"], reverse=True)
    return {"evaluated": scored, "selected": scored[0] if scored else None}


def store_hypotheses(result: Dict, path: str = "knowledge_hub/spoe/hypotheses_log.jsonl") -> str:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(UTC).isoformat()
    with p.open("a", encoding="utf-8") as f:
        for hyp in result.get("evaluated", []):
            payload = {"timestamp": ts, **hyp}
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    return str(p)
