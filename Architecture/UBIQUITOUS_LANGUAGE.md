# Ubiquitous Language — CRM, Opportunities y Event/Activity Core

Fecha: 2026-06-29

Propósito
--------
Definir un vocabulario único y no ambiguo para todo el equipo (productos, código, eventos, agentes y documentación). Cada término aquí tiene significado preciso y debe usarse tal cual en APIs, eventos y UI.

Reglas generales
- Un término = un significado. No introducir sinónimo nuevo sin ADR.
- Preferir términos del Ubiquitous Language en nombres de eventos, campos y logs.
- Cambios al vocabulario se registran vía ADR.

Términos clave (definiciones exactas)
- Account — Registro canónico de la organización/empresa (SoR: `CRM`). Identificador: `account_id` (UUID). Uso: identidad empresarial en todas las vistas.
- Customer — Estado comercial; evita usarlo como sustituto de `Account`. `Customer` puede ser el role (ej. "Customer = Account with status=customer").
- Contact — Persona asociada a una `Account`. Identificador: `contact_id`.
- Activity — Registro inmutable y business‑level de interacción (call, meeting, email, note, demo). Owner: `CRM`. Atributos: `activity_id`, `type`, `timestamp`, `outcome`. No confundir con `Event`.
- Event — Mensaje técnico que viaja por el Event/Activity Core (envelope). Representa cambios o señales; puede contener referencias a `Activity` o `Account` por id.
- Opportunity — Hipótesis de ingreso; aggregate root del contexto `Opportunities`. Identificador: `opportunity_id`. Incluye probabilidad, stage y valor esperado. No es un contrato ni una factura.
- Deal / Contract / Sale — Resultado comercial o contrato firmado; distinto de `Opportunity`. Use `Opportunity` hasta cierre; al cierre emita `OpportunityWon` y cree `Sale` o `Contract` (dominio de `Finance`/`ERP`).
- Offer / Quote — Propuesta formal asociada a una `Opportunity` (owner: `Opportunities`).
- Stage — Valor referencial del pipeline (owned by `Opportunities`).
- Forecast — Entidad derivada: estimación calculada a partir de oportunidades (owner lógico: `Opportunities`; materializado por `BI`).
- Identity / Canonical ID — Conjunto de identificadores primarios (`account_id`, `contact_id`, `user_id`) usados para correlación y resolución de identidad.
- System of Record (SoR) — El módulo/servicio que es fuente autoritativa para una entidad (ej.: `CRM` es SoR para `Account`, `Contact`, `Activity`; `Opportunities` es SoR para `Opportunity`, `Offer`).
- Event/Activity Core — Pilar horizontal encargado de: normalizar eventos, resolución de identidad, correlación, deduplicación, enriquecimiento de activities y delivery a consumidores. NO sustituye al SoR.
- Shared Kernel — Pequeño conjunto de modelos/VOs compartidos entre contextos (ej.: tipos de moneda, códigos de país, definiciones inmutables de stage catalog si se comparte).

Distinciones críticas (prohibiciones explicitas)
- `Account` ≠ `Customer` — usar `Account` como entidad canónica.
- `Opportunity` ≠ `Deal` — no usar `Deal` para referirse a pipeline; `Deal` sólo tras cierre/contrato.
- `Activity` ≠ `Event` — `Activity` es el registro de negocio (owner: CRM). `Event` es el mensaje técnico que describe o transporta cambios.

Convenciones de uso
- Nombres de eventos y campos deben usar estos términos (ej.: `AccountCreated`, `ActivityLogged`, `OpportunityStageChanged`).
- Campos de identidad siempre usan sufijo `_id` y UUID (ej.: `account_id`, `contact_id`).
- Evitar homónimos: si un término ya existe en el registro, no crear sinónimo.

Identity resolution (reglas)
- Canonical `account_id` es el identificador preferido para enlazar datos entre contextos.
- External IDs (ERP id, legacy id) se guardan en `external_ids` pero no sustituyen a `account_id`.
- Resolución: la fuente autorizada para consolidación es `CRM` (SoR). El Event/Activity Core puede publicar read‑models enriquecidos para consumo, pero cualquier corrección debe realizarse mediante API del SoR.

System of Record (SoR) summary
- CRM: SoR para `Account`, `Contact`, `Activity` (writes autorizados aquí).
- Opportunities: SoR para `Opportunity`, `Offer`, `Stage`, `Forecast` (lógica de pipeline aquí).
- Document Store: SoR para `Attachment/Document`.
- Event/Activity Core: no es SoR; es el backbone para intercambio, canonicalización y enriquecimiento.

Governance y cambios
- Cualquier cambio semántico al Ubiquitous Language requiere ADR y aprobación de los owners de `CRM` y `Opportunities`.
- Los agentes AI y consumidores deben respetar la semántica y no asumir datos que no sean propiedad del SoR.

Checklist para validar uso correcto
- Cada nueva API, evento o campo debe mapear a un término del Ubiquitous Language.
- Antes de publicar un nuevo evento, verificar que el emisor sea el owner semántico.
- Revisiones periódicas: owner del vocabulario realizará revisión trimestral.

Aceptación
- El vocabulario estará vigente tras la aprobación del Chief Architect y owners de `CRM` y `Opportunities`.

Fin.
