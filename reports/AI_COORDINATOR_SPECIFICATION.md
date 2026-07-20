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
11. API & Contracts
-------------------
- Coordinator API (examples):
   - POST /api/coordinator/requests -> Accepts `CoordinatorRequest`, returns `response_id` and `status` (queued|running|completed|failed).
   - GET /api/coordinator/requests/{response_id} -> Returns `CoordinatorResponse` when completed or current status/progress.
   - POST /api/coordinator/requests/{response_id}/cancel -> Attempts to cancel running subtasks.
   - GET /api/coordinator/requests/{response_id}/evidence -> Returns `evidence_bundle` or signed storage references.
   - Transport: JSON over HTTPS (REST) with optional gRPC interface for high-throughput internal integrations.

11.1 Example Request / Response
- Example `CoordinatorRequest`:
   ```
   {
      "request_id": "uuid-1234",
      "requester_id": "user:alice@example.com",
      "scope": {"company_id":"acme"},
      "intent": "Compare Q2 vendor pricing for component X",
      "urgency":"medium",
      "privacy_constraints":{"pii":false},
      "evidence_required": true
   }
   ```
- Example `CoordinatorResponse` (trimmed):
   ```
   {
      "response_id":"resp-5678",
      "merged_answer": { "summary": "...", "recommendation": "..." },
      "evidence_bundle":["artifact-1","artifact-2"],
      "agent_reports": { "agent-price-scraper":"ok", "agent-aggregator":"ok" },
      "executive_quality_score": 92,
      "acceptability": "accepted",
      "trace_log": [ ... ]
   }
   ```

12. Artifact / Evidence Schema
-----------------------------
- Canonical artifact contract:
   - `artifact_id` (uuid)
   - `type` (document|claim|table|dataset|screenshot|url)
   - `content_ref` (signed storage reference or inline payload)
   - `source` (url or system id)
   - `provenance` (agent_id, agent_version, call_payload_hash)
   - `timestamp` (ISO8601)
   - `evidence_confidence` (0-100)
   - `evidence_hash` (sha256)
   - `access_control` (ACL or scope)

13. Agent Registry Schema
------------------------
- Agent descriptor:
   - `agent_id`
   - `capabilities` (list of capability tags)
   - `endpoint` (internal URL / queue topic)
   - `version`
   - `owner`
   - `weight` (default merge weight)
   - `sla` (expected latency)
   - `privacy_flags` (PII_handling, allowed_scopes)

14. Observability & Tracing
---------------------------
- Metrics to emit:
   - `coordinator.request.count`, `coordinator.request.latency`
   - `coordinator.eqa.histogram`, `coordinator.acceptability.count`
   - `agent.invocations.count`, `agent.latency` per `agent_id`
   - `factcheck.failures`, `contradiction.count`
- Tracing:
   - Use `request_id` as the root trace id. Propagate as `coordinator_trace_id`.
   - Emit structured trace events for each agent call (start/end/status).

15. Security, Privacy & Compliance
---------------------------------
- Enforce `privacy_constraints` at intake. Reject or redact queries that violate policy.
- Data access checks: verify `requester_id` permissions against `scope`.
- Store PII-containing artifacts with stricter ACLs and shorter retention by default.
- All transport must use TLS; evidence storage should support envelope encryption and server-side encryption with keys rotated and audited.

16. Testing & Validation
-----------------------
- Unit tests:
   - EQA computation, weighting and normalization logic.
   - Contract serialization/deserialization.
- Integration tests:
   - End-to-end with mock agents (happy path, timeouts, partial failures).
   - Fact-checker integration with injected truth graph responses.
- Load tests:
   - Validate coordinator under fan-out workloads and heavy agent latencies.
- Acceptance criteria:
   - E2E flows return `accepted` for known-good datasets; `escalate_to_human` on authoritative contradictions.

17. Deployment & Scaling
-----------------------
- Design coordinator as stateless service with persistent backing:
   - Queue (Kafka/Rabbit) for subtasks
   - Durable Enterprise Memory for evidence and trace logs
   - Object store for artifact content
- Scaling:
   - Horizontal scale for coordinator instances behind load balancer
   - Per-request concurrency limits and back-pressure to avoid flood of agents

18. Example Workflows
---------------------
- Competitive Intelligence (parallel fan-out):
1. Intake intent → select web-scraper, aggregator, risk-assessor agents.
2. Launch agents in parallel with 30s budget.
3. Merge results, run fact-check, compute EQA.
4. If EQA < 90, run Self-Improver to attempt one iteration.

- Document Summarization + Fact-check (sequential):
1. DocumentIntelligence extracts claims.
2. Facts forwarded to FactChecker in batch.
3. KnowledgeHub reconciles references, then Coordinator synthesizes executive summary.

19. Open Issues & Next Steps
---------------------------
- Implement `CoordinatorRequest` REST endpoints and queue integration.
- Build EQA scoring library and publish config defaults.
- Implement Agent Registry with minimal admin UI.
- Create mock-agent harness for integration testing.
- Define SLA and operational runbooks for escalations.

20. Coordinator ↔ Platform Registry Integration
---------------------------------------------
- Purpose: Allow the Coordinator to resolve required capabilities without knowing implementation details. The Coordinator must only operate in terms of capability names and metadata.
- Implementation: a lightweight client library is bundled in the repository at `platform_registry/client.py` exposing `PlatformRegistryClient`.
- Responsibilities of the Coordinator:
   - Use `PlatformRegistryClient.resolve_capability_from_intent(intent_text)` to obtain candidate capabilities for an incoming intent.
   - Query `PlatformRegistryClient.find_objects_by_capability(capability)` to retrieve implementations (agents, engines, workbenches) and their metadata.
   - Dispatch subtasks to selected implementations by referencing their `path`/`endpoint` and by applying policies (owner, SLA, weight).

- Example pseudocode:
   ```python
   from platform_registry.client import PlatformRegistryClient

   client = PlatformRegistryClient()

   # 1. Resolve capabilities from intent
   candidates = client.resolve_capability_from_intent(intent_text)

   # 2. Select top capability and implementations
   best_cap = candidates[0]['capability']
   implementations = client.find_objects_by_capability(best_cap)

   # 3. Coordinator dispatches to implementation (by path/endpoint)
   for impl in implementations[:3]:
         # map impl['path'] -> actual endpoint or agent_id via Agent Registry
         dispatch_subtask(impl)
   ```

Note: The `PlatformRegistryClient` is intentionally minimal; production deployments should implement robust resolution logic, trust/weighting, and permission checks.

Appendix: References
- EXECUTIVE_REASONING_STANDARD.md — weighting defaults and per-metric definitions.
- Truth Graph API — internal doc for fact verification endpoints.
