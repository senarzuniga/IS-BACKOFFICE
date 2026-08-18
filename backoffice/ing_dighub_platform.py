from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional

from backoffice.integrations.ai_factory_client import AIFactoryClient


@dataclass(frozen=True)
class ModuleSpec:
    key: str
    name: str
    service: str
    description: str


MODULE_SPECS: List[ModuleSpec] = [
    ModuleSpec("industrial_knowledge_hub", "Industrial Knowledge Hub", "industrial-knowledge-hub", "Industrial know-how retrieval and contextualization"),
    ModuleSpec("enterprise_digital_twin", "Enterprise Digital Twin", "enterprise-digital-twin", "Twin state, capability map, and plant observability"),
    ModuleSpec("mission_manager_ui", "Mission Manager UI", "mission-manager-ui", "Mission coordination and execution control"),
    ModuleSpec("engineering_workbench", "Engineering Workbench", "engineering-workbench", "Cross-domain engineering workflows and decisions"),
    ModuleSpec("layout_analysis_workbench", "Layout Analysis Workbench", "layout-analysis-workbench", "Plant layout analysis and optimization"),
    ModuleSpec("simulation_center", "Simulation Center", "simulation-center", "Simulation launch, tracking, and comparative analysis"),
    ModuleSpec("industrial_knowledge_graph", "Industrial Knowledge Graph", "industrial-knowledge-graph", "Industrial entities, relations, and reasoning graph"),
    ModuleSpec("spoe", "SPOE", "spoe", "Standard Product Offer Engine capabilities"),
    ModuleSpec("offer_generator", "Offer Generator", "offer-generator", "Commercial offer generation from engineering context"),
    ModuleSpec("executive_dashboards", "Executive Dashboards", "executive-dashboards", "KPI and executive-level decision dashboards"),
    ModuleSpec("technical_documentation", "Technical Documentation", "technical-documentation", "Technical artifact generation and maintenance"),
    ModuleSpec("industrial_intelligence", "Industrial Intelligence", "industrial-intelligence", "Industrial signals, insights, and recommendations"),
    ModuleSpec("rd_funding", "CTA Industrial R&D Funding Engine", "rd-funding", "Evidence-governed industrial R&D qualification, funding matching, and application missions"),
]


class IngDighubPlatformService:
    """Integration layer delegating module intelligence and mission loops to AI-FACTORY APIs."""

    def __init__(self, ai_factory: Optional[AIFactoryClient] = None):
        self.ai_factory = ai_factory or AIFactoryClient()
        self.module_map = {m.key: m for m in MODULE_SPECS}
        self.service_template = os.environ.get(
            "AI_FACTORY_SERVICE_EXECUTE_TEMPLATE",
            "/api/v1/services/{service}/execute",
        )
        self.autonomy_step_endpoint = os.environ.get(
            "AI_FACTORY_AUTONOMY_STEP_ENDPOINT",
            "/api/v1/cognitive-loop/step",
        )
        self.hypothesis_endpoint = os.environ.get(
            "AI_FACTORY_HYPOTHESIS_ENDPOINT",
            "/api/v1/hypotheses/generate",
        )
        self.score_endpoint = os.environ.get(
            "AI_FACTORY_SCORE_ENDPOINT",
            "/api/v1/hypotheses/score",
        )
        self.select_endpoint = os.environ.get(
            "AI_FACTORY_SELECT_ENDPOINT",
            "/api/v1/hypotheses/select",
        )
        self.validate_endpoint = os.environ.get(
            "AI_FACTORY_VALIDATE_ENDPOINT",
            "/api/v1/hypotheses/validate",
        )

    def list_modules(self) -> List[Dict[str, Any]]:
        return [asdict(spec) for spec in MODULE_SPECS]

    def execute_module(self, module_key: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        spec = self.module_map.get(module_key)
        if spec is None:
            return {"status": "error", "error": "unknown_module", "module_key": module_key}

        payload = {
            "module": asdict(spec),
            "context": context or {},
            "platform": "ING_DIGHUB",
        }
        endpoint = self.service_template.format(service=spec.service)
        result = self.ai_factory.post_json(endpoint, payload)
        return {
            "status": result.get("status", "ok"),
            "module": asdict(spec),
            "endpoint": endpoint,
            "ai_factory": result,
        }

    def run_autonomy_loop(
        self,
        mission: str,
        *,
        context: Optional[Dict[str, Any]] = None,
        max_iterations: int = 8,
        min_expected_value: float = 0.0,
    ) -> Dict[str, Any]:
        runtime_context: Dict[str, Any] = dict(context or {})
        history: List[Dict[str, Any]] = []

        for iteration in range(1, max_iterations + 1):
            step = self._run_ai_factory_step(mission, iteration, runtime_context, min_expected_value)
            expected_value = self._extract_expected_value(step)
            accepted = self._extract_accepted(step)

            history.append(
                {
                    "iteration": iteration,
                    "step": step,
                    "selected_expected_value": expected_value,
                    "validated": accepted,
                }
            )

            if expected_value <= min_expected_value:
                return {
                    "status": "completed",
                    "mission": mission,
                    "iterations_completed": iteration,
                    "stop_reason": "no_positive_expected_value",
                    "history": history,
                }

            if not accepted:
                return {
                    "status": "completed",
                    "mission": mission,
                    "iterations_completed": iteration,
                    "stop_reason": "validation_rejected",
                    "history": history,
                }

            runtime_context.update(self._extract_context_delta(step))

        return {
            "status": "completed",
            "mission": mission,
            "iterations_completed": max_iterations,
            "stop_reason": "max_iterations_reached",
            "history": history,
        }

    def _run_ai_factory_step(
        self,
        mission: str,
        iteration: int,
        context: Dict[str, Any],
        min_expected_value: float,
    ) -> Dict[str, Any]:
        payload = {
            "mission": mission,
            "iteration": iteration,
            "context": context,
            "min_expected_value": min_expected_value,
            "platform": "ING_DIGHUB",
        }

        step = self.ai_factory.post_json(self.autonomy_step_endpoint, payload)
        if step.get("status") not in {"unavailable", "error"}:
            return step

        hypotheses = self.ai_factory.post_json(self.hypothesis_endpoint, payload)
        scored = self.ai_factory.post_json(self.score_endpoint, {**payload, "hypotheses": hypotheses})
        selected = self.ai_factory.post_json(self.select_endpoint, {**payload, "scored": scored})
        validated = self.ai_factory.post_json(self.validate_endpoint, {**payload, "selected": selected})

        return {
            "mode": "fallback_pipeline",
            "hypotheses": hypotheses,
            "scored": scored,
            "selected": selected,
            "validation": validated,
            "status": validated.get("status", "ok"),
        }

    @staticmethod
    def _extract_expected_value(step: Dict[str, Any]) -> float:
        candidates = [
            step.get("selected", {}),
            step.get("selection", {}),
            step.get("selected_hypothesis", {}),
            step.get("validation", {}).get("selected", {}) if isinstance(step.get("validation"), dict) else {},
        ]

        for candidate in candidates:
            if not isinstance(candidate, dict):
                continue
            if "expected_value" in candidate:
                try:
                    return float(candidate["expected_value"])
                except (TypeError, ValueError):
                    continue
            if "expected_delta" in candidate:
                try:
                    return float(candidate["expected_delta"])
                except (TypeError, ValueError):
                    continue

        return 0.0

    @staticmethod
    def _extract_accepted(step: Dict[str, Any]) -> bool:
        validation = step.get("validation")
        if isinstance(validation, dict):
            if "accepted" in validation:
                return bool(validation["accepted"])
            if "is_valid" in validation:
                return bool(validation["is_valid"])
        return True

    @staticmethod
    def _extract_context_delta(step: Dict[str, Any]) -> Dict[str, Any]:
        keys = ["context_delta", "next_context", "state_delta"]
        for key in keys:
            value = step.get(key)
            if isinstance(value, dict):
                return value

        validation = step.get("validation")
        if isinstance(validation, dict):
            for key in keys:
                value = validation.get(key)
                if isinstance(value, dict):
                    return value

        return {}
