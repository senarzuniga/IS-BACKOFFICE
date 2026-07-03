from __future__ import annotations

from typing import List, Dict
from .evidence_store import EvidenceStore


class CitationBuilder:
    """Build human-readable citations for evidence items.

    This component converts Evidence records into a standardized citation
    format suitable for inclusion in executive reports.
    """

    def __init__(self, evidence_store: EvidenceStore):
        self.evidence = evidence_store

    def build_citation(self, ev) -> str:
        # ev is expected to be an Evidence dataclass or dict-like
        src = ev.source_id
        date = ev.source_date or ev.extraction_ts
        snippet = (ev.text[:200] + '...') if len(ev.text) > 200 else ev.text
        return f"[{src}] {date}: {snippet}"

    def build_citations(self, evidence_list: List) -> List[str]:
        return [self.build_citation(e) for e in evidence_list]
