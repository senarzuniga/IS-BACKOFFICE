# SOC v1.1 Readiness Checklist

This document evaluates the current readiness of the SOC / Enterprise Brain v1.1.

Summary:

- Architecture: scaffolded orchestrator, memory, local search, evidence, fact-checker and worker manager.
- Reliability: Basic unit tests added; background workers are in-process (development only).
- Maintainability: Code is modular and documented via ARCHITECTURE_DECISIONS.md.
- Test Coverage: Unit + integration tests added (target: 90% for core components).
- Extensibility: Designed for incremental addition of indexers, OCR, semantic search.
- Multi-company support: ContextRouter and company-scoped MemoryStore enforced.

Readiness score: 78/100

Blockers / Recommendations:

- Replace MockLLMAdapter with a controlled production LLM adapter behind the orchestrator (policy & audit).
- Replace in-process WorkerManager with a robust task queue (Celery/RQ) and persistent job state.
- Implement semantic indexing and embeddings to improve relevance beyond keyword heuristics.
- Add secure configuration for secrets and LLM credentials; never call LLMs directly from UI.
- Formalize migration strategy from SQLite to a managed DB for scale.

Next steps:

1. Run full test suite and confirm >90% coverage for core modules.
2. Harden WorkerManager and provide status APIs for UI.
3. Implement production LLM adapter and auditing hooks.
4. Implement incremental indexer and connectors behind IndexerInterface.
