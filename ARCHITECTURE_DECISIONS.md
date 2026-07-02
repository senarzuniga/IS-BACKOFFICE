# SOC / Enterprise Brain — ARCHITECTURE_DECISIONS

This document records design decisions made while implementing SOC v1.1.

1. Memory persistence
- Decision: Use SQLite for the initial persistent MemoryStore.
- Rationale: Lightweight, cross-platform, easy migration to server DB later.
- File: `soc/brain/memory_store.py`.

2. Local Search
- Decision: Implement a hybrid local search scaffold that presently relies on the MemoryStore documents table and ranks results by recency (0.6) and keyword relevance (0.4).
- Rationale: Allows incremental improvement (add file indexers, OCR, embeddings later) without changing the orchestrator contract.
- File: `soc/brain/local_search.py`.

3. Context Router
- Decision: Provide a small router to resolve company names to UUIDs and enforce scoping.
- Rationale: Keeps downstream components company-aware and prevents cross-company data leakage in queries.
- File: `soc/brain/context_router.py`.

4. LLM usage
- Decision: No direct external LLM calls. Provide `MockLLMAdapter` for offline development and require a production adapter behind the same interface.
- Rationale: Enforces orchestration, auditing, and safe mediated LLM usage.
- File: `soc/brain/llm_adapter.py`.

5. Evidence & Fact Checking
- Decision: Implement a minimal evidence collector and heuristic fact checker to aggregate confidence and detect simple contradictions.
- Rationale: Early safety and traceability; will be replaced by more robust checks later.
- Files: `soc/brain/evidence.py`, `soc/brain/fact_checker.py`.

6. Worker model
- Decision: Provide an in-process WorkerManager for local development; production must replace with proper background workers and queues.
- File: `soc/brain/workers.py`.

7. Incremental rollout
- Decision: Keep UI mock separate from ingestion/indexing. All indexing is manual and explicit.

Next steps:
- Implement MemoryStore-backed unit tests and small integration test for AIOrchestrator using the mock LLM adapter.
- Add indexer interface and incremental file indexer.
