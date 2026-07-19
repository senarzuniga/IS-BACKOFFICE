ENTERPRISE LEARNING STANDARD
===========================

Version: 1.0
Purpose: Describe how the platform learns from completed work, how lessons are captured, and the policies for enriching Knowledge Hub, Truth Graph and Enterprise Memory.

Goals
-----
- Capture validated knowledge from completed projects and decisions.
- Maintain a clean, searchable, and versioned repository of lessons, playbooks, and standards.
- Feed back learnings into models, templates and playbooks to improve future performance.

What becomes Permanent Knowledge
-------------------------------
- Validated decisions and their evidence bundles.
- Approved reports and executive judgments.
- Project history: milestones, changes, post-mortems, KPIs.
- Lessons learned entries with root cause analysis and remediation.
- Updated playbooks and standard operating procedures (SOPs).

What is NOT Stored Permanently
------------------------------
- Temporary calculations, ephemeral drafts, or model internal states that lack verifiable evidence.
- Hallucinated or unverified claims.

Project Completion Enrichment Flow
---------------------------------
1. Trigger: project status marked `completed` or `closed`.
2. Collect: final reports, project KPIs, post-mortem documents, change logs, financial reconciliation.
3. Extract: run Document Intelligence + Project Management Agent to extract structured lessons, metrics and root causes.
4. Validate: Fact Checker + Truth Graph reconciliation.
5. Canonicalize: map entities to `canonical_project_id`, suppliers, customers, and versions.
6. Persist: write validated artifacts to Enterprise Memory and update Truth Graph nodes.
7. Publish: add entries to Knowledge Hub and signal relevant owners for review and acceptance.

Lessons Schema (minimal)
- `lesson_id`
- `project_id`
- `title`
- `summary`
- `root_cause`
- `action_items`
- `owner`
- `evidence_ids`
- `tags` (e.g., engineering, procurement, commercial)
- `severity`
- `created_at`

Governance & Owners
--------------------
- Each lesson must have an owner for verification and acceptance.
- Data Stewards validate canonical mappings and apply retention/PII rules.

Retention & Privacy
-------------------
- Retention policy applied per data class (financials, contracts, lessons). See Data Governance Standard for retention windows.
- PII redaction applied before Knowledge Hub indexing (Document Intelligence stage). Raw source kept under stricter ACLs.

Model & Template Updates
------------------------
- When a lesson meets quality criteria and is accepted, it is tagged for model retraining or template update.
- Retraining events are batched and governed by ML Ops policy (owner, dataset snapshot, validation tests).

KPIs for the Learning Loop
-------------------------
- lessons_ingested_per_project
- lesson_acceptance_rate
- time_to_publish_lesson
- percent_of_models_updated_by_lessons
