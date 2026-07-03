from __future__ import annotations

from typing import List, Dict
from .competitor_report_generator import CompetitorReportGenerator


class CompetitiveBriefGenerator:
    def __init__(self, base_generator: CompetitorReportGenerator):
        self.base = base_generator

    def generate(self, company: str, competitor: str) -> Dict:
        # simple wrapper that runs a short scan and formats a brief
        report = self.base.generate(company, competitor, query=f"{competitor} strategic overview")
        brief = {
            'title': f'Competitive Brief: {competitor} (for {company})',
            'executive_summary': report['findings'][:3],
            'key_evidence': report['evidence'][:4],
            'quality': report['quality']
        }
        return brief
