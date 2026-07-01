# Agent Dependency Map

Date: 2026-06-29

Purpose
- Visualize dependencies between agents and platform services to prevent cycles and to plan deployment order.

Dependencies (graph edges)
- agent.web_research.v1 -> HTTP/Scraper
- agent.knowledge_builder.v1 -> agent.web_research.v1
- agent.knowledge_builder.v1 -> Knowledge Graph
- agent.market_intel.v1 -> agent.web_research.v1
- agent.market_intel.v1 -> agent.knowledge_builder.v1
- agent.analyst.v1 -> Knowledge Graph
- agent.analyst.v1 -> LLM Provider
- agent.report_writer.v1 -> LLM Provider
- agent.simulator.reel.v1 -> Simulation Engine
- agent.validation.v1 -> test harness, Knowledge Graph
- agent.recommender.price.v1 -> Historic Sales DB, Pricing Engine
- agent.kpi_agent.v1 -> EventBus, Data Warehouse
- agent.executive_summary.v1 -> KPI DB, LLM Provider

Recommended deployment order
1. Infrastructure adapters: HTTP/Scraper, Knowledge Graph, Vector DB
2. Ingest agents: agent.web_research.v1
3. Knowledge builders: agent.knowledge_builder.v1
4. Recommenders and analysts: agent.market_intel.v1, agent.analyst.v1
5. Writers and reports: agent.report_writer.v1, agent.executive_summary.v1
6. Validators and KPI agents: agent.validation.v1, agent.kpi_agent.v1

Notes
- Avoid cycles: agents should not depend on artifacts produced by agents that in turn depend on them.
- All agent dependencies must be declared in `AGENT_REGISTRY.md`.
