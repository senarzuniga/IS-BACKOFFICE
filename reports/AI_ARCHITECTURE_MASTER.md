AI ARCHITECTURE MASTER

Purpose
-------
Define responsibilities and contracts for all AI components in IS-BACKOFFICE so agents, orchestrators and memory systems integrate consistently and safely with the Enterprise Object Model.

Core AI components and responsibilities
- AI Coordinator
  - Global orchestration entrypoint for scheduled or user-initiated AI tasks. Responsible for routing to the Context Router and enforcing safety policies.

- Context Router
  - Given a user query and context, select candidate data slices (project scope, time window, document sets) and prepare input for Project Resolver.
  - Inputs: user prompt, project selectors, access control.
  - Evidence: pages/knowledge_intelligence.py context UI; orchestrator pattern in [backoffice/agents/orchestrator.py](backoffice/agents/orchestrator.py).

- Project Resolver
  - Map inputs to canonical_project_id and fetch project-scoped artifacts (documents, invoices, graph nodes, tasks). Must call Project Registry API.

- Knowledge Agent
  - Executes semantic search against KnowledgeMemory / Vector DB and returns ranked document candidates with snippets and scores.
  - Evidence: [agents/knowledge_intelligence/memory/knowledge_memory.py](agents/knowledge_intelligence/memory/knowledge_memory.py).

- ERP Agent
  - Fetches structured financial and procurement data for a project via ERP adapter. Returns canonicalized PO/Invoice/Payment records.

- Engineering Agent
  - Retrieves engineering deliverables, drawing revisions, test reports and consolidates acceptance criteria for commissioning.

- Finance Agent
  - Computes reconciliations, cash flow forecasts and financial KPIs using ERP-adapter outputs.

- Sales Agent / Competitive Intelligence Agent / Simulation Agent
  - Domain-specific agents that fetch and summarize domain datasets; see `agents/competitive_intelligence` and simulators in repo.

- Report Writer Agent
  - Given structured evidence and executive templates, produces drafts (Markdown/HTML/PDF) and attaches evidence references and confidence metrics. Use deterministic templates and do not allow hallucination.

- Fact Checker
  - Validates candidate claims by querying the Truth Graph for matching facts and by cross-checking numeric values in ERP/Document extractions.

- Truth Validator
  - Applies graph-based consistency rules (e.g., PO total = sum of lines, invoice total not exceeding PO, milestone acceptance before payment release). Produces conflicts list.

- Executive Reviewer / Quality Evaluator
  - Human-in-the-loop or automated evaluators that compute the Executive Quality Score and decide publish/regenerate.

- Self Improvement Agent
  - Collects failed cases, feedback and automates retraining / prompt adjustments into the memory manager.

- Memory Manager
  - Handles KnowledgeMemory ingestion, embedding storage, vector index management and deduplication.
  - Evidence: `KnowledgeMemory` implementation in agents.

Design principles (no duplicated responsibilities)
- Single responsibility per agent; orchestration composes agents into pipelines (see MultiAgentOrchestrator in [backoffice/agents/orchestrator.py](backoffice/agents/orchestrator.py)).
- No agent may return final executive output without Report Writer Agent and Executive Reviewer stages.
- Agents should return structured responses with `evidence_ids`, `confidence`, and `trace` metadata.

Safe information flow (enforced pipeline)
1. User Question
2. Context Router (restrict scope) → Project Resolver (canonical_project_id)
3. Knowledge Agent (semantic search) + ERP Agent + Engineering Agent
4. Evidence Aggregator (merge candidates)
5. Evidence Ranking (by confidence, recency, provenance)
6. Fact Checker (Truth Graph validation)
7. Report Writer Agent (generate draft with citations)
8. Executive Reviewer (human or auto quality evaluator) → Quality Score
9. If score ≥ threshold (default 0.9) publish; else iterate

Implementation notes
- Use interface contracts (typed payloads) between agents. Example payload fields: `project_id`, `query`, `candidate_documents` (list of {doc_id, score}), `trace_id`.
- LLM calls must be sandboxed and logged. Store prompt + response + plan in audit logs.
- Use a central `Orchestrator` that can run both synchronous queries (user asks) and asynchronous tasks (daily executive packs).

Evidence and repo mapping
- Orchestrator pattern: [backoffice/agents/orchestrator.py](backoffice/agents/orchestrator.py)
- KnowledgeMemory: [agents/knowledge_intelligence/memory/knowledge_memory.py](agents/knowledge_intelligence/memory/knowledge_memory.py)
- Knowledge UI: [pages/knowledge_intelligence.py](pages/knowledge_intelligence.py)
- Project Closeout extractor: [services/project_closeout_extractor.py](services/project_closeout_extractor.py) (needs to be replaced by robust document pipeline)

Security, privacy and compliance
- Enforce RBAC for query scopes — agents must only access artifacts the user is allowed to see.
- Sanitize PII in LLM prompts; prefer redaction or tokenized references.

Next steps
- Define concrete typed contracts (pydantic models) for agent inputs/outputs and implement adapters in each domain agent.
