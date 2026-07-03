from __future__ import annotations

from typing import List, Dict
from .hybrid_retrieval import HybridRetrieval
from .citation_builder import CitationBuilder
from .evidence_store import EvidenceStore
from .quality_gate import QualityGate


class CompetitorReportGenerator:
    def __init__(self, retriever: HybridRetrieval, citations: CitationBuilder, evidence: EvidenceStore, gate: QualityGate):
        self.retriever = retriever
        self.citations = citations
        self.evidence = evidence
        self.gate = gate

    def generate(self, company: str, competitor: str, query: str) -> Dict:
        hits = self.retriever.keyword_search(company, query, limit=8)
        evs = []
        for h in hits:
            # attempt to find evidence by doc path or file name
            evs.extend(self.evidence.query_recent(20))

        citations = self.citations.build_citations(evs[:6])

        report = {
            'company': company,
            'competitor': competitor,
            'query': query,
            'findings': [h['summary'] for h in hits],
            'evidence': citations,
            'quality': self.gate.evaluate_report(hits, evs)
        }
        return report
