"""Shared application state (singletons)."""
from backoffice.graph.store import GraphStore
from backoffice.extraction.review_queue import ReviewQueue

graph_store = GraphStore()
review_queue = ReviewQueue()
