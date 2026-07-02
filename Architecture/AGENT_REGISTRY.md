# Agent Registry — Adaptive Sales Engine

This registry catalogs all AI agents, their category, owner, inputs, outputs, maturity and dependencies. Every agent must be registered here before merge.

Schema (per entry)
- id: string
- name: string
- category: Ingest|Research|Analysis|Recommender|Writer|Simulator|Orchestrator
- owner: team or module
- inputs: list of events or API inputs
- outputs: events or artifacts
- endpoint: sync/async invocation URL or method
- dependencies: services/agents
- maturity: draft|experimental|production
- tests: links to unit/integration tests

Starter entries

- id: agent.web_research.v1
  name: Web Research Agent
  category: Ingest
  owner: Sales Intelligence
  inputs: research_plan (API), triggers from scheduler
  outputs: raw_pages, snippets -> Knowledge Builder
  endpoint: ai-orch.trigger('web_research')
  dependencies: SmartScraper, HTTP
  maturity: production

- id: agent.knowledge_builder.v1
  name: Knowledge Builder
  category: Analysis
  owner: Sales Intelligence
  inputs: raw_pages, snippets
  outputs: KnowledgeItem -> Knowledge Graph
  endpoint: ai-orch.trigger('knowledge_builder')
  dependencies: Knowledge Graph, Vector DB
  maturity: experimental

- id: agent.market_intel.v1
  name: Market Intelligence
  category: Recommender
  owner: Competitive Intelligence
  inputs: company_name, seeds
  outputs: profile JSON, benchmark
  endpoint: ai-orch.trigger('market_intel')
  dependencies: web_research, knowledge_builder
  maturity: production

Consolidation note: consolidate duplicate extraction agents into `agent.web_research` with config profiles.
