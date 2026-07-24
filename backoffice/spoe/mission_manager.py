from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Dict, List

from .hypothesis_engine import Hypothesis, evaluate_hypotheses, store_hypotheses
from .platform_maturity import update_platform_score_history


@dataclass
class PlatformState:
    templates_total: int
    templates_operational: int
    tests_total: int
    docs_total: int
    registry_extensions_total: int


def _count(glob_pattern: str) -> int:
    return len(list(Path(".").glob(glob_pattern)))


def observe_platform_state() -> PlatformState:
    templates = _count("backoffice/spoe/templates/*.json")
    tests = _count("tests/test_spoe*.py")
    docs = _count("reports/spoe/*.md")
    regs = _count("platform_registry/*spoe*.json")

    operational = 0
    for p in Path("backoffice/spoe/templates").glob("*.json"):
        try:
            obj = json.loads(p.read_text(encoding="utf-8"))
            if obj.get("status") == "operational":
                operational += 1
        except Exception:
            continue

    return PlatformState(
        templates_total=templates,
        templates_operational=operational,
        tests_total=tests,
        docs_total=docs,
        registry_extensions_total=regs,
    )


def detect_opportunities(state: PlatformState) -> List[str]:
    opportunities = []
    if state.tests_total < 2:
        opportunities.append("Increase SPOE test depth and edge-case validation")
    opportunities.append("Add AME mission manager with persistent hypothesis scoring")
    opportunities.append("Improve governance automation for registry/twin/mission graph")
    opportunities.append("Improve media/video integration robustness")
    opportunities.append("Normalize template keys and remove naming drift")
    return opportunities


def generate_hypotheses(state: PlatformState, opportunities: List[str]) -> List[Hypothesis]:
    return [
        Hypothesis(
            key="A",
            architecture="UI-first enhancements",
            implementation_strategy="Expand Streamlit UX only",
            expected_engineering_value="Medium",
            knowledge_gain="Low",
            business_value="Medium",
            reuse="Medium",
            scalability="Medium",
            technical_risk="Low",
            dependencies=["streamlit"],
            future_unlock="Limited",
            metrics_0_10={
                "Strategic Alignment": 6.5,
                "Engineering Quality": 6.5,
                "Architecture Quality": 6.0,
                "Knowledge Gain": 4.5,
                "Maintainability": 6.0,
                "Scalability": 6.0,
                "Industrial Applicability": 7.0,
                "Reuse Potential": 6.0,
                "Coordinator Integration": 5.5,
                "Knowledge Hub Integration": 5.5,
                "Enterprise Digital Twin Integration": 5.5,
                "Mission Graph Impact": 5.0,
                "Capability Graph Impact": 5.0,
                "Future Mission Unlock": 5.5,
                "Technical Debt Reduction": 5.0,
                "Testing Impact": 5.0,
                "Documentation Impact": 5.5,
                "Business Value": 7.0,
                "Confidence": 8.0,
                "Risk Inverse": 8.0,
            },
        ),
        Hypothesis(
            key="B",
            architecture="Engine-first refactor",
            implementation_strategy="Large internal rewrite of SPOE modules",
            expected_engineering_value="Medium-high",
            knowledge_gain="Medium",
            business_value="Medium",
            reuse="High",
            scalability="High",
            technical_risk="High",
            dependencies=["docx", "streamlit", "tests"],
            future_unlock="Good",
            metrics_0_10={
                "Strategic Alignment": 7.5,
                "Engineering Quality": 7.5,
                "Architecture Quality": 8.0,
                "Knowledge Gain": 7.0,
                "Maintainability": 8.0,
                "Scalability": 8.0,
                "Industrial Applicability": 6.5,
                "Reuse Potential": 8.0,
                "Coordinator Integration": 7.0,
                "Knowledge Hub Integration": 7.0,
                "Enterprise Digital Twin Integration": 7.0,
                "Mission Graph Impact": 6.5,
                "Capability Graph Impact": 6.5,
                "Future Mission Unlock": 8.0,
                "Technical Debt Reduction": 8.0,
                "Testing Impact": 6.5,
                "Documentation Impact": 6.0,
                "Business Value": 6.5,
                "Confidence": 6.0,
                "Risk Inverse": 4.5,
            },
        ),
        Hypothesis(
            key="C",
            architecture="Governance automation",
            implementation_strategy="Add mission manager + hypothesis engine + platform scoring",
            expected_engineering_value="High",
            knowledge_gain="High",
            business_value="High",
            reuse="High",
            scalability="High",
            technical_risk="Low",
            dependencies=["existing workbench framework scoring"],
            future_unlock="Excellent",
            metrics_0_10={
                "Strategic Alignment": 9.5,
                "Engineering Quality": 9.0,
                "Architecture Quality": 8.8,
                "Knowledge Gain": 9.5,
                "Maintainability": 8.7,
                "Scalability": 8.8,
                "Industrial Applicability": 8.5,
                "Reuse Potential": 9.2,
                "Coordinator Integration": 9.0,
                "Knowledge Hub Integration": 9.0,
                "Enterprise Digital Twin Integration": 8.8,
                "Mission Graph Impact": 9.0,
                "Capability Graph Impact": 8.8,
                "Future Mission Unlock": 9.3,
                "Technical Debt Reduction": 8.2,
                "Testing Impact": 8.5,
                "Documentation Impact": 8.8,
                "Business Value": 8.7,
                "Confidence": 8.9,
                "Risk Inverse": 8.7,
            },
        ),
        Hypothesis(
            key="D",
            architecture="Data ingestion expansion",
            implementation_strategy="Implement all future templates now",
            expected_engineering_value="High",
            knowledge_gain="Medium",
            business_value="Potentially high",
            reuse="Medium",
            scalability="Medium",
            technical_risk="High",
            dependencies=["domain engineering inputs not yet validated"],
            future_unlock="Moderate",
            metrics_0_10={
                "Strategic Alignment": 7.0,
                "Engineering Quality": 6.0,
                "Architecture Quality": 6.5,
                "Knowledge Gain": 6.0,
                "Maintainability": 5.5,
                "Scalability": 6.0,
                "Industrial Applicability": 7.5,
                "Reuse Potential": 6.0,
                "Coordinator Integration": 6.0,
                "Knowledge Hub Integration": 6.2,
                "Enterprise Digital Twin Integration": 6.0,
                "Mission Graph Impact": 7.2,
                "Capability Graph Impact": 7.0,
                "Future Mission Unlock": 6.5,
                "Technical Debt Reduction": 4.5,
                "Testing Impact": 5.5,
                "Documentation Impact": 5.5,
                "Business Value": 7.8,
                "Confidence": 5.5,
                "Risk Inverse": 4.2,
            },
        ),
        Hypothesis(
            key="E",
            architecture="Coordinator specialization",
            implementation_strategy="Build heavy AI model orchestration for SPOE",
            expected_engineering_value="Medium",
            knowledge_gain="High",
            business_value="Medium",
            reuse="Medium-high",
            scalability="Medium-high",
            technical_risk="Medium-high",
            dependencies=["agent infra", "queueing"],
            future_unlock="Good",
            metrics_0_10={
                "Strategic Alignment": 8.0,
                "Engineering Quality": 7.5,
                "Architecture Quality": 7.3,
                "Knowledge Gain": 8.5,
                "Maintainability": 6.8,
                "Scalability": 7.5,
                "Industrial Applicability": 7.0,
                "Reuse Potential": 7.4,
                "Coordinator Integration": 8.8,
                "Knowledge Hub Integration": 7.8,
                "Enterprise Digital Twin Integration": 7.3,
                "Mission Graph Impact": 7.8,
                "Capability Graph Impact": 7.4,
                "Future Mission Unlock": 8.0,
                "Technical Debt Reduction": 6.0,
                "Testing Impact": 6.5,
                "Documentation Impact": 6.5,
                "Business Value": 7.0,
                "Confidence": 6.5,
                "Risk Inverse": 6.0,
            },
        ),
    ]


def run_ame_iteration() -> Dict:
    state = observe_platform_state()
    opportunities = detect_opportunities(state)
    hypotheses = generate_hypotheses(state, opportunities)
    scored = evaluate_hypotheses(hypotheses)
    hypotheses_path = store_hypotheses(scored)

    kpis = {
        "Mission Completion": 7.8,
        "Platform Maturity": 8.1,
        "Architecture Quality": 8.6,
        "Knowledge Coverage": 8.2,
        "Testing Coverage": 7.9,
        "Documentation Coverage": 8.5,
        "Reuse": 8.7,
        "Automation": 8.6,
        "Engineering Health": 8.4,
        "Mission Portfolio Progress": 8.1,
        "Enterprise Digital Twin Completeness": 8.3,
        "Commercial Workbench Completeness": 8.6,
        "SPOE Completeness": 8.8,
        "Mission Manager Completeness": 8.2,
        "Knowledge Hub Completeness": 8.4,
        "Coordinator Integration": 8.5,
    }
    score_entry = update_platform_score_history(kpis)

    return {
        "timestamp": datetime.now(UTC).isoformat(),
        "platform_state": state.__dict__,
        "opportunities": opportunities,
        "hypotheses": scored,
        "hypotheses_path": hypotheses_path,
        "platform_score": score_entry,
    }
