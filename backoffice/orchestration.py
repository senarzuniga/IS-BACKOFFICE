from __future__ import annotations

from typing import Any

from .analytics import AIAnalyticsEngine
from .extraction.structuring import EntityExtractionStructuringEngine
from .runtime_components import DataIngestionLayer
from .runtime_components import KnowledgeGraphMemorySystem
from .runtime_components import DataProcessingCleaningLayer
from .runtime_components import OutputReportingEngine


class CommercialIntelligenceOS:
    def __init__(self) -> None:
        self.ingestion = DataIngestionLayer()
        self.processing = DataProcessingCleaningLayer()
        self.extraction = EntityExtractionStructuringEngine()
        self.memory = KnowledgeGraphMemorySystem()
        self.analytics = AIAnalyticsEngine()
        self.reporting = OutputReportingEngine()

    def run_cycle(
        self,
        raw_records: list,
        *,
        proactive_mode: bool = True,
        autolearning_mode: bool = True,
        strict_mode: bool = False,
    ) -> dict:
        try:
            processed = self.processing.process(raw_records)
            entities = self.extraction.extract(processed.cleaned_records)
            self.memory.upsert_entities(entities)
            analytics = self.analytics.analyze(entities)
            outputs = self.reporting.generate(analytics, processed.cleaned_records)
        except Exception as exc:
            if strict_mode:
                raise
            return {
                "status": "degraded",
                "error": str(exc),
                "processing": {
                    "dropped_duplicates": 0,
                    "missing_fields": [],
                    "validation_errors": [str(exc)],
                },
                "entities": None,
                "knowledge_graph_nodes": len(self.memory.nodes),
                "knowledge_graph_edges": sum(len(v) for v in self.memory.edges.values()),
                "analytics": {},
                "outputs": {},
                "learning_feedback": list(self.memory.learned_signals),
                "proactive_signals": [],
                "reliability": {
                    "processed_records": 0,
                    "dropped_duplicates": 0,
                    "missing_fields": 0,
                    "validation_errors": 1,
                },
            }

        proactive_signals = self._build_proactive_signals(analytics, outputs, processed)
        if not proactive_mode:
            proactive_signals = []

        if autolearning_mode:
            for insight in outputs.get("strategic_opportunities", []):
                self.memory.feed_learning(insight)
            for signal in proactive_signals:
                self.memory.feed_learning(f"proactive:{signal}")

        reliability = {
            "processed_records": len(processed.cleaned_records),
            "dropped_duplicates": processed.dropped_duplicates,
            "missing_fields": len(processed.missing_fields),
            "validation_errors": len(processed.validation_errors),
        }

        return {
            "status": "ok",
            "processing": {
                "dropped_duplicates": processed.dropped_duplicates,
                "missing_fields": processed.missing_fields,
                "validation_errors": processed.validation_errors,
            },
            "entities": entities,
            "knowledge_graph_nodes": len(self.memory.nodes),
            "knowledge_graph_edges": sum(len(v) for v in self.memory.edges.values()),
            "analytics": analytics,
            "outputs": outputs,
            "learning_feedback": list(self.memory.learned_signals),
            "proactive_signals": proactive_signals,
            "reliability": reliability,
            "modes": {
                "proactive_mode": proactive_mode,
                "autolearning_mode": autolearning_mode,
                "strict_mode": strict_mode,
            },
        }

    @staticmethod
    def _build_proactive_signals(analytics: dict[str, Any], outputs: dict[str, Any], processed: Any) -> list[str]:
        signals: list[str] = []
        sales = analytics.get("sales_intelligence", {})
        forecasting = analytics.get("forecasting", {})
        offer_validation = analytics.get("offer_validation", {})

        pipeline_value = float(sales.get("pipeline_analysis", 0) or 0)
        probability = float(sales.get("deal_probability", 0) or 0)
        forecast = float(forecasting.get("revenue_forecast", 0) or 0)
        anomalies = offer_validation.get("anomalies", [])

        if pipeline_value > 0 and probability < 0.25:
            signals.append("Low close probability despite active pipeline")
        if forecast == 0 and pipeline_value > 0:
            signals.append("Revenue forecast is zero while pipeline is active")
        if anomalies:
            signals.append(f"Detected {len(anomalies)} offer anomalies requiring validation")
        if processed.missing_fields:
            signals.append(f"Detected {len(processed.missing_fields)} records with missing fields")
        if processed.validation_errors:
            signals.append(f"Detected {len(processed.validation_errors)} processing validation errors")
        if not outputs.get("strategic_opportunities"):
            signals.append("No strategic opportunities detected in this cycle")

        return signals
