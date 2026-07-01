# Agent Capability Matrix

Date: 2026-06-29

Purpose
- Map every registered agent to its primary capabilities, inputs, outputs, owner and maturity. This helps prioritization, testing and governance.

Matrix
| Agent ID | Capability(s) | Category | Owner | Inputs | Outputs | Dependencies | Maturity | Notes |
|---|---|---:|---|---|---|---|---|---|
| agent.web_research.v1 | Ingest, Extract | Ingest | Sales Intelligence | research_plan (API), scheduler | raw_pages, snippets | HTTP scraper, DOM parser | production | configurable source profiles |
| agent.knowledge_builder.v1 | Normalize, Enrich, Upsert | Analysis | Sales Intelligence | raw_pages, snippets | KnowledgeItem -> KG | Knowledge Graph, Vector DB, embeddings | experimental | dedup + canonicalization required |
| agent.market_intel.v1 | Profile, Benchmark | Recommender | Competitive Intelligence | company_name, seeds | profile JSON, benchmark | web_research, knowledge_builder | production | integrates external data sources |
| agent.analyst.v1 | Synthesis, Prioritization | Analysis | Sales Intelligence | knowledge_items, signals | recommended_actions, insights | LLMs, KG | draft | used for internal playbooks |
| agent.report_writer.v1 | Summarize, Draft | Writer | Reporting | insights, briefs | report_document, executive_summary | LLMs, formatting templates | experimental | templates + export formats
| agent.simulator.reel.v1 | Simulate, Plan | Simulator | scenario_input, resource_config | simulation_result, metrics | Simulation Engine, plant models | production | Candidate canonical simulator
| agent.validation.v1 | Validate, QA | Orchestrator | artifacts, rules | validation_report | test harness, KG | experimental | used for agent output validation
| agent.recommender.price.v1 | Price Suggestion | Recommender | product_id, opportunity_data | price_suggestion, confidence | Pricing Engine, historic_sales | experimental | supports margin constraints
| agent.kpi_agent.v1 | KPI Calculation | Analysis | events, sales_data | KPI metrics, anomaly alerts | Data Warehouse, ETL | draft | used by BI for dashboards
| agent.executive_summary.v1 | Executive Summary | Writer | insights, KPI snapshots | 1-page executive summary | LLMs, templates | production | audit logs required

How to use this matrix
- Owners must keep `inputs` and `dependencies` current.
- Any new agent must be added here before merge and assigned a maturity level.
