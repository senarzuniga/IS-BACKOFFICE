SELF IMPROVEMENT ENGINE
=======================

Version: 1.0
Purpose: Define the automated internal critique and iterative improvement process that upgrades drafts until they meet Executive Quality thresholds or are escalated for human review.

Overview
--------
The Self Improvement Engine (SIE) is a controlled iterative loop that runs after initial drafts are produced. It combines rule-based checks, targeted retrievals, re-synthesis, and replayed fact-checks to improve quality.

Core Components
- Internal Critic: rule-based and model-based checks (consistency, missing evidence, contradiction detection).
- Gap Detector: queries Knowledge Hub and Truth Graph for missing evidence and conflicting facts.
- Suggestion Generator: produces concrete edits, re-rankings, alternative recommendations.
- Iteration Controller: manages iteration limits, rate-limits, and convergence checks.
- Versioning Recorder: records each draft version, diffs, and EQA history into Enterprise Memory.

Iteration Flow
--------------
1. Input: draft (executive_draft), fact_check_report, quality_report.
2. Internal critique: run rule-based validators (missing evidence, readability, assumption checks).
3. Gap detection: retrieve supporting evidence candidates from Knowledge Hub and Truth Graph.
4. Generate improvements: apply transformations (add evidence links, reword, quantify impacts, propose alternatives).
5. Re-run Fact Checker and Quality Reviewer.
6. If EQA >= threshold → return improved draft.
7. Else repeat up to `max_iterations`.

Parameters & Safety
- Default `max_iterations`: 3 (configurable per request type).
- Auto-approval threshold after SIE: EQA >= 90.
- Human escalation: if after `max_iterations` EQA < 90 or contradictions remain, escalate to Executive Reviewer.

Metadata & Storage
- For each iteration store: `iteration_id`, `parent_draft_id`, `changes_summary`, `evidence_added`, `time_spent`, `EQA_after_iteration`.
- All iteration logs persisted in Enterprise Memory for audit and learning.

Rules & Constraints
- SIE must never remove primary-source evidence; it can only add or re-classify supporting evidence.
- SIE suggestions must reference new or existing `evidence_ids` — no hallucinated claims allowed.
- Any aggressive change that increases risk (financial/operational) triggers human gating.

Evaluation & Metrics
- iterations_to_convergence
- improvement_delta (EQA difference)
- average_time_per_iteration
- % of auto-resolved drafts (EQA >= 90)

Extensibility
- Plug in domain-specific critic modules (FinanceCritic, LegalCritic) to apply stricter domain rules.
