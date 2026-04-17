from __future__ import annotations

from .analytics import AIAnalyticsEngine
from .extraction import EntityExtractionStructuringEngine
from .ingestion import DataIngestionLayer
from .knowledge_graph import KnowledgeGraphMemorySystem
from .processing import DataProcessingCleaningLayer
from .reporting import OutputReportingEngine


class CommercialIntelligenceOS:
    def __init__(self) -> None:
        self.ingestion = DataIngestionLayer()
        self.processing = DataProcessingCleaningLayer()
        self.extraction = EntityExtractionStructuringEngine()
        self.memory = KnowledgeGraphMemorySystem()
        self.analytics = AIAnalyticsEngine()
        self.reporting = OutputReportingEngine()

    def run_cycle(self, raw_records: list) -> dict:
        processed = self.processing.process(raw_records)
        entities = self.extraction.extract(processed.cleaned_records)
        self.memory.upsert_entities(entities)
        analytics = self.analytics.analyze(entities)
        outputs = self.reporting.generate(analytics, processed.cleaned_records)

        for insight in outputs["strategic_opportunities"]:
            self.memory.feed_learning(insight)

        return {
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
        }
