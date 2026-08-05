from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from backoffice.pie.hypothesis_engine import resolve_uncertainty
from backoffice.pie.models import Hypothesis


@dataclass
class VisualRecognitionResult:
    component_kind: str
    confidence: float
    semantic_fidelity: float
    visual_fidelity: float
    structural_fidelity: float
    labels: list[str]
    props: dict[str, Any]
    selected_hypothesis: str


class DiagramRecognitionEngine:
    def recognize(self, slide: Any) -> VisualRecognitionResult:
        tokens = self._slide_tokens(slide)
        candidates = self._candidates(slide, tokens)
        decision = resolve_uncertainty(f"diagram-type:{getattr(slide, 'index', 'unknown')}", candidates)
        top = next(candidate for candidate in candidates if candidate.key == decision.selected_hypothesis.key)
        component_kind, labels, props = self._decode(top.key, slide, tokens)
        return VisualRecognitionResult(
            component_kind=component_kind,
            confidence=top.confidence,
            semantic_fidelity=round(top.impact, 2),
            visual_fidelity=round(top.risk_inverse, 2),
            structural_fidelity=round(top.effort, 2),
            labels=labels,
            props=props,
            selected_hypothesis=top.key,
        )

    def _slide_tokens(self, slide: Any) -> set[str]:
        text = [getattr(slide, "title", "")]
        for element in getattr(slide, "elements", []):
            if getattr(element, "text", ""):
                text.append(element.text)
            text.append(getattr(element, "kind", ""))
        normalized = " ".join(text).lower()
        return {token.strip(".,:;()[]{}") for token in normalized.replace("\n", " ").split() if token.strip()}

    def _candidates(self, slide: Any, tokens: set[str]) -> list[Hypothesis]:
        elements = getattr(slide, "elements", [])
        element_count = len(elements)
        text_count = sum(1 for element in elements if getattr(element, "text", "").strip())
        table_count = sum(1 for element in elements if getattr(element, "table_rows", []))
        chart_count = sum(1 for element in elements if getattr(element, "chart", {}))
        width = float(getattr(slide, "width", 1.0) or 1.0)
        height = float(getattr(slide, "height", 1.0) or 1.0)
        landscape_bias = 1.0 if width >= height else 0.0

        def has_any(*needles: str) -> bool:
            return any(needle in tokens for needle in needles)

        def score(base: float, bump: float = 0.0) -> float:
            return max(0.0, min(10.0, base + bump))

        return [
            Hypothesis("timeline", "Linear milestones/timeline reconstruction", score(5.8, 2.2 if has_any("timeline", "roadmap", "milestone", "phase", "schedule") else 0.0), score(6.2, 2.0 if has_any("timeline", "milestone", "phase") else 0.0), score(7.8, 1.0 if element_count > 3 else 0.0), score(8.0, landscape_bias), "Timeline-oriented labels and sequential blocks detected."),
            Hypothesis("gantt", "Gantt timeline with spans", score(5.7, 2.4 if has_any("gantt", "schedule", "duration", "task") else 0.0), score(6.0, 2.3 if has_any("gantt", "task") else 0.0), score(7.2, 1.2 if table_count > 0 else 0.0), score(7.5, landscape_bias), "Tabular schedule semantics detected."),
            Hypothesis("process_flow", "Chevron-based process flow", score(6.2, 2.0 if has_any("process", "flow", "workflow", "step") else 0.0), score(6.4, 1.8 if text_count >= 3 else 0.0), score(8.4, 0.8 if landscape_bias else 0.0), score(8.0, 0.5 if element_count >= 4 else 0.0), "Sequential process hints detected."),
            Hypothesis("sipoc", "SIPOC table-style reconstruction", score(5.4, 2.8 if has_any("supplier", "input", "process", "output", "customer", "sipoc") else 0.0), score(6.5, 2.4 if table_count > 0 else 0.0), score(8.0, 1.0 if table_count > 0 else 0.0), score(7.6, 0.5 if text_count >= 5 else 0.0), "SIPOC vocabulary or table structure detected."),
            Hypothesis("bpmn_simplified", "BPMN-like simplified process diagram", score(5.5, 2.5 if has_any("bpmn", "gateway", "task", "start", "end", "event") else 0.0), score(6.3, 1.8 if has_any("gateway", "event") else 0.0), score(7.3, 1.0 if element_count > 5 else 0.0), score(7.2, 0.6 if landscape_bias else 0.0), "Event/task flow semantics detected."),
            Hypothesis("swimlane", "Swimlane role/process diagram", score(5.3, 2.7 if has_any("lane", "role", "owner", "department", "swimlane") else 0.0), score(6.0, 2.0 if has_any("role", "department") else 0.0), score(7.5, 1.0 if element_count > 6 else 0.0), score(7.3, landscape_bias), "Role-based lanes inferred from labels and wide layout."),
            Hypothesis("matrix", "Quadrant or decision matrix", score(5.9, 2.2 if has_any("matrix", "impact", "effort", "risk", "priority") else 0.0), score(6.2, 1.8 if table_count > 0 else 0.0), score(8.0, 1.0 if element_count >= 4 else 0.0), score(7.8, 0.6 if has_any("quadrant") else 0.0), "Matrix semantics or quadrant language detected."),
            Hypothesis("hierarchy", "Hierarchy or org-chart tree", score(5.8, 2.6 if has_any("hierarchy", "organization", "org", "manager", "team") else 0.0), score(6.0, 1.9 if text_count >= 4 else 0.0), score(7.8, 1.0 if element_count >= 4 else 0.0), score(7.6, 0.8 if has_any("org") else 0.0), "Tree-like organizational structure inferred."),
            Hypothesis("relationship", "Hub-and-spoke relationship map", score(5.6, 2.4 if has_any("relationship", "ecosystem", "network", "platform") else 0.0), score(6.1, 2.0 if element_count >= 5 else 0.0), score(7.5, 0.8 if landscape_bias else 0.0), score(7.9, 0.8 if has_any("ecosystem") else 0.0), "Central concept plus surrounding entities inferred."),
            Hypothesis("cycle", "Circular/cycle diagram", score(5.8, 2.5 if has_any("cycle", "loop", "continuous", "feedback") else 0.0), score(6.2, 1.8 if text_count >= 3 else 0.0), score(7.9, 0.8 if element_count >= 3 else 0.0), score(7.5, 0.8 if has_any("continuous") else 0.0), "Closed-loop semantics detected."),
            Hypothesis("venn", "Venn overlap diagram", score(5.0, 3.0 if has_any("venn", "overlap", "intersection") else 0.0), score(6.0, 2.2 if has_any("intersection") else 0.0), score(7.0, 0.6 if element_count >= 3 else 0.0), score(7.0, 0.6 if chart_count > 0 else 0.0), "Overlap/intersection semantics detected."),
            Hypothesis("pyramid", "Layered pyramid maturity diagram", score(5.9, 2.3 if has_any("pyramid", "maturity", "layer", "tier") else 0.0), score(6.0, 1.8 if text_count >= 3 else 0.0), score(7.9, 0.8 if element_count >= 3 else 0.0), score(7.6, 0.8 if has_any("maturity") else 0.0), "Layer-based maturity hierarchy inferred."),
            Hypothesis("plant_layout", "Factory/plant layout reconstruction", score(5.4, 2.7 if has_any("layout", "plant", "warehouse", "line", "factory") else 0.0), score(6.2, 1.8 if has_any("warehouse", "factory") else 0.0), score(7.6, 1.0 if element_count > 6 else 0.0), score(7.4, landscape_bias), "Spatial layout semantics inferred."),
            Hypothesis("electrical_diagram", "Electrical wiring/block diagram", score(5.0, 3.0 if has_any("electrical", "sensor", "io", "plc", "motor", "relay") else 0.0), score(6.4, 2.0 if has_any("plc", "sensor") else 0.0), score(7.0, 0.8 if element_count > 5 else 0.0), score(7.2, 0.5 if chart_count > 0 else 0.0), "Electrical/control-system terms detected."),
            Hypothesis("mechanical_diagram", "Mechanical assembly/exploded view reconstruction", score(5.1, 2.8 if has_any("bearing", "shaft", "frame", "mechanical", "assembly") else 0.0), score(6.2, 1.8 if has_any("mechanical", "assembly") else 0.0), score(7.0, 0.8 if element_count > 5 else 0.0), score(7.1, 0.5 if landscape_bias else 0.0), "Mechanical assembly semantics detected."),
            Hypothesis("material_flow_diagram", "Material flow diagram", score(5.8, 2.5 if has_any("material", "flow", "logistics", "supply", "return", "reel") else 0.0), score(6.5, 2.0 if has_any("logistics", "supply", "return") else 0.0), score(7.8, 0.8 if element_count > 4 else 0.0), score(7.9, 0.6 if landscape_bias else 0.0), "Material movement semantics detected."),
            Hypothesis("table", "Executive table or tabular comparison", score(5.7, 2.2 if table_count > 0 or has_any("table", "comparison", "specification") else 0.0), score(6.3, 2.0 if table_count > 0 else 0.0), score(8.5, 0.5 if table_count > 0 else 0.0), score(8.2, 0.2 if text_count > 4 else 0.0), "Native table data detected."),
        ]

    def _decode(self, key: str, slide: Any, tokens: set[str]) -> tuple[str, list[str], dict[str, Any]]:
        items = []
        for element in getattr(slide, "elements", []):
            if getattr(element, "text", "").strip():
                items.append({"title": getattr(element, "kind", "item").title(), "body": element.text.strip()})
        labels = sorted(token for token in tokens if len(token) > 2)[:12]
        props = {
            "layout": getattr(slide, "layout", "single-column"),
            "item_count": len(items),
            "items": items[:12],
            "source_title": getattr(slide, "title", ""),
        }
        return key, labels, props