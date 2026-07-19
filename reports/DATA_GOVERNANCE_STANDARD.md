DATA GOVERNANCE STANDARD

Purpose
-------
Define enterprise-grade governance rules for master data, transactional data, knowledge assets and AI-generated content across IS-BACKOFFICE.

Principles
----------
- Single Source of Truth (SSoT): canonical records (Company, Project, Customer, Supplier, Document) must exist in Project Registry or their authoritative system; anything else references them by `canonical_id`.
- Provenance-first: every record must carry `source`, `source_id`, `trace_id`, and timestamps.
- Truth confidence: store `confidence` and `truth_status` on AI-extracted or agent-created records.
- Immutable audit trail: maintain append-only audit log of changes for critical entities.

Data categories
---------------
- Master Data: Company, Business Unit, Customer, Supplier, Product, Employee. Source: canonical master service (ERP/CRM). These must be edited only through defined processes.
- Reference Data: enumerations (currency, country, project status). Stored centrally and versioned.
- Transactional Data: Invoices, Payments, POs, Tasks, Issues. Authoritative sources: ERP or Project Registry depending on ownership.
- Knowledge Assets: Extracted text, embeddings, insights. Stored in KnowledgeMemory; must reference source documents and project.
- Historical Records: Retain documents, versions, and audit logs per retention policy.
- AI Generated Knowledge: insights, recommendations, must include confidence and references; never treated as authoritative without validation.

Source confidence and truth status
- `confidence` field: float [0..1], assigned by extractor/agent.
- `truth_status`: {unverified, verified, disputed, retracted}
- Rules:
  - Data imported from ERP gets `source=erp`, `confidence=1.0`, `truth_status=verified` by default.
  - Data extracted from documents gets extracted `confidence` and `truth_status=unverified` until validated.

Versioning & lineage
---------------------
- Documents: maintain `document_versions` with `created_by`, `created_at`, `file_hash`.
- Records updated by agents: store a `provenance` object linking to the evidence documents and the agent run id.

Conflict resolution
-------------------
1. Detect: scheduled reconciliation jobs identify duplicates or conflicting values across authoritative sources.
2. Resolve order (automated): authoritative system wins (ERP > Project Registry if ERP is canonical for financials), else highest confidence.
3. Human escalation: conflicts that cannot be resolved automatically are routed to a data steward queue.

Data access & security
----------------------
- RBAC: project-level permissions, role-based for approvals.
- Data masking: PII redaction rules for LLM inputs; audit which prompts included PII.

Retention & archival
---------------------
- Define retention policy per entity class (legal, contract, warranty). Implement archival to cold storage and index pointers.

Data quality metrics & monitoring
--------------------------------
- Completeness (% of required fields present), Freshness (age of last update), Duplication rates, Source mismatch counts, Ingestion error rates.
- Create dashboards for these metrics and alert on thresholds.

Enforcement mechanisms
----------------------
- Pre-ingest validators: JSON schema + business rules.
- Post-ingest reconciliers: nightly jobs comparing canonical records.
- CI gates: migrations must include automated verification scripts.

Mapping to repo and immediate actions
------------------------------------
- Add `source`, `source_id`, `confidence` and `truth_status` fields to critical tables (projects, documents, issues) — currently `services/project_closeout_service.py` stores master_data as JSON; migrate to explicit fields for governance.
- Implement audit log table and integrate event emission from Project Registry.
