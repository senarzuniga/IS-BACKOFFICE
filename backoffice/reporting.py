from __future__ import annotations

from .models import RawRecord


class OutputReportingEngine:
    def generate(self, analytics: dict, records: list[RawRecord]) -> dict:
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
                    "forecast": analytics["forecasting"],
                    "pipeline": analytics["sales_intelligence"]["pipeline_analysis"],
                },
                "insight_summary": analytics,
            },
            "client_diagnostics": analytics["key_account_intelligence"],
            "sales_performance": analytics["sales_intelligence"],
            "strategic_opportunities": analytics["key_account_intelligence"]["opportunity_detection"],
            "automated_presentation": [
                "Current pipeline and forecast",
                "Key account health and opportunities",
                "Offer anomalies and actions",
            ],
            "traceability": traceability,
        }
