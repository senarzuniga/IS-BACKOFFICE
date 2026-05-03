from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from backoffice import CommercialIntelligenceOS


@dataclass
class AgentContext:
    payload: dict[str, Any]
    result: dict[str, Any] = field(default_factory=dict)
    alerts: list[str] = field(default_factory=list)
    trace: list[str] = field(default_factory=list)


class BaseAgent:
    name = "base-agent"

    def run(self, context: AgentContext) -> None:
        context.trace.append(self.name)


class IngestionAgent(BaseAgent):
    name = "ingestion-agent"


class DataCleaningAgent(BaseAgent):
    name = "data-cleaning-agent"


class ExtractionAgent(BaseAgent):
    name = "extraction-agent"


class KnowledgeGraphAgent(BaseAgent):
    name = "knowledge-graph-agent"


class AnalyticsAgent(BaseAgent):
    name = "analytics-agent"


class ForecastAgent(BaseAgent):
    name = "forecast-agent"


class AnomalyAgent(BaseAgent):
    name = "anomaly-agent"

    def run(self, context: AgentContext) -> None:
        super().run(context)
        anomalies = context.result.get("analytics", {}).get("offer_validation", {}).get("anomalies", [])
        if anomalies:
            context.alerts.append(f"Pricing anomalies detected: {len(anomalies)}")


class ReportAgent(BaseAgent):
    name = "report-agent"


class ReviewAgent(BaseAgent):
    name = "review-agent"

    def run(self, context: AgentContext) -> None:
        super().run(context)
        signals = context.result.get("proactive_signals", [])
        for signal in signals:
            context.alerts.append(f"Action required: {signal}")


class MultiAgentOrchestrator:
    def __init__(self) -> None:
        self.osys = CommercialIntelligenceOS()
        self.agents: list[BaseAgent] = [
            IngestionAgent(),
            DataCleaningAgent(),
            ExtractionAgent(),
            KnowledgeGraphAgent(),
            AnalyticsAgent(),
            ForecastAgent(),
            AnomalyAgent(),
            ReportAgent(),
            ReviewAgent(),
        ]

    def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        context = AgentContext(payload=payload)

        source_type = payload.get("source_type", "txt")
        source_id = payload.get("source_id", "agent-001")
        content = payload.get("content", "")
        classification = payload.get("classification")
        proactive_mode = bool(payload.get("proactive_mode", True))
        autolearning_mode = bool(payload.get("autolearning_mode", True))
        strict_mode = bool(payload.get("strict_mode", False))

        metadata: dict[str, str] = {}
        if classification:
            metadata["classification"] = classification

        record = self.osys.ingestion.ingest_record(
            source_type=source_type,
            source_id=source_id,
            content=content,
            **metadata,
        )
        context.result = self.osys.run_cycle(
            [record],
            proactive_mode=proactive_mode,
            autolearning_mode=autolearning_mode,
            strict_mode=strict_mode,
        )

        for agent in self.agents:
            agent.run(context)

        return {
            "status": context.result.get("status", "ok"),
            "pipeline": context.trace,
            "result": context.result,
            "alerts": sorted(set(context.alerts)),
        }
