REPORT GENERATION STANDARD
==========================

Version: 1.0
Purpose: Define the canonical report generation pipeline required for all executive outputs. Enforces consistent steps, evidence flows and quality gates.

Canonical Pipeline (every report)
--------------------------------
1. Request
   - Intake of the requester intent and scope. Produce `request_id` and initial metadata.

2. Intent Detection
   - Natural language intent classification and slot-filling (project_id, timeframe, decision_type).

3. Context Resolution
   - Resolve company, canonical_project_id, permissions, relevant time window.

4. Enterprise Memory
   - Retrieve prior validated decisions and related lessons for the project/organization.

5. Knowledge Hub
   - Semantic retrieval (embeddings + metadata) of relevant documents and extracts.

6. Truth Graph
   - Pull canonical entities and persisted relationships relevant to the query.

7. ERP Data
   - Query transactional and financial records as required.

8. Document Analysis
   - Run Document Intelligence to extract structured fields and evidence IDs.

9. Cross Validation
   - Validate claims against Truth Graph, ERP and primary sources. Produce `fact_check_report`.

10. Reasoning
    - Activate domain agents to analyze data, run simulations, and construct options.

11. Executive Draft
    - Assemble top-line draft with observation, finding, options and recommended_action. Attach evidence bundle.

12. Executive Review
    - Human and Quality Reviewer checks. Compute EQA.

13. Evidence Validation
    - Final validation of evidence links and provenance. Mark `truth_status`.

14. Executive Quality Score
    - Aggregate metrics and compute EQA.

15. Auto Improvement Loop
    - If EQA < threshold, run Self Improvement Engine (SIE) and iterate.

16. Final Report
    - Publish versioned report to repository and Enterprise Memory; notify owners.

Step-level Responsibilities
-------------------------
- Intent Detection: Intent Detector + Coordinator
- Knowledge Hub retrievals: Knowledge Hub Agent
- Document Analysis: Document Intelligence Agent
- Cross Validation: Fact Checker + Truth Graph Agent
- Reasoning: domain-specific agents (Finance, Engineering, Project Management, Simulation)
- Drafting: Executive Agent
- Review & scoring: Quality Reviewer + Executive Reviewer
- Publication: Reporting Agent + Memory Agent

Required Metadata on every report
-------------------------------
- `report_id`, `request_id`, `created_by`, `created_at`, `canonical_project_id`, `version`.
- `evidence_bundle` (list of artifact references with extraction_confidence and processing_version).
- `executive_quality_score` and per-metric breakdown.
- `trace_log` linking coordinator events and agent calls.

Release Policy
--------------
- Minimum release EQA: 90. Reports below threshold are not published to the executive distribution list.
- Exceptions: in emergencies a human Executive Reviewer may approve lower-EQA reports; this is logged and requires explicit justification.

Output Publication Policy
-------------------------
- Agents must never write directly into `reports/<project>/final/`.
- Each agent writes into its own isolated workspace, e.g. `reports/<project>/workspaces/<agent_name>/`.
- Only the `report_publisher_agent` can write into `reports/<project>/final/`.
- Publisher requirements per target file:
   - Acquire lock file.
   - Retry lock acquisition every 500 ms.
   - Maximum 20 retries.
   - If still locked, generate warning and continue remaining publish tasks.
   - Verify source checksum (and expected checksum when provided).
   - Replace target atomically.
   - Release lock.

Reference implementation
------------------------
- `tools/report_publication_guard.py`
- `tools/report_publisher_agent.py`
- `tools/report_publish_manifest.example.json`

Automation & Jobs
-----------------
- Long-running reasoning and simulation tasks run as async jobs with job_ids. Partial results can be returned with transparency about completeness.

Testing & Validation
--------------------
- Unit tests for retrievals (precision@k), extraction (F1), fact checking (contradiction detection), reasoning (sanity checks), and report rendering.
- Integration tests that exercise the entire pipeline for sample requests and validate EQA computation.

Appendix: Minimal report JSON skeleton
-------------------------------------
{
  "report_id":"uuid-...",
  "request_id":"uuid-...",
  "canonical_project_id":"proj-...",
  "title":"...",
  "observation":"...",
  "finding":"...",
  "recommended_action":"...",
  "evidence_bundle":[{"artifact_id":"doc-...","extraction_confidence":0.94}],
  "executive_quality_score":92,
  "trace_log":[{"event":"...","ts":"..."}]
}
