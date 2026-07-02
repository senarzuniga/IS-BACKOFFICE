# Canonical Data Model — Adaptive Sales Engine

Entities (owner):
- Account (CRM)
- Contact (CRM)
- Product (Product Catalog)
- Opportunity (Opportunities)
- Offer (Offers)
- Sale (Finance)
- Document (Document Store)
- KnowledgeItem (Sales Intelligence / Knowledge Graph)
- SimulationScenario / SimulationResult (Simulation Module)

Rules:
- Single source of truth per entity. Owner module handles writes.
- Events for state propagation.
