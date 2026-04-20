"""Semantic search over stored entities using TF-IDF-style scoring."""
from __future__ import annotations
import math
import re
from typing import Any, Dict, List, Tuple

from backoffice.graph.store import GraphStore


def _tokenize(text: str) -> List[str]:
    return re.findall(r"[a-zA-Z0-9À-ÿ]+", text.lower())


def _tf_idf_score(query_tokens: List[str], doc_tokens: List[str]) -> float:
    if not query_tokens or not doc_tokens:
        return 0.0
    doc_set = set(doc_tokens)
    matches = sum(1 for t in query_tokens if t in doc_set)
    return matches / math.sqrt(len(query_tokens) * len(doc_tokens) + 1)


class SemanticSearch:
    """Searches entities in the graph using keyword/TF-IDF similarity."""

    def __init__(self, store: GraphStore):
        self._store = store

    def search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        q_tokens = _tokenize(query)
        results: List[Tuple[float, Dict[str, Any]]] = []

        # Search clients
        for c in self._store.get_all_clients():
            text = f"{c.name} {c.industry or ''} {c.country or ''}"
            score = _tf_idf_score(q_tokens, _tokenize(text))
            if score > 0:
                results.append((score, {"type": "client", "id": c.id, "name": c.name, "score": score}))

        # Search offers
        for o in self._store.get_all_offers():
            text = f"{o.title} {o.status}"
            score = _tf_idf_score(q_tokens, _tokenize(text))
            if score > 0:
                results.append((score, {"type": "offer", "id": o.id, "title": o.title, "score": score}))

        # Search opportunities
        for opp in self._store.get_all_opportunities():
            text = f"{opp.title} {opp.stage}"
            score = _tf_idf_score(q_tokens, _tokenize(text))
            if score > 0:
                results.append((score, {"type": "opportunity", "id": opp.id, "title": opp.title, "score": score}))

        results.sort(key=lambda x: x[0], reverse=True)
        return [r[1] for r in results[:top_k]]
