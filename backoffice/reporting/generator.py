"""Report generation — produces JSON, text, and HTML reports."""
from __future__ import annotations
import json
from datetime import datetime, timezone
from typing import Any, Dict

from backoffice.graph.store import GraphStore
from backoffice.analytics.pipeline_scoring import PipelineScorer
from backoffice.analytics.forecasting import Forecaster
from backoffice.analytics.account_health import AccountHealthScorer
from backoffice.analytics.offer_validation import OfferValidator
from backoffice.analytics.portfolio import PortfolioAnalyzer


class ReportGenerator:
    """Generates business intelligence reports from the analytics engines."""

    def __init__(self, store: GraphStore):
        self._store = store
        self._pipeline = PipelineScorer(store)
        self._forecaster = Forecaster(store)
        self._health = AccountHealthScorer(store)
        self._offer_val = OfferValidator(store)
        self._portfolio = PortfolioAnalyzer(store)

    def executive_summary(self) -> Dict[str, Any]:
        """Executive dashboard report."""
        return {
            "report_type": "executive_summary",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "graph_stats": self._store.stats(),
            "pipeline": self._pipeline.pipeline_summary(),
            "forecast": self._forecaster.forecast_next_period(periods=3),
            "conversion": self._forecaster.conversion_probability(),
            "top_accounts": self._health.score_all_clients()[:5],
            "portfolio": self._portfolio.classify_products(),
            "offer_anomalies": [
                r for r in self._offer_val.validate_all_offers() if not r.get("is_valid")
            ],
        }

    def client_diagnostic(self, client_id: str) -> Dict[str, Any]:
        """Detailed diagnostic report for a single client."""
        health = self._health.score_client(client_id)
        timeline = self._store.get_client_timeline(client_id)
        offers_validation = [
            self._offer_val.validate_offer(o["id"])
            for o in timeline.get("offers", [])
        ]
        return {
            "report_type": "client_diagnostic",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "health": health,
            "timeline": timeline,
            "offer_validations": offers_validation,
        }

    def sales_performance(self) -> Dict[str, Any]:
        """Sales performance report."""
        monthly = self._forecaster.monthly_revenue()
        return {
            "report_type": "sales_performance",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "monthly_revenue": monthly,
            "pipeline": self._pipeline.pipeline_summary(),
            "account_scores": self._health.score_all_clients(),
        }

    def to_json(self, report: Dict[str, Any], indent: int = 2) -> str:
        return json.dumps(report, indent=indent, default=str)

    def to_html(self, report: Dict[str, Any]) -> str:
        title = report.get("report_type", "Report").replace("_", " ").title()
        generated = report.get("generated_at", "")
        rows = ""
        for key, val in report.items():
            if key in ("report_type", "generated_at"):
                continue
            rows += f"<tr><td><strong>{key}</strong></td><td><pre>{json.dumps(val, indent=2, default=str)}</pre></td></tr>"
        return f"""<!DOCTYPE html>
<html><head><title>{title}</title>
<style>body{{font-family:Arial,sans-serif;padding:20px}}
table{{border-collapse:collapse;width:100%}}
td{{border:1px solid #ccc;padding:8px;vertical-align:top}}
pre{{white-space:pre-wrap;font-size:12px}}</style>
</head><body>
<h1>{title}</h1><p>Generated: {generated}</p>
<table>{rows}</table>
</body></html>"""
