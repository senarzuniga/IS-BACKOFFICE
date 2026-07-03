from __future__ import annotations

from typing import List, Dict
from .hybrid_retrieval import HybridRetrieval
from .citation_builder import CitationBuilder
from .evidence_store import EvidenceStore
from .quality_gate import QualityGate


class MarketWatchReportGenerator:
    def __init__(self, retriever: HybridRetrieval, citations: CitationBuilder, evidence: EvidenceStore, gate: QualityGate):
        self.retriever = retriever
        self.citations = citations
        self.evidence = evidence
        self.gate = gate

    def generate(self, company: str, topic: str) -> Dict:
        hits = self.retriever.keyword_search(company, topic, limit=12)
        evs = self.evidence.query_recent(50)
        citations = self.citations.build_citations(evs[:8])
        report = {
            'company': company,
            'topic': topic,
            'trends': [h['summary'] for h in hits],
            'evidence': citations,
            'quality': self.gate.evaluate_report(hits, evs)
        }
        return report
