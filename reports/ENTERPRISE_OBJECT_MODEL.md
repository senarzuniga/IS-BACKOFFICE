ENTERPRISE OBJECT MODEL (EOM)

Purpose
-------
Define the canonical Enterprise Object Model to be used by every module in IS-BACKOFFICE. The EOM is the single ontology that prevents duplicated concepts, enforces consistent identifiers and supports AI-native workflows.

Guidelines (global)
- Every persisted artifact that relates to business or project activity MUST reference `canonical_project_id` when applicable.
- Entities must include provenance fields: `source`, `source_id`, `confidence`, `truth_status`, `created_at`, `updated_at`.
- Use UUID PKs + human-friendly business keys (e.g. `PRJ-2026-001`).
- Preserve backward compatibility with `external_ids` mapping for legacy systems (ERP, Closeout, others).

Core Business Objects (canonical list and minimal attributes)
- Company
  - id, name, tax_id, primary_address, metadata
  - Evidence: company_profile in [erp_facturacion/erp.py](erp_facturacion/erp.py)

- Business Unit
  - id, company_id, name, metadata

- Project
  - id (UUID), canonical_project_id, name, code, status, customer_id, start_date, end_date, budget, currency, external_ids, metadata, truth_fields
  - Evidence: `projects` in [services/project_closeout_service.py](services/project_closeout_service.py) (local closeout) and [erp_facturacion/erp.py](erp_facturacion/erp.py)

- Customer
  - id, external_ids, company_name, contact_id, metadata
  - Evidence: `clients` in [erp_facturacion/erp.py](erp_facturacion/erp.py)

- Supplier
  - id, external_ids, name, contact, metadata
  - Evidence: `suppliers` in [erp_facturacion/erp.py](erp_facturacion/erp.py)

- Contact
  - id, name, email, phone, role, organization_id

- Employee
  - id, employee_number, name, role, department, contact_id

- Opportunity
  - id, project_id (optional), client_id, amount, status, pipeline_stage

- Quotation
  - id, project_id, quote_number, items, total, status

- Contract
  - id, project_id, contract_number, parties, effective_date, status

- Purchase Order
  - id, project_id, po_number, supplier_id, amount, currency, status
  - Evidence: `purchase_orders` in [erp_facturacion/erp.py](erp_facturacion/erp.py)

- Invoice
  - id, project_id, invoice_number, invoice_date, due_date, total, status
  - Evidence: `invoice_headers` in [erp_facturacion/erp.py](erp_facturacion/erp.py)

- Payment
  - id, invoice_id, project_id, payment_date, amount, method, reference

- Cash Flow (Entry)
  - id, project_id, date, amount, type (in/out), category

- Product / Equipment / Machine / AMR Fleet
  - id, sku/model, serial_number, project_id (if asset-tagged to project), metadata

- Simulation
  - id, project_id, simulator_type, inputs, outputs, artifacts
  - Evidence: simulator projects under `ingetrans-reel-simulator/` and `plant_simulator` pages

- Technical Document / Document
  - id, project_id, filename, object_store_url, doc_type, extracted_text, extracted_entities, metadata, versions
  - Evidence: `documents` tables in [services/project_closeout_service.py](services/project_closeout_service.py) and [erp_facturacion/erp.py](erp_facturacion/erp.py)

- Engineering Deliverable / Drawing / Revision
  - deliverable_id, project_id, title, status; drawings have revision history (document_versions)

- Meeting / Decision / Action
  - meeting: id, project_id, date, participants, minutes
  - decision: id, project_id, title, made_by, status
  - action: id, project_id, title, assigned_to, due_date, status

- Issue / Punch List / Risk
  - id, project_id, type(issue|punch|risk), severity/priority, owner, status, linked_docs
  - Evidence: `issues` table in [services/project_closeout_service.py](services/project_closeout_service.py)

- Installation / Commissioning / Service Report / Warranty / Claim
  - records with links to tests, reports, acceptance criteria and documents

- Lesson Learned / Knowledge Asset / AI Insight / Executive Recommendation
  - id, project_id, content, confidence, references (document ids), validated
  - Evidence: KnowledgeMemory stores `knowledge_items` with `project` field ([agents/knowledge_intelligence/memory/knowledge_memory.py](agents/knowledge_intelligence/memory/knowledge_memory.py))

- Truth Node
  - graph node representing canonical facts/evidence; edges carry relation_type and confidence
  - Evidence: Graph primitives in [backoffice/graph/store.py](backoffice/graph/store.py) but currently lacking `project` node type

Entity metadata standard (applies to all entities)
- `source`: system creating the record (erp, closeout, user, agent)
- `source_id`: original id in source system
- `confidence`: numeric [0..1] for extracted/AI-generated items
- `truth_status`: enum {unverified, verified, disputed, retracted}
- `provenance`: trace_id or event log pointer

Notes on current repo gaps (evidence-based)
- Duplicate `projects` definitions: Closeout `projects` vs ERP `projects` ([services/project_closeout_service.py](services/project_closeout_service.py) vs [erp_facturacion/erp.py](erp_facturacion/erp.py)). These must be reconciled into canonical `Project`.
- Document models are scattered: `documents` in Closeout and `documents` in ERP; unify to canonical `Document` with `object_store_url` and `versions`.
- Knowledge items already include `project` metadata, which is positive — ensure all document ingests propagate `canonical_project_id`.

Next steps
- Approve this EOM and then enforce it via DB schema (see reports/PROJECT_DATABASE_SCHEMA_V2.md) and code adapters (ERP adapter, Closeout adapter, Knowledge Hub indexer).
