from __future__ import annotations

from typing import List, Dict, Optional
from .indexer import Indexer


class HybridRetrieval:
    """Facade for hybrid retrieval: keyword + (placeholder) semantic + entity-aware.

    At the moment this wraps the existing `Indexer`. Later we will plug
    semantic search (embeddings) and graph-based retrieval.
    """

    def __init__(self, db_path: Optional[str] = None):
        self.idx = Indexer(db_path=db_path)

    def keyword_search(self, company: str, query: str, limit: int = 10) -> List[Dict]:
        return self.idx.search_by_company_name(company, query, limit=limit)

    def semantic_search(self, company: str, vector, top_k: int = 10) -> List[Dict]:
        # Placeholder: integrate embedding store (e.g., FAISS) later.
        return []

    def entity_search(self, company: str, entity: str, limit: int = 20) -> List[Dict]:
        # Basic fallback: keyword search for entity tokens
        return self.keyword_search(company, entity, limit=limit)
