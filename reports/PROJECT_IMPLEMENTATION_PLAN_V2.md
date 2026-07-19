PROJECT IMPLEMENTATION PLAN V2

Scope
-----
Detailed phased implementation plan to transform Project Management into the enterprise backbone (V2). The plan respects backward compatibility and incremental delivery.

Priority mapping (per user)
---------------------------
Priority 1: Canonical Project Registry
Priority 2: ERP Synchronization
Priority 3: Knowledge Hub Integration
Priority 4: Truth Graph
Priority 5: AI Orchestrator
Priority 6: Executive Intelligence
Priority 7: Automatic Executive Reports

Delivery phases and tasks
-------------------------
Phase A — Foundations (2–3 weeks)
1. Provision infra: Postgres instance (dev/prod), object store (S3 or local dev alternative), message broker (Redis/Kafka), vector DB (Chroma/hosted), graph DB (optional)
   - Deliverables: infra scripts, environment configs
   - Tests: connectivity, smoke tests

2. Implement Project Registry service
   - API: CRUD, search, events
   - DB: create projects table and `external_mappings`
   - Backwards compatibility: read existing `data/project_closeout/closeout.db` and create `external_ids.closeout`
   - Tests: unit tests for CRUD; migration test for closeout import
   - Estimate: 6–12 dev days

3. Add canonical_project_id to existing Closeout flows
   - Update `services/project_closeout_service.py` to include `canonical_project_id` where applicable (non-breaking).
   - Tests: ensure `scripts/generate_demo_project.py` populates `external_ids.closeout`.
   - Estimate: 2–4 dev days

Phase B — ERP Sync & Financials (2–4 weeks)
1. ERP Adapter (read-only then two-way)
   - Implement mapping logic (ERP project id → canonical_project_id) using `external_mappings`
   - Offer reconciliation endpoints and scheduled job
   - Estimate: 6–12 dev days

2. Materialize financial snapshots for reporting
   - Implement `invoices`/`payments` materialization or views; create `project_financial_summary` view
   - Add `/projects/{id}/financial` endpoint
   - Estimate: 6–10 dev days

Phase C — Knowledge Hub Integration (2–3 weeks)
1. On-upload ingestion
   - Hook `save_document` to call extractor and KnowledgeMemory.save_knowledge with canonical_project_id metadata.
   - Create background worker or async job to index heavy files and update Chroma.
   - Tests: indexing smoke test; search by project returns newly indexed doc
   - Estimate: 7–12 dev days

Phase D — Truth Graph & Linkers (2–3 weeks)
1. Extend GraphStore with `project` nodes and edges.
2. Implement graph ingesters that generate nodes/edges for each document, invoice, risk, meeting.
3. Provide APIs to query graph neighbors for a project.
4. Tests: ingestion unit tests; graph query correctness
5. Estimate: 10–15 dev days

Phase E — AI Orchestrator integration (2–4 weeks)
1. Define Orchestrator contract for project-scoped queries (context router and project resolver).
2. Implement safe retrieval pipeline: Knowledge Hub → Truth Graph → Evidence Ranking → Fact Checker → LLM (constrained prompt) → Executive Quality Evaluator
3. Persist LLM outputs as `insights` with references and confidence.
4. Tests: integration tests using mocked LLMs and sample docs
5. Estimate: 10–20 dev days

Phase F — Executive Intelligence & Auto-Reports (2–4 weeks)
1. Extend reporting generator to accept canonical_project_id and produce project-specific executive packs.
2. Schedule auto-generation and email/portal distribution.
3. Add ability to regenerate with revision history.
4. Tests: generation unit tests and acceptance criteria for evidence + confidence.
5. Estimate: 8–15 dev days

Phase G — UX polish, wireframes & dashboards (ongoing)
1. Integrate Gantt component, charts, and graph viewer into project page.
2. Improve uploads, metadata editing, and review flows.
3. Tests: E2E UI tests for main flows.
4. Estimate: 8–20 dev days

Cross-cutting work
------------------
- RBAC & access control (applies to all phases) — design roles, implement middleware.
- Observability & logging — ensure events, retries, failures are tracked.
- Tests: unit tests for all new services; integration tests for end-to-end flows; CI pipeline updates with smoke tests.

Acceptance criteria (minimum for each priority)
---------------------------------------------
- Priority 1 (Registry): CRUD works, events emitted, all existing Closeout projects mapped with `external_ids.closeout`.
- Priority 2 (ERP sync): ERP projects + invoices mapped to canonical ids, financial summary endpoint returns reconciled numbers.
- Priority 3 (Knowledge Hub): Uploaded docs visible via project-scoped semantic search within upload index window.
- Priority 4 (Truth Graph): Project node created and at least three edge types (document_of, invoice_for, risk_of) present.
- Priority 5 (Orchestrator): Project-scoped questions processed through full pipeline with listed evidence and confidence.
- Priority 6/7 (Executive reports): Scheduled reports generated with evidence + confidence and available for download.

Testing strategy
----------------
- Unit tests for each service and data access object (DAO).
- Integration tests for adapters (ERP, KnowledgeMemory, GraphStore) using test containers or lightweight mocks.
- End-to-end scenario tests: create project, upload doc, index, query AI assistant, generate report.

Backward compatibility & rollout
-------------------------------
1. Deploy Project Registry in read-only ingest mode.
2. Backfill mappings from Closeout and ERP.
3. Switch UI to show canonical_project_id; keep fallbacks to legacy ids.
4. Enable write paths gradually (first doc uploads, then project updates, then ERP accept sync).

Risk & mitigation
-----------------
- Data duplication/mismatch: map via `external_mappings` and reconcile via scheduled jobs.
- LLM hallucinations: always include evidence; apply fact-checker stage; require human validation before automated decisions.

Team & timeline (example)
-------------------------
- Small core team (2 backend, 1 frontend, 1 data engineer, 0.5 product/PM) can deliver Phase A–C in ~8–12 weeks.

Deliverables
------------
- API definitions and OpenAPI spec
- Database migrations & seeders
- Backfill scripts
- Unit/integration tests
- Updated UI components and wireframe implementations
