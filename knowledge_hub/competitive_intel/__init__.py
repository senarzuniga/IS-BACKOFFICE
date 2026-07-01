"""Competitive Intelligence module (scaffold).

This package provides skeletons and contracts for the Competitive
Intelligence Engine. It is intentionally non-destructive and contains
no network scraping or indexing logic that runs on import.
"""

from .indexer import Indexer
from .graph import KnowledgeGraph
from .score import compute_scores

__all__ = ["Indexer", "KnowledgeGraph", "compute_scores"]
