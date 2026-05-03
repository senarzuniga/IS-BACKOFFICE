from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class RuntimeRecord:
    source_type: str
    content: str
    source_id: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    client_reference: str | None = None
    classification: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class DataIngestionLayer:
    SUPPORTED = {
        "outlook_email",
        "pdf",
        "word",
        "excel",
        "txt",
        "folder_scan",
        "crm",
    }

    def ingest_record(self, source_type: str, content: str, source_id: str, **metadata: str) -> RuntimeRecord:
        if source_type not in self.SUPPORTED:
            raise ValueError(f"Unsupported source type: {source_type}")
        return RuntimeRecord(
            source_type=source_type,
            content=(content or "").strip(),
            source_id=source_id,
            client_reference=metadata.get("client_reference"),
            classification=metadata.get("classification"),
            metadata=metadata,
        )


class DataProcessingCleaningLayer:
    CURRENCY_MAP = {"usd": "USD", "$": "USD", "eur": "EUR", "€": "EUR"}

    def process(self, records: list[RuntimeRecord]) -> Any:
        seen = set()
        cleaned: list[RuntimeRecord] = []
        dropped = 0
        missing_fields: list[str] = []
        validation_errors: list[str] = []

        for record in records:
            key = (record.source_id, record.content.lower())
            if key in seen:
                dropped += 1
                continue
            seen.add(key)

            if not record.content:
                missing_fields.append(f"empty_content:{record.source_id}")
                continue

            normalized = " ".join(record.content.split())
            normalized = normalized.replace("US$", "USD ").replace("usd", "USD")
            normalized = normalized.replace("eur", "EUR")
            for k, v in self.CURRENCY_MAP.items():
                normalized = normalized.replace(f" {k} ", f" {v} ")

            if "value=" in normalized.lower():
                frag = normalized.lower().split("value=", 1)[1].split()[0].rstrip(",.;")
                try:
                    float(frag)
                except ValueError as exc:
                    validation_errors.append(f"invalid_value:{record.source_id}:{frag}")
                    raise ValueError(f"Invalid numeric value for record {record.source_id}: {frag}") from exc

            record.content = normalized
            cleaned.append(record)

        return type(
            "ProcessingResult",
            (),
            {
                "cleaned_records": cleaned,
                "dropped_duplicates": dropped,
                "missing_fields": missing_fields,
                "validation_errors": validation_errors,
            },
        )()


class KnowledgeGraphMemorySystem:
    def __init__(self) -> None:
        self.nodes: dict[str, dict] = {}
        self.edges: dict[str, set[str]] = defaultdict(set)
        self.timeline: dict[str, list[str]] = defaultdict(list)
        self.learned_signals: list[str] = []

    def upsert_entities(self, bundle: Any) -> None:
        for customer in bundle.customers:
            self.nodes[customer.id] = {"type": "customer", "name": customer.name, "contacts": customer.contacts}

        customer_by_name = {v["name"]: k for k, v in self.nodes.items() if v.get("type") == "customer"}

        for offer in bundle.offers:
            self.nodes[offer.id] = {"type": "offer", "client": offer.client, "price": offer.price, "description": offer.description}
            c_id = customer_by_name.get(offer.client)
            if c_id:
                self.edges[c_id].add(offer.id)
                self.timeline[offer.client].append(f"offer:{offer.id}:{offer.date or 'unknown'}")

        for sale in bundle.sales:
            self.nodes[sale.id] = {"type": "sale", "client": sale.client, "value": sale.value, "product": sale.product}
            c_id = customer_by_name.get(sale.client)
            if c_id:
                self.edges[c_id].add(sale.id)
                self.timeline[sale.client].append(f"sale:{sale.id}:{sale.date or 'unknown'}")

        for opp in bundle.opportunities:
            self.nodes[opp.id] = {
                "type": "opportunity",
                "client": opp.client,
                "amount": opp.amount,
                "description": opp.description,
                "close_date": opp.close_date,
            }
            c_id = customer_by_name.get(opp.client)
            if c_id:
                self.edges[c_id].add(opp.id)
                self.timeline[opp.client].append(f"opportunity:{opp.id}:{opp.close_date or 'unknown'}")

    def feed_learning(self, signal: str) -> None:
        if signal and signal not in self.learned_signals:
            self.learned_signals.append(signal)


class OutputReportingEngine:
    def generate(self, analytics: dict, records: list[RuntimeRecord]) -> dict:
        sales = analytics.get("sales_intelligence", {})
        forecasting = analytics.get("forecasting", {})
        account = analytics.get("key_account_intelligence", {})

        traceability = [
            {
                "source_id": r.source_id,
                "source_type": r.source_type,
                "timestamp": r.timestamp,
                "classification": r.classification,
            }
            for r in records
        ]

        return {
            "executive_report": {
                "summary": {
                    "forecast": forecasting,
                    "pipeline": sales.get("pipeline_analysis", 0),
                },
                "insight_summary": analytics,
            },
            "client_diagnostics": account,
            "sales_performance": sales,
            "strategic_opportunities": account.get("opportunity_detection", []),
            "automated_presentation": [
                "Current pipeline and forecast",
                "Key account health and opportunities",
                "Offer anomalies and actions",
            ],
            "operational_reliability": {
                "records_processed": len(records),
                "traceability_complete": all(r.source_id and r.timestamp for r in records),
            },
            "traceability": traceability,
        }
