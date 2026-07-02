# Event Catalog — Canonical Event Registry

Fecha: 2026-06-29
Estado: Draft — cambios arquitectónicos aplicados; pendiente aprobación final

Propósito
--------
Catálogo canónico de eventos para la plataforma. Este documento actúa como la "fuente de verdad" para el Event Bus y describe, por evento, su clasificación, significado de negocio, metadatos estructurales y reglas de versionado. NO define payloads técnicos (estos se harán en la Fase 2 tras aprobación).

Principios y convenciones (resumen)
- Nombres canónicos: com.ingecart.<context>.<entity>.<action> (ej.: com.ingecart.crm.account.created).
- Ownership: reemplazamos el campo único `owner` por una sección de ownership estructurada (ver Metadatos por evento). No se asignan valores de ownership en esta versión — esos se definirán en la fase de asignación de equipos.
- Ordering: el catálogo indica la necesidad y el alcance del ordering (`Ordering Scope`) — no prescribe mecanismos de infraestructura (p. ej. partition keys, Kafka, Event Hubs). La implementación del mecanismo queda en la capa de infraestructura.
- Versionado: usar `schema_version` en el envelope; cambios incompatibles deben indicar un incremento mayor y seguir el playbook de migración.
- Compatibilidad: los cambios compatibles (añadir campos opcionales) son permitidos; renombrar o eliminar campos requiere nueva versión mayor y plan de migración.
- Entrega: el bus garantiza at-least-once; los productores deben incluir `event_id` y, cuando correspondan, `origin_command_id` para facilitar idempotencia. Los consumidores deben diseñar idempotencia y reconciliación.

Event category matrix

| Category | Changes business state | Persistent | Emitted by |
|---|---:|---:|---|
| Business Event | Sí / puede | Sí | SoR (domain owner)
| Analytical Event | No | Opcional | Event Core / Analytics
| AI Inference Event | No | Opcional | AI Orchestrator / Agents
| Integration Event | Depende | Sí | Integration adapters
| System Event | No | No | Infra / platform services

Metadatos por evento (campos estándar)
- `catalog_id` (EV-<context>-NNN): Identificador canónico y permanente del evento en el catálogo.
- `ownership` (estructura):
	- `domain_owner`: equipo de dominio (ej. CRM, Opportunities) — asignado en fase posterior.
	- `technical_owner`: equipo técnico responsable de la emisión/integración.
	- `data_steward` (opcional): responsable de calidad/semántica de datos.
- `ordering_scope`: Describe la necesidad/alcance de orden. Valores posibles: `None` | `EntityScoped` | `Global`.
- `lifecycle`: Estado del evento en catálogo: `Draft` | `Approved` | `Deprecated` | `Retired`.
- `criticality`: Negocio: `Critical` | `Important` | `Normal` | `Informational`.
- `quality_level`: Madurez: `Experimental` | `Internal` | `Stable` | `LTS`.
- `notes`: campo libre para consideraciones por evento.

Envelope mínimo obligatorio (sin payloads)
Todos los eventos emitidos en la plataforma deben incluir al menos los siguientes campos en el envelope (no confundir con el payload de negocio):
- `event_id` (UUID, producer-generated)
- `catalog_id` (EV-<context>-NNN) — referencia al catálogo
- `schema_version` (formato acordado: semver o major-int — decidir en gobernanza)
- `occurred_at` (ISO8601 UTC)
- `producer` (service id)
- `derived` (bool) — true para eventos generados por pipelines/enrichers
- `provenance` (array de event_id) — obligatorio para eventos derivados
- `origin_command_id` (opcional pero recomendado) — correlación para idempotencia

Nota operativa: información como contactos de owners, SLAs, runbooks y canales de soporte NO forman parte del catálogo canónico; se documentarán en un **Operations Catalog / Runbooks** separado.

Cómo leer este catálogo
- Para cada evento listamos: `catalog_id`, Nombre canónico, Categoría, Significado funcional, Ownership (placeholders), Aggregate raíz, Ordering Scope, Cuándo se emite, Productores posibles, Consumidores esperados, Garantías (delivery / idempotencia / orden), Lifecycle, Criticality, Quality Level y Reglas de compatibilidad. No se incluyen payloads en Fase 1.

---------------------------------

SECCIÓN A — Business Events (catálogo principal)

1) `com.ingecart.crm.account.created` — AccountCreated
- `catalog_id`: EV-CRM-001
- Categoría: Business Event
- Ownership:
	- Domain Owner: TBD
	- Technical Owner: TBD
	- Data Steward: TBD
- Aggregate raíz: `Account`
- Ordering Scope: None
- Lifecycle: Draft
- Criticality: TBD
- Quality Level: TBD
- Significado: Se ha creado una nueva `Account` en el CRM (registro oficial de la organización cliente).
- Cuándo se emite: Tras la confirmación de creación de cuenta en el SoR (commit exitoso; API response 201).
- Quién puede emitirlo: `CRM` service, import batch jobs, sync adapters (tras validación de no-duplicado).
- Quién puede consumirlo: `Opportunities` (crear referencia), `Sales Intelligence`, `BI`, Integraciones externas (ERP sync), Event Core for identity consolidation.
- Garantías: Delivery: at-least-once. Consumers must be idempotent; include `account_external_id` or `command_id` for idempotency. No strict ordering required across different accounts.
- Versionado / Reglas de compatibilidad: Incremental via `schema_version`; breaking change => new major version and deprecation plan.

2) `com.ingecart.crm.account.updated` — AccountUpdated
- `catalog_id`: EV-CRM-002
- Categoría: Business Event
- Ownership:
	- Domain Owner: TBD
	- Technical Owner: TBD
	- Data Steward: TBD
- Aggregate raíz: `Account`
- Ordering Scope: EntityScoped
- Lifecycle: Draft
- Criticality: TBD
- Quality Level: TBD
- Significado: Atributos clave de una `Account` han cambiado (segmento, owner, status, etc.).
- Cuándo se emite: Tras commit de update en SoR, si el cambio excede umbral de relevancia (configurable).
- Quién puede emitirlo: `CRM` service, integration adapters (cuando actualizan datos desde fuente externa autorizada).
- Quién puede consumirlo: `Opportunities`, `Sales Intelligence`, `BI`, Integraciones.
- Garantías: at-least-once. Consumers should use `account_id` + `updated_at` to reconcile. Consider event version and sequence when ordering matters.

3) `com.ingecart.crm.contact.created` — ContactCreated
- `catalog_id`: EV-CRM-003
- Categoría: Business Event
- Ownership:
	- Domain Owner: TBD
	- Technical Owner: TBD
	- Data Steward: TBD
- Aggregate raíz: `Contact` (referencia a `account_id`)
- Ordering Scope: EntityScoped
- Lifecycle: Draft
- Criticality: TBD
- Quality Level: TBD
- Significado: Se ha creado un nuevo `Contact` asociado a una `Account`.
- Cuándo se emite: Tras creación en CRM.
- Productores: CRM service, import processes.
- Consumidores: `Opportunities` (participantes de decision), `Sales Intelligence`, `Notifications`.
- Garantías: at-least-once; consumers idempotent via `contact_id`.

4) `com.ingecart.crm.activity.logged` — ActivityLogged (SoR)
- `catalog_id`: EV-CRM-004
- Categoría: Business Event
- Ownership:
	- Domain Owner: TBD
	- Technical Owner: TBD
	- Data Steward: TBD
- Aggregate raíz: `Activity` (referencia: `account_id` / `contact_id`)
- Ordering Scope: EntityScoped
- Lifecycle: Draft
- Criticality: TBD
- Quality Level: TBD
- Significado: Un registro de interacción (call, meeting, email, demo, note) ha sido creado en el SoR CRM.
- Cuándo se emite: Al registrar una interacción en CRM (commit exitoso).
- Quién puede emitirlo: CRM UI/API, ingestion pipelines, mobile apps.
- Quién puede consumirlo: `Event/Activity Core` (canonicalization), `Opportunities`, `Sales Intelligence`, `BI`, `Notifications`.
- Garantías: at-least-once; producers MUST include `activity_id` (UUID) and an optional `origin_command_id` para idempotencia. EventCore dedupe by fingerprint and republish derived events.
- Política EventCore: EventCore MUST NOT mutate the original SoR topic. EventCore MUST publish derived/enriched events as new topics (ej.: `com.ingecart.activity.enriched`) con `provenance` referenciando el `event_id` original.

5) `com.ingecart.opportunities.opportunity.created` — OpportunityCreated
- `catalog_id`: EV-OPP-001
- Categoría: Business Event
- Ownership:
	- Domain Owner: TBD
	- Technical Owner: TBD
	- Data Steward: TBD
- Aggregate raíz: `Opportunity`
- Ordering Scope: None
- Lifecycle: Draft
- Criticality: TBD
- Quality Level: TBD
- Significado: Se ha creado una nueva `Opportunity` (hipótesis de ingreso) en el contexto `Opportunities`.
- Cuándo se emite: Tras persistir la nueva Opportunity en el SoR.
- Quién puede emitirlo: `Opportunities` service (UI, automation, integrations), sales reps tools.
- Quién puede consumirlo: `CRM`, `BI`, `Sales Intelligence`, `Forecasting`, `Notifications`, `Finance`.
- Garantías: at-least-once; include `opportunity_id` and `origin_command_id` for idempotency. Consumers should tolerate duplicate events.

6) `com.ingecart.opportunities.opportunity.stage_changed` — OpportunityStageChanged
- `catalog_id`: EV-OPP-002
- Categoría: Business Event
- Ownership:
	- Domain Owner: TBD
	- Technical Owner: TBD
	- Data Steward: TBD
- Aggregate raíz: `Opportunity`
- Ordering Scope: EntityScoped
- Lifecycle: Draft
- Criticality: TBD
- Quality Level: TBD
- Significado: Cambio de `stage` en un `Opportunity` (movimiento en el pipeline).
- Cuándo se emite: Tras commit de la transición de stage en SoR (manual o automática).
- Quién puede emitirlo: `Opportunities` service, automation rules (workflow engine).
- Quién puede consumirlo: `Sales Intelligence`, `BI`, `Forecasting`, `Notifications`, `Event Core` for lineage.
- Garantías: at-least-once; ordering is important per opportunity — consumers should process stage changes en orden. Implement sequence handling at producer level cuando sea necesario.

7) `com.ingecart.opportunities.opportunity.won` — OpportunityWon
- `catalog_id`: EV-OPP-003
- Categoría: Business Event
- Ownership:
	- Domain Owner: TBD
	- Technical Owner: TBD
	- Data Steward: TBD
- Aggregate raíz: `Opportunity`
- Ordering Scope: EntityScoped
- Lifecycle: Draft
- Criticality: TBD
- Quality Level: TBD
- Significado: Oportunidad marcada como ganada; desencadena downstream financial & after-sales processes.
- Cuándo se emite: Tras confirmación de cierre (win) en SoR, posiblemente tras approval workflow.
- Quién puede emitirlo: `Opportunities` service, approval workflows.
- Quién puede consumirlo: `Finance`, `CRM`, `AfterSales`, `BI`, `ERP Adapter`, `Reporting`.
- Garantías: at-least-once; consumers must be idempotent; ensure finality (no subsequent state reversal except via compensating `opportunity.reopened` event which must ser explícito).

8) `com.ingecart.opportunities.opportunity.lost` — OpportunityLost
- `catalog_id`: EV-OPP-004
- Categoría: Business Event
- Ownership:
	- Domain Owner: TBD
	- Technical Owner: TBD
	- Data Steward: TBD
- Aggregate raíz: `Opportunity`
- Ordering Scope: EntityScoped
- Lifecycle: Draft
- Criticality: TBD
- Quality Level: TBD
- Significado: Oportunidad marcada como perdida.
- Cuándo se emite: Tras cierre como lost in SoR.
- Quién puede emitirlo: `Opportunities` service.
- Quién puede consumirlo: `CRM`, `BI`, `Sales Intelligence`, `Reporting`.
- Garantías: at-least-once; idempotency via `opportunity_id`.

---------------------------------

SECCIÓN B — Analytical Events (derived / phase 3)

Nota: Estos eventos son derivados por el Event/Activity Core o pipelines analíticos. No modifican el estado de dominio autoritativo.

1) `com.ingecart.identity.resolved` — IdentityResolved
- `catalog_id`: EV-ANL-001
- Categoría: Analytical Event
- Ownership:
	- Domain Owner: Event/Activity Core (TBD)
	- Technical Owner: TBD
	- Data Steward: TBD
- Ordering Scope: None
- Lifecycle: Draft
- Criticality: TBD
- Quality Level: TBD
- Significado: Event Core ha resuelto/creado mapping canónico entre `external_ids` y `canonical_id`.
- Emisor: EventCore
- Consumidores: `Opportunities`, `Sales Intelligence`, `BI`, Integrations
- Garantías: at-least-once; must include evidence and confidence_score.

2) `com.ingecart.activity.enriched` — ActivityEnriched
- `catalog_id`: EV-ANL-002
- Categoría: Analytical Event
- Ownership:
	- Domain Owner: Event/Activity Core (TBD)
	- Technical Owner: TBD
	- Data Steward: TBD
- Ordering Scope: None
- Lifecycle: Draft
- Criticality: TBD
- Quality Level: TBD
- Significado: Activity normalizada y enriquecida (firmographics, geo, KG links, embeddings optional).
- Emisor: EventCore enrich processors
- Consumidores: `Opportunities`, `Sales Intelligence`, `BI`, Agents
- Garantías: at-least-once; include provenance to original ActivityLogged ids.

3) `com.ingecart.analytics.engagement_score_calculated` — EngagementScoreCalculated
- `catalog_id`: EV-ANL-003
- Categoría: Analytical Event
- Ownership: TBD
- Ordering Scope: None
- Lifecycle: Draft
- Criticality: TBD
- Quality Level: TBD
- Significado: Score calculado de engagement para una Account/Contact en window.
- Consumidores: `SalesOps`, `Opportunities`, `Notifications`

4) `com.ingecart.analytics.opportunity.risk_detected` — OpportunityRiskDetected
- `catalog_id`: EV-ANL-004
- Categoría: Analytical Event
- Ownership: TBD
- Ordering Scope: None
- Lifecycle: Draft
- Criticality: TBD
- Quality Level: TBD
- Significado: Señal de riesgo calculada sobre una Opportunity.
- Emisor: `Sales Intelligence` / `EventCore`

5) `com.ingecart.analytics.sales_velocity_calculated` — SalesVelocityCalculated
- `catalog_id`: EV-ANL-005
- Categoría: Analytical Event
- Ownership: TBD
- Ordering Scope: None
- Lifecycle: Draft
- Criticality: TBD
- Quality Level: TBD

---------------------------------

SECCIÓN C — AI Inference Events (phase 4)

Nota: AI Events deben estar claramente etiquetados como `derived=true` y contener `evidence` (input ids, model_version, confidence). Además deben documentar tratamiento de PII y retención.

1) `com.ingecart.ai.recommendation.generated` — RecommendationGenerated
- `catalog_id`: EV-AI-001
- Categoría: AI Inference Event
- Ownership: TBD
- Ordering Scope: None
- Lifecycle: Draft
- Criticality: TBD
- Quality Level: Experimental
- Emisor: AI Orchestrator / Agents
- Consumidores: `Opportunities`, UI, Notifications

2) `com.ingecart.ai.next_best_action.proposed` — NextBestActionProposed
- `catalog_id`: EV-AI-002
- Categoría: AI Inference Event
- Ownership: TBD
- Ordering Scope: None
- Lifecycle: Draft
- Criticality: TBD
- Quality Level: Experimental

3) `com.ingecart.ai.opportunity.summary_generated` — OpportunitySummaryGenerated
- `catalog_id`: EV-AI-003
- Categoría: AI Inference Event
- Ownership: TBD
- Ordering Scope: None
- Lifecycle: Draft
- Criticality: TBD
- Quality Level: Experimental

4) `com.ingecart.ai.customer.intent_detected` — CustomerIntentDetected
- `catalog_id`: EV-AI-004
- Categoría: AI Inference Event
- Ownership: TBD
- Ordering Scope: None
- Lifecycle: Draft
- Criticality: TBD
- Quality Level: Experimental

Reglas generales para AI events
- Todos deben incluir: `evidence_ids`, `model_version`, `confidence_score`, `derived=true`.
- No deben actuar como authoritative commands; solo humanos/SoR pueden promover un AI signal a una acción autoritativa.

Governance: Registro y aprobación
- Todo nuevo evento debe registrarse en este catálogo con `catalog_id` y una propuesta de esquema.
- Los cambios semánticos requieren ADR y comunicación a equipos consumidores.
- El Event Core será responsable de publicar read models y versiones derivadas (enriquecidas) y de mantener lineage y `provenance`.

Checklist pre-condición para pasar a Fase 2 (payloads)
- [ ] Nombres ambiguos consolidados (ActivityLogged, etc.).
- [ ] Ownership estructurado definido por evento (Domain/Technical/Data Steward) — asignación en fase posterior.
- [ ] Envelope mínimo documentado y aprobado.
- [ ] Ordering Scope definido para eventos ordering-sensitive.
- [ ] Versioning policy y deprecation windows aprobadas.
- [ ] PII & evidence handling policy aprobada para AI events.

Compensaciones y eventos del ciclo de vida
- El catálogo incluye explícitamente eventos de ciclo de vida y compensación cuando proceda (ejemplos a añadir): `reopened`, `deleted`, `archived`, `restored`, `merged`, `split`, `superseded`.

Fin del Catálogo.
