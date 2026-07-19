PROJECT DATA MODEL V2

Overview
--------
This document defines the canonical data model for `Project` and related entities required to make Project the central object across the Enterprise OS. Each artifact references `canonical_project_id`.

Modeling notes
---------------
- Use UUIDs or human-friendly canonical IDs for `canonical_project_id` (e.g., PRJ-2026-001). 
- Support `external_ids` to map legacy systems (ERP id, closeout id, other systems).
- Use JSONB / structured `metadata` for flexible fields and to maintain backward compatibility.
- Include AI/traceability metadata for each row: `source`, `source_id`, `confidence`, `truth_status`, `extracted_at`, `validated_by`.

Canonical Entities (minimum)
---------------------------
Below each entity lists core fields, types and relationships.

1. Project
- `id` (PK, UUID)
- `canonical_project_id` (unique human code)
- `name` (string)
- `code` (string)
- `status` (enum: Proposal, Open, Execution, SAT, Closed, OnHold)
- `customer_id` (ref to Customer)
- `primary_contact` (ref to Contact)
- `start_date`, `end_date` (date)
- `budget` (numeric)
- `currency` (string)
- `external_ids` (JSON: {erp:..., closeout:..., other:...})
- `metadata` (JSON)
- `created_at`, `updated_at`, `created_by`, `updated_by`
- `source`, `source_id`, `confidence`, `truth_status`

2. ProjectPhase
- `id`, `project_id` (FK), `name`, `phase_order`, `start_date`, `end_date`, `status`, `metadata`

3. Milestone
- `id`, `project_id`, `phase_id` (optional), `name`, `planned_date`, `actual_date`, `critical` (bool), `status`

4. Task (work package)
- `id`, `project_id`, `phase_id`, `milestone_id` (optional), `title`, `description`, `assignee_id` (resource), `estimated_hours`, `actual_hours`, `start_date`, `end_date`, `status`, `dependencies` (list of task ids), `priority`

5. Risk
- `id`, `project_id`, `title`, `description`, `probability` (low/med/high), `impact` (financial/schedule/quality), `mitigation`, `owner_id`, `status`, `risk_score` (computed)

6. Issue
- `id`, `project_id`, `issue_id` (human), `source` (import/manual/site), `category`, `description`, `priority`, `date_opened`, `owner_id`, `due_date`, `status`, `resolution`, `linked_documents` (list)

7. Decision
- `id`, `project_id`, `title`, `date`, `decision_text`, `decided_by`, `approval_status`, `linked_actions` (list)

8. Action
- `id`, `project_id`, `title`, `assigned_to`, `due_date`, `status`, `related_decision_id`

9. Meeting
- `id`, `project_id`, `title`, `date`, `participants` (list), `minutes` (document id / text), `action_items` (list)

10. Customer / Supplier (reference entities)
- Keep canonical customer/supplier IDs; map ERP client/supplier IDs via `external_ids`.

11. PurchaseOrder (light model)
- `id`, `project_id`, `po_number`, `supplier_id`, `amount`, `currency`, `po_date`, `status`, `erp_id` (external)

12. Invoice / Payment
- `invoice_id`, `project_id`, `client_id`, `invoice_number`, `invoice_date`, `due_date`, `subtotal`, `iva`, `total`, `status`, `payments` (link table)

13. CashFlowEntry
- `id`, `project_id`, `date`, `amount`, `type` (inflow/outflow), `category`, `reference_id`

14. EngineeringDeliverable / Drawing / Revision
- Deliverable: `id`, `project_id`, `title`, `owner`, `status`, `deliverable_type`
- Drawing: `id`, `deliverable_id`, `drawing_number`, `revision`, `file_id`
- Revision history tracked in `document_versions`

15. Installation / Commissioning / SAT
- `installation_record`: `id`, `project_id`, `site`, `date`, `report_document_id`, `status`
- `commissioning_record`: `id`, `project_id`, `test_name`, `results`, `reported_by`, `document_id`

16. PunchListItem
- `id`, `project_id`, `issue_id`, `location`, `description`, `priority`, `status`, `assigned_to` 

17. Warranty / Claim
- `warranty_id`, `project_id`, `item`, `start_date`, `end_date`, `coverage`, `claim_id` (FK to claims)

18. Email / Document
- Documents and Emails stored as `document` rows: `id`, `project_id`, `file_path` or `object_store_url`, `filename`, `doc_type`, `metadata`, `extracted_text`, `confidence`, `source`, `source_id`, `uploaded_at`, `uploaded_by`

19. AI Insight / Executive Recommendation / Knowledge Node
- Store LLM outputs as `insights`: `id`, `project_id`, `insight_type`, `content`, `confidence`, `source`, `created_at`, `references` (list of document ids), `validated`

20. Truth Graph Node / Edge
- Node: `id`, `node_type`, `project_id` (optional), `payload` (JSON), `created_at`
- Edge: `id`, `source_node_id`, `target_node_id`, `relation_type`, `confidence`

Cardinality & indexing
----------------------
- Most tables are `project_id` partitioned / indexed.
- Frequently queried fields: canonical_project_id, external_ids->erp, status, date ranges, owner/assignee.

Example JSON: Project with a phase, milestone and a task
-----------------------------------------------------
{
  "canonical_project_id": "PRJ-2026-001",
  "name": "ACME Corrugator Line",
  "external_ids": {"erp":"ERP-12345","closeout":"DEMO-001"},
  "phases": [
    {"name":"Engineering","phase_order":1,"milestones":[{"name":"Design freeze","planned_date":"2026-05-01"}]}
  ],
  "metadata": {"plant":"Seville","equipment":"SR1400"}
}

Mapping to existing repo artifacts
----------------------------------
- `services/project_closeout_service.py` currently stores projects in local SQLite — add `canonical_project_id` and migrate.
- `erp_facturacion/erp.py` contains ERP tables; `external_ids.erp` will map ERP project PKs.
- KnowledgeMemory (`agents/knowledge_intelligence/memory/knowledge_memory.py`) stores a `project` field in metadata; indexer must use canonical_project_id.

Notes on lightweight vs heavyweight storage
-----------------------------------------
- Documents / emails: keep metadata in SQL but store binary/object in S3 or `data/` in dev.
- Truth Graph: use graph DB for rich queries (Neo4j/Janus) or edge table for simpler deployments.
