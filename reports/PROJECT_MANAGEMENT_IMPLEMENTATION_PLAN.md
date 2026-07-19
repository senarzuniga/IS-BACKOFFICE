Project Management — Implementation Plan (step-by-step)

This plan converts the roadmap into sequenced engineering tasks, with target deliverables, affected files, DB changes, tests and estimates.

Phase 0 — Preparation (1–2 dev days)
- Create tasks, staging branch, CI smoke tests, backup data/project_closeout/closeout.db copy.
- Files: none; process only.

Phase 1 — Canonical Project Registry (6–12 dev days)
1. Design schema: `projects_registry` table with canonical_id, external_ids (ERP_project_code), name, customer_id, status, created_at, updated_at.
   - DB change: add new table in a central location (e.g., data/projects_registry.db or reuse erp DB).
2. Implement API endpoints: GET/POST /api/projects, /api/projects/{id}/sync-from-erp
   - Files: add api/routes/projects.py; update main router registration.
3. Sync job: implement export/import script to map erp_facturacion.projects ↔ projects_registry.
   - Files: erp_facturacion/erp.py (export function), services/project_closeout_service.py (sync import).
4. Tests: unit tests for schema migration and sync mappings.

Phase 2 — Financial Reconciliation & Project P&L (10–18 dev days)
1. Add service to fetch ERP invoices/POs by canonical project id (erp_facturacion/erp.py API function).
2. Implement reconciliation logic in backoffice/reporting/generator.py and services/project_closeout_reporter.py to consume ERP financials and attach to JSON/HTML closeout.
3. UI: show financial summary tab in pages/project_closeout.py (read-only initially).
4. Tests: integration test to generate project P&L using seeded demo data.

Phase 3 — Schedule model + Gantt (12–25 dev days)
1. DB changes: add tables `tasks`, `milestones`, `task_dependencies` in closeout DB.
2. API endpoints for CRUD on tasks (api/routes/projects.py or services layer).
3. UI: task editor and interactive Gantt using `plotly.express.timeline` or `dash` embedded component in Streamlit.
4. Reporter: include schedule JSON in report_versions output so external Gantt consumers can use it.
5. Tests: unit tests for CRUD + sample Gantt render smoke test.

Phase 4 — Change-order workflow & document versioning (9–18 dev days)
1. Extend `change_orders` with `state`, `requested_by`, `approved_by`, `approved_at`, `audit_log`.
2. Document versioning: add `document_versions` table and `current_version_id` in `documents` table.
3. UI: change-order approval UI with role checks (Streamlit simple roles config) and document history viewer.
4. Tests: workflow state transitions + doc versioning tests.

Phase 5 — Knowledge Hub ingestion & AI hooks (14–28 dev days)
1. On file save, call extractor (services/project_closeout_extractor.extract_text_and_entities_from_file) and then KnowledgeMemory.save_knowledge (agents/knowledge_intelligence/memory/knowledge_memory.py) with `project` metadata.
2. Add orchestrator call on report generation: send payload to agents/knowledge_intelligence/orchestrator.py to produce executive summary and risk signals; persist results in report_versions.
3. Tests: indexing smoke test; orchestrator integration tests (mock LLM where appropriate).

Phase 6 — Dashboards, Risk Register, Resource Planning (12–30 dev days)
- Implement Risk, Actions, Decisions tables and UI; implement KPI dashboard page derived from projects + ERP + tasks.

Testing, Validation, Delivery (ongoing)
- Add unit tests and integration tests to `tests/` for each area.
- Create demo data generator updates (scripts/generate_demo_project.py) to include tasks, CO workflows and financials.

Estimated total: 600–1200 hours (cross-check with roadmap). Prioritise Phase 1→2→3 to unlock reporting and AI ingestion.
