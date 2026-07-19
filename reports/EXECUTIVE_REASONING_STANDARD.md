EXECUTIVE REASONING STANDARD
===========================

Version: 1.0
Purpose: Uniform template and scoring rubric for executive reasoning, recommendations and decision support. Ensures readability, traceability and measurable quality for CEO/COO/CFO/CGO decisions.

1. Output Template (required for every executive output)
- `report_id` (uuid)
- `canonical_project_id` (nullable)
- `title` (one-line executive summary)
- `observation` (what we observed; 1–2 sentences)
- `finding` (concise synthesis of the observation)
- `evidence_ids` (list of artifact ids supporting each claim)
- `analysis` (structured reasoning steps, numbered)
- `options` (1..n recommended options with cost/benefit)
- `recommended_action` (single preferred action with justification)
- `decision_required` (who must approve, by when)
- `impacts` (financial, operational, strategic — each with estimate)
- `assumptions` (explicit list)
- `measurement_plan` (how to track outcome)
- `confidence` (0–100)
- `executive_quality_score` (0–100)

2. Decision Support Classification (stamp each recommendation)
- Observation | Finding | Risk | Opportunity | Recommendation | Decision Required
- Tag each recommendation with: `urgency`, `financial_impact`, `operational_impact`, `strategic_impact`, `confidence`.

3. Reasoning Quality Checklist
- Explicit chain-of-evidence: every assertion references `evidence_ids`.
- Alternatives considered: at least 2 alternatives must be listed unless impractical.
- Quantification: numeric impacts or ranges must be provided for material recommendations.
- Assumptions: all assumptions declared and their sensitivity discussed.
- Sources: primary sources preferred; secondary sources must be validated.

4. Executive Quality Score (EQA) — metric definitions
- Evidence Coverage: fraction of core claims with at least one primary-source evidence (0–100).
- Fact Consistency: fraction of claims that pass fact-check against Truth Graph/ERP (0–100).
- Source Reliability: weighted mean reliability score of sources used (0–100).
- Data Freshness: recency score (1 - age/max_age) mapped to 0–100.
- Reasoning Quality: human/agent-rated score for logic completeness (0–100).
- Business Value: estimated value or impact normalized to 0–100.
- Executive Readability: readability and brevity score (0–100).
- Actionability: clarity of next steps and owners (0–100).
- Traceability: ease of finding raw evidence (0–100).
- Confidence: aggregated agent confidence (0–100).

Aggregation
- Default EQA = weighted average with equal weights unless overridden by governance policy. Platform default weights can be configured per report type.
- Minimum release threshold: 90. If EQA < 90 follow Self Improvement loop.

5. Presentation Rules
- Top-line summary: 2–3 sentences.
- One-page executive view: include only observation, finding, recommended_action, impacts, decision_required and EQA.
- Full annex: evidence bundle, chain_of_reasoning, simulation outputs, and data appendices.

6. Traceability & Evidence Packaging
- Every report must include an `evidence_bundle` with direct links to artifacts in Knowledge Hub and Truth Graph.
- Attach extraction confidence and processing version for each evidence item.

7. Escalation & Human Review
- If any claim fails fact-check or EQA < 70, automatically escalate to Executive Reviewer (human) with required remediation steps.

8. Minimal Compliance Checks (pre-publish)
- All claims have `evidence_ids`.
- No hallucinated statements flagged by Fact Checker.
- EQA computed and stored.
- Privacy & PII checks completed.
