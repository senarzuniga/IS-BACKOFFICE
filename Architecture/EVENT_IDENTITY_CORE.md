# Event & Identity Core — Diseño Arquitectónico

Fecha: 2026-06-29

Propósito
--------
Formalizar el **Event/Activity Core** como bounded context de primera clase y definir el **Canonical Identity Model**. Este documento es la base operativa y semántica para poder derivar contratos técnicos y OpenAPI tras la aprobación. No contiene payloads técnicos; solo reglas, flujos y criterios de aceptación.

Principios básicos
- El Event/Activity Core es un pilar transversal: normaliza, canoniza, enriquece y entrega eventos y vistas materializadas. No sustituye a los System of Record (SoR).
- SoR mantienen la autoridad de escritura sobre sus entidades (ej.: `CRM` es SoR para `Account`, `Contact`, `Activity` del origen de captura; `Opportunities` es SoR para `Opportunity`).
- Separación clara entre: Business Events (autoritativos), Analytical Events (derivados), AI Signals (inferidos). Cada clase tiene reglas de emisión y consumo.

Alcance y límites
- Incluye:
  - Ingesta y normalización de eventos y activities
  - Resolución canónica de identidad (Account/Contact/User)
  - Deduplicación y fingerprinting
  - Enriquecimiento (geolocal, firm/segmentation, embeddings opcionales en KG)
  - Clasificación (event taxonomy) y ruteo a consumidores
  - Persistencia de raw events y transformaciones (lineage)
  - Materialized read models (Activity timeline, Identity map, Recent activities)
- Excluye:
  - Lógica de negocio propietaria (pipeline, probability, pricing) — permanece en SoR
  - Persistencia primaria de entidades de negocio (seguida por SoR)

Responsabilidades del Event/Activity Core
- Garantizar un timeline canónico de interactions (`Activity Timeline`).
- Mantener un `Identity Map` que enlaza `canonical_id` con `external_ids`.
- Publicar eventos enriquecidos y read models para subscribers (Opportunities, SI, BI).
- Clasificar y etiquetar eventos según Event Taxonomy.
- Exponer evidencia de trazabilidad para cada inferencia (audit trail).

Canonical Identity Model
------------------------
Objetivo: resolver referencias heterogéneas a la misma entidad (Account/Contact/User) y proporcionar `canonical_id` estable.

Estructura mínima del Identity Profile (conceptual)
- `canonical_id` (UUID)
- `entity_type` (Account|Contact|User)
- `canonical_attributes` (name, trusted_email, primary_phone, tax_id, country)
- `external_ids` (list of {source, external_id})
- `confidence_score` (0-1) — si resolución es probabilística
- `created_at`, `resolved_at`, `sources` (list)

Reglas de resolución
- Deterministas first: match por unique keys (tax_id, company_reg_number, email for contacts).
- Fuzzy next: name+domain+location with threshold and explainability (audit evidence).
- Manual reconciliation: cuando `confidence_score` < threshold, crear task para revisión humana.
- Merge policy: la fuente SoR con mayor autoridad (configurable per tenant) determina atributos preferentes; Event Core no reescribe SoR — sólo mantiene mapping y publishes `IdentityResolved` (signal).

Identity lifecycle events (conceptual)
- `IdentityCreated` (Event Core crea canonical mapping)
- `IdentityMerged` (two canonical_ids merged)
- `IdentitySplit` (manual unmerge)
- `IdentityUpdated` (attributes changed after enrichment)

Event Taxonomy (3 capas)
------------------------
1) Business Events (Domain Truth)
  - Emisor: System of Record (SoR)
  - Ejemplos: `AccountCreated`, `ActivityLogged`, `OpportunityCreated`, `OpportunityStageChanged`, `OpportunityWon`
  - Reglas: payloads pequeños, owner único, idempotencia garantizada por originator token, versioning obligatorio.

2) Analytical Events (Derived)
  - Emisor: ETL/Stream processors, Event Core
  - Ejemplos: `DailyActivitySummary`, `SessionAggregated`, `KPIUpdate`
  - Reglas: consumidos por BI/ML; deben incluir link back to origin events (ids).

3) AI Signals (Inferred)
  - Emisor: Agents / AI Orchestrator
  - Ejemplos: `OpportunityRiskDetected`, `AccountEngagementIncreased`
  - Reglas: etiquetado explícito como `derived=true` y `evidence` required (input ids, scorer, model_version). No son authoritative unless a human or SoR action promotes them.

Event envelope (conceptual fields)
- `event_type` (string, business term)
- `schema_version` (semver-like)
- `occurred_at` (iso8601)
- `emitted_by` (service/module)
- `correlation_id` (UUID)
- `causation_id` (UUID)
- `canonical_ids` (list of resolved canonical ids)
- `data_ref` (id reference to heavy artifact stored in object store)
- `provenance` (list of origin event ids)

Activity model (primario en Event Core)
-------------------------------------
Definición: `Activity` = registro append-only de una interacción de negocio. No confundir con `Event` (mensaje técnico).

Campos conceptuales:
- `activity_id`, `canonical_account_id`, `canonical_contact_ids` (0..n), `type` (call|email|meeting|demo|note|system), `channel` (phone|email|web|in_person), `timestamp`, `subject`, `outcome`, `source_system`, `raw_payload_ref`, `fingerprint`.

Propiedades:
- Append-only: no updates rutinarios; correcciones se realizan con compensating activities (tipo note/correction).
- Fingerprint generation: hash(raw_payload + source_id) — usado para dedupe.
- Sequence per account (optional): monotonic ordering to build canonical timeline.

Interpretación y Anti-Corruption Layers (ACL)
--------------------------------------------
Regla: cada bounded context interpreta `Activity` con su propia semántica mediante un ACL.

- CRM ACL: interpreta `Activity` para historial, owner assignment, engagement scoring superficial.
- Opportunities ACL: interpreta `Activity` para triggers de pipeline (ej.: `demo=+stage_probability`) usando mapping rules definidas por Opportunities.

ACL responsibilities
- Transform canonical `Activity` → context-specific Signal
- Maintain mapping config (versioned) and rules as first-class artifacts
- Log mapping decisions and provide revert path

Deduplicación y idempotencia
---------------------------
- Dedup window: configurable (e.g., 5 minutes for real-time, 24h for batch)
- Dedupe key: fingerprint || source_id + origin_ts
- Idempotency token: producers encouraged to include originator token for safe retries

Enriquecimiento pipeline (conceptual)
- Steps: ingest -> normalize -> identity_resolve -> dedupe -> enrich (geo/firmographics/KG) -> classify -> persist -> route
- Enrichment outputs must include `evidence` pointers to source events and enrichment jobs

Read models y vistas materializadas
---------------------------------
- `AccountTimeline` (canonical activities timeline)
- `RecentActivities` (sliding window cache)
- `IdentityMap` (canonical->external mapping)
- `ActivityCountsByType` (for SI signals)

Lineage, auditoría y cumplimiento
-------------------------------
- Mantener raw event store (immutable) con acceso restringido para auditoría.
- Cada transformation debe registrar lineage metadata: `input_event_ids`, `processor_id`, `timestamp`, `output_event_ids`.
- PII rules: mask sensitive fields at enrichment stage and maintain original payload in encrypted store with access controls.

Observabilidad y SLOs
---------------------
- Métricas mínimas: ingestion_latency_p95, events_per_second, identity_resolution_error_rate, dedupe_rate, enrich_failure_rate.
- Alertas: identity_resolution_error_rate > threshold; backpressure in queues; high dedupe rate (possible loop).
- SLO examples: ingestion_latency_p95 < 1s (real-time path), availability 99.9%.

Seguridad
---------
- Producers must be authenticated & authorized to publish. Internal services use mTLS.
- Event signing recommended for non-repudiation.
- Encrypt raw event store at rest.

Governance
----------
- Event Registry: todo nuevo evento debe estar registrado y aprobado (Event owner + ADR if semantics change).
- Agents: deben declarar outputs en `AGENT_REGISTRY.md` y marcar si emiten AI Signals.
- ADRs: cualquier cambio semántico en Identity o Activity model requiere ADR.

Checklist de aceptación (pre-contratos)
-------------------------------------
- [ ] Event/Activity Core definido como bounded context con owner asignado.
- [ ] Canonical Identity Model aprobado (matching rules y thresholds).
- [ ] Event Taxonomy publicada y mapeada a owners.
- [ ] Activity interpretation ACL pattern definido y ejemplo de mapping para CRM y Opportunities.
- [ ] Dedupe & idempotency strategy documentada.
- [ ] Read models listada y responsables asignados.
- [ ] Privacy & retention policies definidas para PII.

Flujo de ejemplo (conceptual)
----------------------------
1. `CRM` crea `Activity` en su SoR → emite `ActivityLogged` (business event).
2. Event Core ingesta el evento, normaliza y ejecuta `identity_resolve`.
3. Dedupe verifica fingerprint; si nuevo, encola enrich job.
4. Enriquecimiento añade firmographics y publica `ActivityEnriched` (analytical) y actualiza `AccountTimeline`.
5. Opportunities ACL suscribe y mapea `ActivityEnriched` → `ConversionSignal` (local mapping). Si threshold supera, Opportunities ejecuta transición de stage y emite `OpportunityStageChanged`.

Próximos pasos tras aprobación
------------------------------
1. Aprobar documento y checklist.
2. Generar contract drafts de eventos Business (payload shapes) y publicar en Schema Registry (drafts).
3. Implementar pruebas de contrato para producers/consumers.

Fin del diseño.
