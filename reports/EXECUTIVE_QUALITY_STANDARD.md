EXECUTIVE QUALITY STANDARD

Purpose
-------
Define the policy, metrics and evaluation pipeline that guarantee executive outputs (reports, recommendations) meet a high bar of evidence, traceability and confidence before being presented to decision makers.

Executive Quality Pipeline (mandatory)
-------------------------------------
1. Context Resolution (project scope, timeframe)
2. Knowledge Retrieval (ranked documents + structured data)
3. Evidence Ranking (score by provenance, recency, confidence)
4. Truth Graph Validation (check against canonical facts)
5. Fact Checking (numeric reconciliation, cross-source agreement)
6. Draft Generation (Report Writer Agent) with explicit `evidence_ids`
7. Executive Reviewer / Quality Evaluator computes `Executive Quality Score`
8. If score >= 0.9 publish; else iterate with improved evidence or human-assisted steps

Executive Quality Score (example components & weights)
- Evidence Coverage (30%): percent of claims backed by at least one verified evidence node
- Evidence Confidence (20%): average confidence of evidence items
- Fact-Check Pass Rate (20%): fraction of numeric/boolean claims validated against Truth Graph/ERP
- Provenance Quality (10%): proportion of evidence from authoritative sources (ERP, certified documents)
- Human Validation (10%): binary approval or partial remediation
- Freshness & Completeness (10%): recency of evidence and completeness of key sections

Report requirements
- Every claim must include `evidence_ids` linking to document nodes and relevant graph edges.
- Include an `AI Reasoning Summary` describing steps taken, search queries, and filters.
- Provide `Confidence` per section and overall `Executive Quality Score`.
- Include `Last updated` timestamp and `Author` (agent id or user id).

Fact-checking rules
- Numeric claims (totals, budgets, forecasts) must be reconciled with ERP snapshots where available.
- Acceptance criteria for reconciled numbers: difference <= threshold % (configurable per KPI).

Human-in-the-loop
- Any report failing to reach the `Minimum Executive Quality Score` must be reviewed by a human expert before publication.
- Human reviewers can flag evidence as `validated` or `rejected`; system should record reviewer id and timestamp.

Storage & audit
- Save draft versions, evaluation logs and final published artifacts in `report_versions` table (see services/project_closeout_reporter.py pattern).

Output Control Policy
- All non-publisher agents must write only to isolated workspaces.
- Final publication directory `reports/<project>/final/` is reserved for `report_publisher_agent`.
- Publication flow must enforce lock acquisition, checksum verification, atomic replace, and lock release.
- Lock retry policy: every 500 ms, maximum 20 retries, warning on exhaustion, continue remaining tasks.

Integration points in repo
- Report generator: [backoffice/reporting/generator.py](backoffice/reporting/generator.py)
- Closeout report versions: [services/project_closeout_reporter.py](services/project_closeout_reporter.py)
- KnowledgeMemory & orchestrator patterns: agents/knowledge_intelligence and backoffice/agents/orchestrator.py

Acceptance criteria
- All auto-generated executive reports must include evidence and a computed `Executive Quality Score`.
- System must prevent publishing reports with score < 0.9 unless explicit override with audit trail.
- System must prevent non-publisher writes into `reports/<project>/final/`.
