AI COORDINATOR SPECIFICATION
============================

Version: 1.0
Purpose: Specification for the Coordinator Agent (AI Orchestrator). The Coordinator is the platform's governor for multi-agent workflows: it never answers using its own domain knowledge, only orchestrates specialized agents, merges outputs, enforces quality gates and produces auditable results.

1. Contract: Inputs & Outputs
- Input (CoordinatorRequest):
  - `request_id` (uuid)
  - `requester_id` (user or system)
  - `scope` (company_id, canonical_project_id?)
  - `intent` (raw text + optional structured intent)
  - `urgency` (low|medium|high)
  - `privacy_constraints` (PII flags, do_not_query_sources[])
  - `evidence_required` (boolean)

- Output (CoordinatorResponse):
  - `response_id` (uuid)
  - `merged_answer` (structured content)
  - `evidence_bundle` (list of artifact_ids)
  - `agent_reports` (map agent_id -> agent_output)
  - `executive_quality_score` (0-100)
  - `acceptability` (accepted|needs_improvement|escalate_to_human)
  - `trace_log` (ordered events with timestamps)

2. High-level Flow
------------------
1. Intake & Intent Detection
   - Normalize request and run intent detection.
2. Context Resolution
   - Resolve `company`, `canonical_project_id`, permissions, data access, and relevant time window.
3. Determine Expert Agents
   - Mapping from intent → list of specialized agents (from Agent Registry). Decide concurrency model (parallel/serial).
4. Launch Agents
   - Dispatch subtasks with context, required evidence template, and time budget. Use async jobs for long runs.
5. Collect & Normalize
   - Standardize agent outputs to canonical artifact contract and record evidence_ids.
6. Merge & Reconcile
   - Weighted-merge outputs using agent confidence, source reliability, and Truth Graph verification.
7. Fact-check
   - Invoke Fact Checker on core claims; annotate contradictions.
8. Self-evaluate & Score
   - Run Quality Reviewer to compute Executive Quality Score (EQA).
9. Decide Acceptability
   - If EQA >= 90 and no hard contradictions -> `accepted`.
   - If 70 <= EQA < 90 -> run Self Improvement Agent for auto-iteration.
   - If EQA < 70 or contradictions on authoritative facts -> escalate to Executive Reviewer (human).
10. Publish Response
   - Produce CoordinatorResponse, store evidence bundle and trace_log in Enterprise Memory if validated.

3. Agent Activation Patterns
- Parallel fan-out: for discovery-style queries (Competitive Intelligence, Document retrieval).
- Sequential pipeline: for workflows requiring staged outputs (DocumentIntelligence -> KnowledgeHub -> Reasoning).
- Hybrid: run low-latency agents first to form a seed, then heavy agents (Simulation) in background.

4. Merging Strategy
- Normalization: each agent output converted to canonical schema.
- Weighting: score_claim = sum(agent_confidence * agent_weight * source_reliability) / normalization.
- Contradiction detection: facts with opposing verified truth_status are flagged and cause downgrade or escalate.

5. Fact Checking
- Primary checks: Truth Graph lookup, ERP reconciliation, direct source retrieval.
- Outcomes: pass | inconclusive | fail. Fails tag the claim and add required remediation steps.

6. Executive Quality Score (EQA) — computed by Coordinator
- Inputs: per-metric scores (Evidence Coverage, Fact Consistency, Source Reliability, Data Freshness, Reasoning Quality, Business Value, Executive Readability, Actionability, Traceability, Confidence).
- Aggregation: weighted average (defaults provided in EXECUTIVE_REASONING_STANDARD.md).

7. Error Handling & Escalation
- Timeouts: if some agents time out, Coordinator returns partial results with `acceptability = needs_improvement`.
- Contradictions: Coordinator can request additional evidence or escalate to human reviewer.

8. Audit & Traceability
- Trace log contains: agent_id, call_payload_hash, start_ts, end_ts, output_reference, evidence_ids.
- All Coordinator decisions stored in Enterprise Memory with `coordinator_request_id` for future audits.

9. Security & Access Control
- Coordinator enforces `privacy_constraints` and query whitelists per request.

10. Implementation Notes
- Agent Registry: dynamic registry with capability descriptors, version and owner.
- Idempotency: coordinator operations must be idempotent; use `request_id` to deduplicate.
- Configurable policies: EQA thresholds, agent_weights and allowed auto-action policies are stored in platform config and audited.
