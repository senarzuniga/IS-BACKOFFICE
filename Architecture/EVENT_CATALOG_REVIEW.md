# Event Catalog Review

Fecha: 2026-06-30
Revisor: GitHub Copilot (GPT-5 mini)

Resumen ejecutivo
------------------
El catálogo es una base sólida: sigue la convención de nombres propuesta y cubre Business/Analytical/AI events de forma clara. Sin embargo, antes de avanzar a la Fase 2 (definición de payloads y contratos técnicos) hay varias clarificaciones y decisiones de gobernanza que son necesarias. Recomiendo aprobar el catálogo como documento conceptual (Fase 1) pero BLOQUEAR la generación de payloads y OpenAPI hasta que se resuelvan los puntos listados abajo.

Hallazgos clave
---------------
- **Nombres duplicados / inconsistencia:** El ítem `ActivityLogged` aparece referido como `com.ingecart.activity.logged` y `com.ingecart.crm.activity.logged`. Esto crea ambigüedad sobre quién emite la versión "canónica" y cuál es el tópico SoR. (Ver sección SECCIÓN A — item 4 en [Architecture/EVENT_CATALOG.md](Architecture/EVENT_CATALOG.md)).
- **Propietario ambiguo en eventos analíticos:** Varias entradas de la Sección B muestran propietarios mixtos como `Analytics / EventCore`. Cada evento debe tener un único `owner` (responsable autoritativo) para firmar su esquema y compatibilidad.
- **Falta de reglas explícitas de particionado/orden:** El catálogo recomienda particionar por aggregate cuando hace falta (ej. `opportunity_id`) pero no exige que cada evento declare su `recommended_partition_key` ni si debe incluir `sequence` numbers para ordering strong-consistency.
- **Idempotencia y de-dup no prescriptivos:** Hay recomendaciones generales (proveer tokens de idempotencia) pero no hay un mínimo obligatorio (e.g., `event_id` UUID, `origin_command_id`) ni un patrón de TTL/dedupe en EventCore.
- **Versionado insuficientemente formalizado:** `schema_version` está indicado en el envelope, pero faltan reglas operativas: formato (semver vs integer), estrategia de `major` breaking changes, ventanas de deprecación y roll-out plan.
- **EventCore mutation policy poco clara:** El documento indica que Event/Activity Core canonicaliza y repubblica, pero no define si puede mutar el payload original o debe publicar eventos derivados con `provenance` apuntando al evento origen.
- **Privacidad / PII en AI events:** Las reglas para `evidence` y `model_version` están bien pero falta una política explícita sobre PII, retención y anonimización antes de publicar AI-derived events.
- **Eventos de ciclo de vida faltantes:** Hay referencias a compensaciones (`opportunity.reopened`) pero el catálogo no registra explícitamente esos eventos de reversión/compensación ni eventos de eliminación (`account.deleted`, `contact.deleted`).

Bloqueantes antes de Fase 2 (payloads)
--------------------------------------
Estos asuntos deben resolverse antes de que los equipos empiecen a codificar esquemas/payloads:

- **Consolidar nombres y convención canónica** (Activity duplication). Owner: CRM + EventCore.
- **Asignar owner único por evento**, especialmente para eventos analíticos y AI. Owner: domain teams + Architecture.
- **Definir per-event partition key y ordering semantics** (ej. `partition_key=opportunity_id`, `sequence` incremental por aggregate). Owner: Platform/Architecture.
- **Definir envelope mínimo obligatorio** (campo mínimo del mensaje que todos los productores deben incluir). Ejemplo mínimo recomendado en la checklist (ver más abajo). Owner: Platform.
- **Acuerdo operativo sobre versionado y deprecación** (formato semver vs major int, windows de despliegue). Owner: Architecture / Release Managers.
- **Idempotency & dedupe policy** (event_id requirement, origin_command_id, EventCore dedupe algorithm and TTL). Owner: Platform + EventCore.
- **PII / evidence policy para AI/Analytical events** (redacción/anonymization, retention). Owner: Legal / DPO.

Recomendaciones y próximos pasos (acciones concretas)
-------------------------------------------------
- **1) Resolver naming collisions (urgent).** Reemplazar la entrada dual de ActivityLogged por la convención SoR: `com.ingecart.crm.activity.logged` como evento SoR; EventCore republicará `com.ingecart.activity.enriched` o `com.ingecart.activity.canonicalized` como evento derivado. (Owners: CRM, EventCore).
- **2) Añadir por cada evento los metadatos operativos mínimos:** `owner`, `recommended_partition_key`, `ordering_required: boolean`, `ordering_strategy: sequence|timestamp`, `idempotency_recommendation`. (Owner: Architecture).
- **3) Definir envelope mínimo (Phase 1 → must-have before Phase 2):** acuerden un conjunto pequeño y obligatorio (no payload fields):
  - `event_id` (UUID, producer-generated)
  - `schema_version` (semver or major int — decide)
  - `occurred_at` (ISO8601 UTC)
  - `producer` (service id)
  - `aggregate_id` or `partition_key` (optional, but required when ordering matters)
  - `derived` (bool)
  - `provenance` (list of source event ids) — required for derived events
  - `origin_command_id` (optional but recommended for idempotency)

- **4) Formalizar versioning policy.** Decide semver or major-only policy, deprecation window, and how to indicate breaking vs additive changes. (Owner: Architecture / Governance).
- **5) EventCore rules:** Specify that EventCore SHOULD NOT mutate original SoR events in-place; it MUST publish derived events with provenance metadata and explicit `derived=true`. Define dedupe and fingerprint algorithm and ownership for the canonicalized event.
- **6) Add lifecycle/compensation events to catalog.** E.g., `com.ingecart.opportunities.opportunity.reopened`, `com.ingecart.account.deleted`, `com.ingecart.contact.deleted` at minimum. (Owners: Domain teams).
- **7) Privacy & evidence rules for AI events.** Add mandatory `pii_handling` guidance for events containing `evidence_ids` and `evidence` payloads. (Owners: Legal/DPO).

Pequeñas mejoras / no bloqueantes
--------------------------------
- Añadir una columna/tabla visible por evento que indique el `owner contact` (team + slack/email) y el `SLA de entrega` objetivo para consumidores críticos.
- Añadir ejemplos de patterns operativos: how to handle late-arriving events, replays and backfills (applies to Analytics and EventCore).
- Separar claramente `Analytical` vs `AI Inference` en el documento, y enumerar qué campos de `provenance` son obligatorios para que los consumidores confíen en el resultado.

Fragmento de edición sugerida (ActivityLogged)
---------------------------------------------
Reemplace la entrada actual 4) por el bloque sugerido a continuación (texto propuesto):

```
4) `com.ingecart.crm.activity.logged` — ActivityLogged (SoR)
- Categoría: Business Event
- Significado: Un registro de interacción (call, meeting, email, demo, note) ha sido creado en el SoR CRM.
- Bounded Context propietario: `CRM` (SoR del evento)
- Aggregate raíz: `Activity` (referencia: `account_id` / `contact_id`)
- Cuándo se emite: Al registrar una interacción en CRM (commit exitoso).
- Quién puede emitirlo: CRM UI/API, ingestion pipelines, mobile apps.
- Quién puede consumirlo: `Event/Activity Core` (canonicalization), `Opportunities`, `Sales Intelligence`, `BI`, `Notifications`.
- Garantías: Delivery: at-least-once. Producers MUST include `event_id` (UUID) and an optional `origin_command_id` to enable idempotency. EventCore will dedupe by fingerprint and republish derived events.
- Política EventCore: EventCore MUST NOT mutate the original SoR topic. EventCore MUST publish derived/enriched events as new topics (`com.ingecart.activity.enriched`) with `provenance` referencing original `event_id`.
```

Aceptación para avanzar a Fase 2 (checklist mínima)
-------------------------------------------------
- [ ] Todos los nombres ambiguos han sido consolidados y documentados.
- [ ] Owner único asignado por cada evento (incluyendo Analytical/AI).
- [ ] Envelope mínimo documentado y aprobado.
- [ ] Particionado/ordering definido para eventos donde sea crítico.
- [ ] Versioning policy y deprecation windows aprobadas.
- [ ] PII & evidence handling policy aprobada para AI events.

Recomendación final
--------------------
Estado propuesto: **Aprobar conceptualmente (Fase 1)** y **BLOQUEAR** el inicio de Fase 2 (generación de payloads/OpenAPI) hasta que se completen y verifiquen los items bloqueantes listados arriba. Una vez resueltos, pasar a Fase 2 con un sprint corto para generar payloads v1 por evento (con owners firmando los esquemas).

Si desea, puedo:
- Generar un diff propuesto directamente en `Architecture/EVENT_CATALOG.md` para aplicar las ediciones sugeridas (solo texto, sin payloads).
- Crear una tabla CSV con todos los eventos actuales y columnas vacías (`owner`, `partition_key`, `ordering_required`, `notes`) para que los equipos la rellenen.
