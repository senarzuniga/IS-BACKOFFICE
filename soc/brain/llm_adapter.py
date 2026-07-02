from __future__ import annotations

from typing import Dict, List
import random


class MockLLMAdapter:
    """Mock LLM adapter to synthesize structured responses from evidence.

    This adapter intentionally does NOT call external services and is
    used for development and unit testing. Replace with a production
    adapter that funnels all calls through a controlled orchestrator.
    """

    def generate(self, prompt: str, evidence: List[Dict]) -> Dict:
        # produce a deterministic-ish mock response using evidence
        top_evidence = evidence[0:3]
        summary = ' '.join([e.get('snippet', '')[:200] for e in top_evidence]).strip()
        confidence = round(min(0.99, 0.5 + 0.1 * len(top_evidence) + random.uniform(-0.05, 0.05)), 2)

        findings = []
        for e in top_evidence:
            findings.append(f"From {e.get('title')}: { (e.get('snippet') or '')[:120] }")

        risks = ["Operational capacity may limit scaling."]
        opportunities = ["Pilot subscription service for key accounts."]
        recommendations = ["Prioritize repeatable service productization and KPI capture."]

        return {
            'executive_summary': (summary or 'No strong evidence found.')[:1000],
            'key_findings': findings,
            'evidence_used': [e.get('doc_uuid') for e in top_evidence],
            'risks': risks,
            'opportunities': opportunities,
            'recommendations': recommendations,
            'confidence': confidence,
            'missing_information': [],
        }
