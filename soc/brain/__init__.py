"""Enterprise Brain core package.

Provides the Enterprise Memory, Local Search, Context Router, AI
Orchestrator, Evidence Layer, Fact Checker and worker skeletons for
SOC v1.1. This package is a scaffold: it implements the contracts and
local persistence but does NOT execute background indexing or external
LLM calls by default.
"""

from .memory_store import MemoryStore
from .local_search import LocalSearch
from .context_router import ContextRouter
from .ai_orchestrator import AIOrchestrator
from .llm_adapter import MockLLMAdapter
from .evidence import collect_evidence
from .fact_checker import assess_evidence
from .workers import WorkerManager
from .indexer_interface import IndexerInterface

__all__ = [
    'MemoryStore',
    'LocalSearch',
    'ContextRouter',
    'AIOrchestrator',
    'MockLLMAdapter',
    'collect_evidence',
    'assess_evidence',
    'WorkerManager',
    'IndexerInterface',
]
