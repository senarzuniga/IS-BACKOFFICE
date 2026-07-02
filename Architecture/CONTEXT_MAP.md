# Context Map — CRM, Opportunities, Event/Activity Core

Fecha: 2026-06-29

Descripción
-----------
Mapa visual y textual de las relaciones entre bounded contexts, el Event/Activity Core (pilar transversal), Shared Kernel y adaptadores (Anti-Corruption Layers).

Mermaid diagram

```mermaid
graph LR
  subgraph EventCore[Event/Activity Core]
    EV(Event Bus & Activity Normalizer)
    ID(Identity Resolver)
    KG(Knowledge Graph)
  end

  subgraph CRM[CRM Context]
    Account[Account]
    Contact[Contact]
    Activity[Activity]
  end

  subgraph Opp[Opportunities Context]
    Opportunity[Opportunity]
    Stage[Stage]
    Offer[Offer]
  end

  subgraph SI[Sales Intelligence]
    Agents[Agents]
  end

  Account -->|publishes events| EV
  Activity -->|publishes activities as events| EV
  EV -->|enriched events / read models| Opp
  EV -->|enriched events| SI
  ID -->|resolve ids| EV
  Agents -->|write signals| EV
  Opp -->|publish opportunity events| EV
  CRM -->|SoR| Account
  Opp -->|SoR| Opportunity
  subgraph SK[Shared Kernel]
    Currency
    CountryCode
  end
  SK --- CRM
  SK --- Opp

  %% Anti-Corruption Layer
  CRM -- ACL --> Opp
  note right of Opp: Opportunities reads CRM via
  note right of Opp: ACL / materialized views

```

Textual notes
- Flow: CRM emits `ActivityLogged`, `AccountCreated`, `AccountUpdated` into EventCore. EventCore normalizes and enriches, resolves identity and republishes canonical events and read models.
- Opportunities subscribes to enriched events (materialized view) to operate offline on pipeline data.
- Sales Intelligence (agents) subscribe to events and may emit signals (e.g., `OpportunityRiskDetected`) back into EventCore.
- Anti-Corruption Layer: when Opportunities requires different semantics of `Account`, an ACL adapter transforms CRM model into Opportunities' model.

Event Spine / Activity Layer
- Centralizes ingestion of `Activity` records and events.
- Responsibilities: deduplication, enrichment (geolocation, enrichment), identity resolution, persistence of canonical activity timeline.

Ownership summary
- CRM: SoR for Account, Contact, Activity (writes)
- Opportunities: SoR for Opportunity, Offer, Stage
- Event/Activity Core: No write ownership for domain entities; proporciona read models y normalización.

Integration patterns
- Use event envelopes with `schema_version`, `source`, `correlation_id`.
- Prefer eventual consistency; provide sync API for time-critical reads with ACL.

Acceptance
- Context Map and Ubiquitous Language must be approved by owners (CRM, Opportunities) and Chief Architect before generating technical contracts.

Fin.
