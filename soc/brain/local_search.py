from __future__ import annotations

import time
from typing import Dict, List, Optional

from .memory_store import MemoryStore


class LocalSearch:
    """Hybrid Local Search over Enterprise Memory (scaffold).

    This implementation currently searches the `documents` table in the
    `MemoryStore`. It provides ranking by recency + simple keyword
    relevance. The class is designed to be extended with file indexing,
    OCR and semantic search later.
    """

    def __init__(self, memory_store: MemoryStore):
        self.memory_store = memory_store

    def search(self, company_uuid: Optional[str], query: str, limit: int = 10) -> List[Dict]:
        docs = self.memory_store.search_documents(company_uuid=company_uuid, query=query, limit=limit * 5)
        if not docs:
            return []

        tokens = [t.lower() for t in (query or '').split() if t.strip()]
        min_m = min(d.get('last_modified', 0) for d in docs) if docs else time.time()
        max_m = max(d.get('last_modified', 0) for d in docs) if docs else time.time()

        results = []
        for d in docs:
            content = (d.get('content') or '').lower()
            relevance = sum(content.count(t) for t in tokens) if tokens else 0
            rel_norm = min(relevance, 20) / 20.0
            if max_m > min_m:
                recency = (d.get('last_modified', 0) - min_m) / (max_m - min_m)
            else:
                recency = 1.0
            score = 0.6 * recency + 0.4 * rel_norm
            results.append({
                'company_uuid': d.get('company_uuid'),
                'file': d.get('file_name'),
                'path': d.get('file_path'),
                'last_modified': d.get('last_modified'),
                'summary': d.get('summary'),
                'confidence': round(min(1.0, score), 2),
                'doc_uuid': d.get('uuid'),
                'score_raw': score,
            })

        results = sorted(results, key=lambda x: x['score_raw'], reverse=True)[:limit]
        return results

    def index_document(self, company_uuid: str, file_name: str, content: str, file_path: Optional[str] = None, source_ref: Optional[str] = None) -> str:
        """Index a single document into MemoryStore (manual operation).

        This method does not perform file IO itself; callers choose how to
        obtain the content (e.g., from safe parsers or manual upload).
        """
        return self.memory_store.add_document(company_uuid, file_name, content, file_path=file_path, source_ref=source_ref)
