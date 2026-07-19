Project Management — Architecture & Integration Map

Objective: show how Project Closeout currently sits in the platform and where integration points should be added.

Components (current state & recommended integration)

- Project Closeout (pages/project_closeout.py, services/project_closeout_service.py)
  - Current: local SQLite DB (data/project_closeout/closeout.db), file store under data/project_closeout/files/, reporter writes to data/project_closeout/reports/
  - Recommendation: expose canonical project service API and message/queue events for ingestion (e.g., POST /api/projects/{id}/ingest-document).

- ERP (erp_facturacion/erp.py)
  - Current: separate SQLite DB for invoices, POs, projects. Contains project-level financial data but not linked to Closeout.
  - Recommendation: implement sync (pull/push) or foreign-key mapping to canonical project registry. Provide endpoints or ETL to reconcile invoices/POs by project code.

- Knowledge Hub / Enterprise Memory (agents/knowledge_intelligence/memory/knowledge_memory.py)
  - Current: supports `project` metadata and Chroma-based RAG indexing.
  - Recommendation: build an ingestion connector in services/project_closeout_service.save_document to index document text and metadata into KnowledgeMemory with `project` tag.

- Truth Graph (backoffice/graph/store.py)
  - Current: GraphStore holds clients/offers/opportunities/documents but lacks `project` objects.
  - Recommendation: extend GraphStore with `project` entity; create relations from `project` → `offer` / `opportunity` / `purchase_order` / `document`.

- AI Orchestrator / Agents (backoffice/agents/orchestrator.py, agents/knowledge_intelligence/orchestrator.py)
  - Current: orchestrators exist and UIs exist in pages/knowledge_intelligence.py. Closeout does not invoke them.
  - Recommendation: provide an event hook (e.g., on-report-generation) to call Orchestrator for drafting executive summaries, risk analyses and structured register suggestions.

- Executive Intelligence (backoffice/reporting/generator.py, api/routes/reporting.py)
  - Current: reports draw from GraphStore and analytics pipelines; not from closeout DB.
  - Recommendation: extend ReportGenerator to optionally consume Closeout canonical projects and project-level P&L and KPIs.

Data flows (recommended)
1. Canonical Project Registry: central `projects` service (DB + API). ERP writes/feeds canonical IDs; Closeout, GraphStore and KnowledgeMemory reference canonical ID.
2. Document ingestion: on file upload in Closeout, service saves file, extracts text (existing extractor), then sends document metadata + text to KnowledgeMemory and to GraphStore as `document` node linked to project.
3. Financial sync: scheduled ETL job to reconcile ERP invoices/POs → canonical project ledger used by the Closeout reporter and Executive Intelligence.
4. AI enrichment: when report generated, orchestrator runs (ingest relevant docs, produce executive summary + risk scoring) and writes results to KnowledgeMemory and report_versions table.

Files to change (first iteration)
- services/project_closeout_service.py — add connectors to KnowledgeMemory and GraphStore; extend save_document to call extractor + indexer
- agents/knowledge_intelligence/memory/knowledge_memory.py — ensure ingestion API methods are public and documented
- backoffice/graph/store.py — add `project` entity, import/export helpers
- erp_facturacion/erp.py — add API or export function to fetch project financials by canonical ID
- backoffice/reporting/generator.py — accept optional project_id parameter and integrate closeout P&L & KPIs
