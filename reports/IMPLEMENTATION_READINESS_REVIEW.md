IMPLEMENTATION READINESS REVIEW

Scope
-----
Review of Project Management V2 documents and overall platform readiness to begin Priority 1 implementation (canonical Project Registry) while ensuring enterprise-wide consistency.

Documents reviewed
- reports/PROJECT_REGISTRY_ARCHITECTURE_V2.md
- reports/PROJECT_DATA_MODEL_V2.md
- reports/PROJECT_DATABASE_SCHEMA_V2.md
- reports/PROJECT_UI_WIREFRAMES_V2.md
- reports/PROJECT_IMPLEMENTATION_PLAN_V2.md

High-level findings (consistency & gaps)
- EOM consistency: The EOM defined in reports/PROJECT_DATA_MODEL_V2.md aligns closely with the requested Enterprise Object Model, but some entities are duplicated in the codebase (ERP `projects` vs Closeout `projects`) and require canonicalization.
  - Evidence: [services/project_closeout_service.py](services/project_closeout_service.py) and [erp_facturacion/erp.py](erp_facturacion/erp.py).

- Relationship model: Mermaid ER diagram exists in reports/ENTERPRISE_RELATIONSHIP_MODEL.md and maps most relations, but TASK/MILESTONE/RESOURCE entities are missing from current DBs.

- AI architecture: backoffice/agents/orchestrator.py provides a multi-agent template; however, direct orchestration of Closeout documents is not implemented and KnowledgeMemory ingestion is not consistently used by Closeout services.
  - Evidence: [backoffice/agents/orchestrator.py](backoffice/agents/orchestrator.py), [agents/knowledge_intelligence/memory/knowledge_memory.py](agents/knowledge_intelligence/memory/knowledge_memory.py), [pages/project_closeout.py](pages/project_closeout.py).

- Data governance: current Closeout persistence stores `master_data` as free-form JSON (`services/project_closeout_service.py`) — this makes governance and queryability harder. Recommend explicit schema fields and metadata on key entities.

- Document pipeline: extractor exists ([services/project_closeout_extractor.py](services/project_closeout_extractor.py)) but is heuristic-only and lacks OCR, classification, relationship extraction and ingestion into KnowledgeMemory/Graph.

- Truth Graph: backoffice/graph/store.py holds several entity types but lacks project nodes, graph persistence and automated ingestion.

Duplicated concepts discovered
- `projects` entity stored in ERP and Closeout — must map to canonical `Project`.
- `documents` stored in multiple places (ERP/Closeout) — unify into canonical `Document` with `object_store_url` and `versions`.

Missing entities / immediate additions required
- Tasks, Milestones, Resources, Deliverables: essential for schedule and CPM functionality.
- Project-level financial snapshot table or view for efficient KPIs.
- Graph nodes for projects and standard edge types.

Scalability risks
- Storing extracted text inline in SQL (`extracted_text`) will not scale for large corpora — move to object store and embedding store with text excerpts only in SQL.
- Synchronous LLM calls in UI could block — use background jobs for long-running orchestrations.

AI integration gaps
- Ingestion: Closeout does not index uploaded documents into KnowledgeMemory. Implement ingestion hook in `save_document`.
- Evidence & traceability: Agent outputs are not yet required to include `evidence_ids` in UI flows.

Knowledge Hub gaps
- KnowledgeMemory exists but lacks operational connectors from many modules (Closeout, ERP exports, Competitive Intelligence outputs). Prioritize connectors.

Truth Graph gaps
- GraphStore needs `project` support and persistent storage (not only in-memory). Implement graph persistence tables and ingestion from canonical sources.

Executive Intelligence gaps
- Report generation exists (backoffice/reporting/generator.py) but is scoped to GraphStore analytics; it needs to accept project-level inputs (canonical_project_id) and ingest financials from ERP and closeout reports.

Prioritized pre-implementation action list (must be completed before coding Priority 1)
1. Finalize and approve Enterprise Object Model (reports/ENTERPRISE_OBJECT_MODEL.md). (Owner: Chief Architect)
2. Decide canonical authority for financials vs project metadata (ERP vs Project Registry). (Owner: Finance/Product)
3. Add `canonical_project_id` mapping field to existing Closeout DB and ERP adapter design doc. (Owner: Backend)
4. Implement Knowledge Hub ingestion contract and required metadata fields; create sample ingestion implementation in dev. (Owner: Data Engineer)
5. Extend GraphStore to support project nodes and persist graph to disk/DB. (Owner: Backend)
6. Convert `master_data` free-form JSON to explicit columns or JSONB with defined keys (Owner: Backend)

Acceptance checklist to pass Approval Gate
- EOM approved and signed off.
- Migration plan for existing Closeout/ERP projects with roll-back plan.
- Knowledge Hub ingestion contract and a proof-of-concept (ingest one demo document and verify retrieval by project).
- Graph persistence and simple project node ingestion POC.
- Automated unit tests for new adapters and integration smoke tests.

Estimated readiness to begin Priority 1 after actions: 3–10 working days depending on approvals and availability of infra.

Next steps
- Resolve ownership questions for master data and confirm mapping rules between ERP and Project Registry.
- Approve EOM and the Data Governance Standard.
