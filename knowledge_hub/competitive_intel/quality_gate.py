from __future__ import annotations

from typing import List, Dict


class QualityGate:
    """Basic quality checks for generated reports.

    Evaluates hits and evidence items and returns a simple quality dict.
    """

    def evaluate_report(self, hits: List[Dict], evidence_items: List[Dict]) -> Dict:
        coverage = len(hits)
        evidence = len(evidence_items)
        diversity = len({h.get('path') for h in hits if h.get('path')}) if hits else 0
        score = min(1.0, (coverage / 5.0) * 0.4 + (evidence / 10.0) * 0.4 + (diversity / 3.0) * 0.2)
        status = 'draft'
        if score > 0.7:
            status = 'final'
        elif score > 0.4:
            status = 'incomplete'
        else:
            status = 'insufficient_evidence'

        return {'score': round(score, 2), 'status': status, 'coverage': coverage, 'evidence': evidence, 'diversity': diversity}
