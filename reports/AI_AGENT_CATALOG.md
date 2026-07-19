AI AGENT CATALOG
================

Version: 1.0
Purpose: Canonical description of specialized agents, their responsibilities, interfaces (inputs/outputs), confidence model, required evidence, and KPIs.

Format for each agent:
- Role: short description
- Inputs: required inputs
- Outputs: produced artifacts
- Confidence model: expected confidence output and thresholds
- Required evidence: minimum evidence types to operate
- KPIs: measurable indicators to track

1) Coordinator Agent (Orchestrator)
- Role: Understand requests, resolve context, activate agents, merge results, enforce quality gates.
- Inputs: request object, requester identity, optional `canonical_project_id`.
- Outputs: merged_response (with evidence bundle), Executive Quality Score, action plan.
- Confidence model: reports component-level confidences; Coordinator computes weighted confidence.
- Required evidence: agent outputs, Truth Graph validations, Knowledge Hub retrievals.
- KPIs: time-to-first-draft, merge-accuracy, EQA of produced reports.

2) Executive Agent
- Role: Create CEO-level executive drafts and recommendations across domains.
- Inputs: merged domain outputs, evidence bundle, executive brief.
- Outputs: Executive Draft (Observation, Finding, Recommendation), evidence_ids, confidence.
- Confidence: required >= 85 for top-line recs; always present as 0–100.
- Required evidence: cross-domain KPIs, validated facts, risk assessments.
- KPIs: executive_readability_score, adoption_rate, time-to-decision.

3) Finance Agent
- Role: Financial analysis, cashflow forecasting, variance explanations.
- Inputs: ERP data, project financials, invoices, contracts.
- Outputs: financial_summary, forecast, sensitivity analysis, evidence_ids.
- Confidence: include model confidence and data freshness score.
- Required evidence: ERP transactions, validated invoice documents, contract terms.
- KPIs: forecast_error, evidence_coverage, reconciliation_rate.

4) CFO Agent
- Role: Policy-level recommendations, capital decisions, accounting implications.
- Inputs: outputs from Finance Agent, strategic constraints.
- Outputs: CFO recommendation, regulatory flags, capital impact.
- Confidence: conservative; must flag any assumptions.
- Required evidence: audited financials, compliance rules, board policies.
- KPIs: policy_compliance_score, flagged_issues_rate.

5) Commercial Agent
- Role: Pricing, margins, channel strategy analysis.
- Inputs: sales data, market signals, CI outputs.
- Outputs: commercial_strategy, price_recommendations, evidence_ids.
- KPIs: margin_lift_simulation, recommendation_precision.

6) CGO Agent (Growth/Go-to-Market)
- Role: GTM planning, campaign ROI estimates, expansion playbooks.
- Inputs: commercial outputs, competitive intelligence.
- Outputs: GTM playbooks, KPI targets, confidence.
- KPIs: projected_revenue_lift, ROI_accuracy.

7) Sales Agent
- Role: Opportunity scoring, deal playbooks, churn risk.
- Inputs: CRM data, customer history, competitive signals.
- Outputs: opportunity_score, engagement_plan, evidence_ids.
- KPIs: win_rate_delta, scoring_precision.

8) Engineering Agent
- Role: Technical impact analysis, feasibility, risk and resource estimates.
- Inputs: designs, codebase metrics, project specs.
- Outputs: technical_assessment, resource_requirements, risk_register.
- KPIs: estimation_accuracy, defect_risk_score.

9) Operations Agent
- Role: Operational feasibility, capacity planning, runbook suggestions.
- Inputs: production metrics, SRE signals, resource pools.
- Outputs: ops_plan, alerting_changes, expected_impact.
- KPIs: ops_uptime_impact, recovery_time_estimate_accuracy.

10) Procurement Agent
- Role: Supplier evaluation, procurement timing, cost optimization.
- Inputs: supplier history, POs, contract terms.
- Outputs: supplier_rankings, procurement_plan, negotiation_points.
- KPIs: cost_savings_estimate, supplier_reliability_score.

11) Project Management Agent
- Role: Schedule analysis, milestone risk, resource leveling.
- Inputs: tasks, milestones, dependencies, timesheets.
- Outputs: project_health, schedule_recovery_plan, critical_path.
- KPIs: on_time_delivery_probability, schedule_slippage_index.

12) Knowledge Hub Agent
- Role: Indexing, retrieval, embedding management, semantic search.
- Inputs: documents, extracts, canonical IDs.
- Outputs: ranked_retrievals, embeddings, vector_store_maintenance.
- KPIs: retrieval_precision@k, embedding_refresh_latency.

13) Competitive Intelligence Agent
- Role: Market signals, competitor tracking, opportunity detection.
- Inputs: public sources, scraped content, CI reports.
- Outputs: competitor_profiles, strategic_alerts.
- KPIs: detection_precision, alert_relevance.

14) Simulation Agent
- Role: Run scenario simulations, sensitivity analysis, Monte Carlo runs.
- Inputs: model_spec, parameter_ranges, historical distributions.
- Outputs: simulation_results, probabilistic_outcomes, confidence_intervals.
- KPIs: simulation_accuracy (backtested), runtime.

15) Document Intelligence Agent
- Role: OCR, document classification, structured extraction (invoices, contracts).
- Inputs: document_bytes, document_type_hint.
- Outputs: extracted_fields, evidence_id, extraction_confidence.
- KPIs: extraction_precision, OCR_error_rate.

16) Legal Agent
- Role: Contract risk, compliance checks, clause extraction.
- Inputs: contract_text, regulatory_rules.
- Outputs: legal_risks, required_clauses, next_steps.
- KPIs: clause_detection_rate, false_positive_rate.

17) ERP Agent
- Role: Read/write to ERP canonical tables, reconciliation tasks.
- Inputs: ERP API, canonical_project_id mapping.
- Outputs: transactional writes (POs, invoices), reconciliations, evidence.
- KPIs: reconciliation_accuracy, latency.

18) Reporting Agent
- Role: Render executive reports in agreed templates, manage versions, signatures.
- Inputs: executive_draft, evidence_bundle, EQA.
- Outputs: versioned_report (PDF/HTML/JSON), publication_record.
- KPIs: publish_time, version_rollbacks.

19) Truth Graph Agent
- Role: Maintain and validate canonical entities and relations.
- Inputs: extracts, reconciliations, manual mappings.
- Outputs: verified_nodes, contradictions.
- KPIs: contradiction_resolution_time, node_stability_index.

20) Memory Agent
- Role: Persist validated artifacts into Enterprise Memory; enforce retention and access policies.
- Inputs: validated_decision, lessons, approved_reports.
- Outputs: memory_record_ids.
- KPIs: ingestion_latency, retrieval_success_rate.

21) Fact Checker
- Role: Validate claims against Truth Graph, primary sources and ERP.
- Inputs: claim_bundle, evidence_ids.
- Outputs: fact_check_report (pass|fail|inconclusive), supporting_evidence.
- KPIs: contradiction_detection_precision, fact_check_latency.

22) Executive Reviewer (human)
- Role: Human-in-the-loop review of high-impact recommendations.
- Inputs: executive_draft, fact_check_report, EQA.
- Outputs: approval|rework_instructions.
- KPIs: review_time, approval_rate.

23) Quality Reviewer (human/agent)
- Role: Apply Executive Quality Score rubric and check readability and traceability.
- Inputs: draft_report, evidence_bundle.
- Outputs: quality_report, required_changes.
- KPIs: EQA_accuracy, turnaround_time.

24) Self Improvement Agent
- Role: Run internal critique and iterate on outputs until quality thresholds met.
- Inputs: draft_report, quality_report, fact_check_report.
- Outputs: improved_draft_versions, iteration_log.
- KPIs: iterations_to_convergence, improvement_delta.

Notes
-----
- Every agent must emit `evidence_ids` and `confidence` with every claim.
- Agents are registered in a central Agent Registry with capability descriptors, version, and owner contact.
