from __future__ import annotations

from .models import RawRecord


class OutputReportingEngine:
    def generate(self, analytics: dict, records: list[RawRecord]) -> dict:
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
