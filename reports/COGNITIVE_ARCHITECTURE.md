COGNITIVE ARCHITECTURE
======================

Version: 1.0
Status: Approved as Enterprise Foundation (PHASE 0.5)

Purpose
-------
This document defines how the platform "thinks": the canonical cognitive model, layer responsibilities, interfaces and quality gates. It enforces an evidence-first, auditable, and repeatable reasoning methodology that applies to all modules and agents.

Principles
----------
- Evidence-first: every inference, recommendation, and decision must point to verifiable evidence (evidence_ids).
- Layered cognition: the system progresses through explicit layers (Data → Information → Knowledge → Understanding → Reasoning → Recommendation → Decision Support → Action) and must not skip layers.
- Auditability: every output includes provenance, confidence, timestamps, and processing version.
- Gatekeeping: automated quality gates (Executive Quality Score) control promotions to recommendation and action.
- Coordinator-centric orchestration: the Coordinator Agent orchestrates; no single specialized agent may unilaterally produce executive recommendations.

Cognitive Model (layers)
------------------------
1. Data
   - Raw facts: files, database rows, sensor readings, transaction logs, OCR text, embeddings.
   - Storage: object store + raw tables in Enterprise Memory; minimal indexing in Knowledge Hub.
   - Artifact examples: `raw_document_id`, `erp_row_id`, `sensor_stream_id`.

2. Information
   - Structured extracts and indexes derived from Data (NER, invoices parsed, normalized fields).
   - Storage: Knowledge Hub indexing, extraction tables, metadata stores.
   - Artifacts include typed fields (date, amount, party_id), normalized entities (supplier_id).

3. Knowledge
   - Linked facts and relationships (entities, canonical IDs, verified mappings). Represented in the Truth Graph and canonical stores.
   - Storage: Truth Graph for relationships; Enterprise Memory for validated artifacts.

4. Understanding
   - Aggregated patterns, derived KPIs, business-contextual summaries (project cashflow trends, milestone slippage).
   - Produced by domain agents and stored with explanation and evidence pointers.

5. Reasoning
   - Multi-step inference combining Knowledge + Understanding to produce supported conclusions. Includes simulation outputs and counterfactuals.
   - Must emit the chain-of-evidence linking back to Knowledge and Information.

6. Recommendation
   - Actionable options with impacts, risks and rationale. Each recommendation contains recommended actions, expected outcomes, measurement plan and confidence.
   - Promotions into Recommendation require cross-validation and EQA >= threshold.

7. Decision Support
   - Decision classification, required approvals, financial/operational impact analysis and suggested decision gates. Prepared for human signoff.

8. Action
   - Approved commands to downstream systems (ERP updates, notifications, POs). All automated actions require explicit approval policy and an auditable record.

Layer Transition Rules
----------------------
- No component may produce a Recommendation without: (1) evidence_ids for every core claim; (2) cross-validation against Truth Graph/ERP where applicable; (3) a Reasoning artifact documenting inference steps.
- The Coordinator enforces transitions and records the promotion event and responsible agents.

Core Components & Contracts
---------------------------
- Coordinator Agent (AI Orchestrator): Intake, context resolution, agent activation, merge, gating (see AI_COORDINATOR_SPECIFICATION.md).
- Knowledge Hub: stores embeddings, document indexes and retrieval interfaces. Exposes `retrieve(query, project_id, top_k)`.
- Truth Graph: canonical entity-relationship store for facts and links. Exposes graph queries and fact-validation APIs.
- Enterprise Memory: long-term validated artifacts (decisions, approved reports, lessons learned).
- Document Intelligence: OCR, classification, extraction pipelines producing Information artifacts with `evidence_id` and `extracted_fields`.

Artifact Metadata Contract (every artifact)
------------------------------------------
- `artifact_id` (uuid)
- `type` (document|extract|kpi|recommendation|decision|simulation)
- `canonical_project_id` (nullable)
- `source` (system|human|agent name)
- `source_id` (original id in source system)
- `evidence_ids` (array)
- `confidence` (0-100)
- `provenance` (list of processing steps with timestamps and versions)
- `truth_status` (unverified | verified | contradicted)

Quality Gates and Thresholds
---------------------------
- Executive Quality Score (EQA): numeric 0–100 (see EXECUTIVE_REASONING_STANDARD.md). Minimum release threshold: 90.
- Promotion rules:
  - Reasoning → Recommendation: EQA >= 90 and evidence_coverage >= 0.75 (75%).
  - Recommendation → Action (auto): EQA >= 95, Business Value > defined threshold, and explicit policy permit_auto_action = true.

Operational Modes
-----------------
- Synchronous: low-latency info retrieval and simple recommendations; must be conservative and include clear disclaimers.
- Asynchronous: heavy reasoning, simulations, and batch enrichment — run in background with tracked job IDs.

Security, Privacy & Retention
----------------------------
- PII redaction policy enforced at Document Intelligence stage; raw data stored but access-controlled.
- Enterprise Memory retention and deletion policies defined in Enterprise Learning Standard.

Audit & Explainability
----------------------
- Every final output includes an `evidence_bundle` and a human-readable `chain_of_reasoning` with step-level links to artifacts in Knowledge Hub / Truth Graph.
- All agent decisions are logged with `agent_id`, `inputs`, `outputs`, and `metrics` to allow offline review and forensic analysis.

Appendix: Minimal artifact example
---------------------------------
{
  "artifact_id": "uuid-...",
  "type": "recommendation",
  "canonical_project_id": "proj-123",
  "source": "ExecutiveAgent",
  "evidence_ids": ["doc-123", "kpi-456"],
  "confidence": 92,
  "provenance": [{"step":"extract","agent":"DocumentIntelligence","ts":"..."}, {"step":"reason","agent":"EngineeringAgent","ts":"..."}],
  "truth_status": "verified"
}
