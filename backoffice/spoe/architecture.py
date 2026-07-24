from __future__ import annotations

from dataclasses import asdict
from typing import Dict, List

from backoffice.ui.workbench_framework.scoring import global_score, normalize_scores

from .models import ArchitectureAlternative


def evaluate_architecture_alternatives() -> Dict:
    alternatives: List[ArchitectureAlternative] = [
        ArchitectureAlternative(
            name="A1 | Monolithic Workbench",
            description="Single large page with embedded business logic.",
            metrics_0_10={
                "Maintainability": 4.5,
                "Scalability": 4.0,
                "Template Reuse": 3.5,
                "Engineering Accuracy": 6.0,
                "Commercial Flexibility": 5.0,
                "Knowledge Integration": 4.0,
                "Coordinator Integration": 4.0,
                "Future Products": 3.0,
                "EDT Compatibility": 5.0,
            },
        ),
        ArchitectureAlternative(
            name="A2 | Framework Extension (Chosen)",
            description="Extend existing workbench framework with dedicated SPOE services and templates.",
            metrics_0_10={
                "Maintainability": 9.0,
                "Scalability": 8.5,
                "Template Reuse": 9.0,
                "Engineering Accuracy": 8.5,
                "Commercial Flexibility": 8.5,
                "Knowledge Integration": 8.0,
                "Coordinator Integration": 8.0,
                "Future Products": 9.0,
                "EDT Compatibility": 8.5,
            },
        ),
        ArchitectureAlternative(
            name="A3 | Separate Microservice",
            description="Isolated SPOE service with API gateway bridge to the platform.",
            metrics_0_10={
                "Maintainability": 7.5,
                "Scalability": 9.0,
                "Template Reuse": 7.0,
                "Engineering Accuracy": 8.0,
                "Commercial Flexibility": 8.0,
                "Knowledge Integration": 7.0,
                "Coordinator Integration": 7.5,
                "Future Products": 8.5,
                "EDT Compatibility": 7.0,
            },
        ),
        ArchitectureAlternative(
            name="A4 | Plugin Runtime",
            description="Dynamic plugin loading for product templates with registry-backed policies.",
            metrics_0_10={
                "Maintainability": 8.0,
                "Scalability": 8.5,
                "Template Reuse": 9.5,
                "Engineering Accuracy": 7.5,
                "Commercial Flexibility": 8.0,
                "Knowledge Integration": 7.5,
                "Coordinator Integration": 7.5,
                "Future Products": 9.5,
                "EDT Compatibility": 8.0,
            },
        ),
    ]

    weighted = {
        "Maintainability": 1.2,
        "Scalability": 1.1,
        "Template Reuse": 1.2,
        "Engineering Accuracy": 1.2,
        "Commercial Flexibility": 1.0,
        "Knowledge Integration": 1.0,
        "Coordinator Integration": 1.1,
        "Future Products": 1.1,
        "EDT Compatibility": 1.1,
    }

    scored = []
    for alt in alternatives:
        normalized = normalize_scores(alt.metrics_0_10)
        score = global_score(normalized, weighted)
        scored.append(
            {
                "name": alt.name,
                "description": alt.description,
                "metrics_0_10": alt.metrics_0_10,
                "normalized_0_100": normalized,
                "global_engineering_score": score,
            }
        )

    scored.sort(key=lambda x: x["global_engineering_score"], reverse=True)
    return {
        "alternatives": scored,
        "selected": scored[0],
    }
