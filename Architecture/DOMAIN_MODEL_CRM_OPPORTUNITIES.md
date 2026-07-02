# Modelo de Dominio Canónico — CRM + Opportunities

Fecha: 2026-06-29

Propósito
--------
Formalizar el lenguaje del negocio (Ubiquitous Language), los bounded contexts y el modelo de dominio conceptual para `CRM` y `Opportunities`. Este documento es PRE‑CONTRACTUAL: aquí definimos entidades, agregados, relaciones, ownership y eventos conceptuales — sin OpenAPI ni contratos técnicos.

1) Aclaración de Dominio (obligatorio)
------------------------------------

Entidades principales
- **Account** (empresa/cliente): `account_id`, `name`, `industry`, `segment`, `status`, `hierarchy_parent_account_id`, `owner_user_id`, `created_at`.
- **Contact** (persona): `contact_id`, `account_id`, `full_name`, `email`, `phone`, `role`, `influence_level`, `is_decision_maker`.
- **Activity** (registro inmutable de interacción): `activity_id`, `type` (call/email/meeting/note/system), `timestamp`, `subject`, `outcome`, `account_id`, `contact_id`, `user_id`.
- **Opportunity** (hipótesis de ingreso, aggregate root de pipeline): `opportunity_id`, `account_id`, `name`, `value{amount,currency}`, `stage_id`, `probability`, `expected_close_date`, `status`, `source`, `owner_user_id`.
- **Stage** (valor/lookup del pipeline): `stage_id`, `name`, `order`, `probability_weight`, `is_closed_won`, `is_closed_lost`.
- **Forecast** (entidad derivada): `forecast_id`, `opportunity_id`, `period`, `expected_value`, `confidence_score`.
- **Offer / Quote** (si aplica dentro de Opportunity): `offer_id`, `opportunity_id`, `lines`, `total`, `status`, `approved_at`.
- **Attachment / Document**: referencias a documentos y su metadata (owner: Document Store / owning module).
- **User / SalesRep**: identidad humana vinculada a ownership y acciones.

Agregados (Aggregates) y raíces
- **Account Aggregate (root = Account)**: contiene la información canónica de la cuenta; `Contact` puede modelarse como entidad interna al agregado o como agregado propio dependiendo del volumen y necesidades operativas. Recomendación: tratar `Contact` como entidad dentro de `Account` para coherencia en cambios de contacto; sin embargo, si el sistema maneja millones de contactos, considerar `Contact` como agregado separado con `account_id` como referencia.
- **Activity Aggregate (root = Activity)**: alto volumen, append-only/immutable; owned por CRM, referencia a `Account` y `Contact`.
- **Opportunity Aggregate (root = Opportunity)**: contiene ofertas (Offer/Quote) como entidades hijas; stage es un value object o referencia a catálogo de stages.
- **Forecast**: derivado (preferiblemente materializado por BI/Forecasting service), no parte interna mutable del agregado Opportunity.

Relaciones clave
- `Account 1:N Contact`
- `Account 1:N Activity`
- `Account 1:N Opportunity` (cross-context reference)
- `Contact N:M Opportunity` (contactos involucrados en decisiones)
- `Activity` ↔ `Opportunity` (Vínculo: actividad puede referenciar `opportunity_id` o inferirse mediante reglas de correlación)

Ownership de datos
- `Account` — owner: **CRM**
- `Contact` — owner: **CRM**
- `Activity` — owner: **CRM**
- `Opportunity` — owner: **Opportunities**
- `Stage` — owner: **Opportunities** (catalog management)
- `Forecast` — owner: **Opportunities** (logical owner) / materialized by **BI**
- `Offer/Quote` — owner: **Opportunities**
- `Document/Attachment` — owner: **Document Store** (referenciado por modules)

Eventos conceptuales (business events — no técnicos)
- `AccountCreated` — significado: una nueva cuenta empresarial ha sido registrada. Emite: **CRM**. Consumidores: **Opportunities**, **Sales Intelligence**, **BI**, sincronizadores externos.
- `AccountUpdated` — significado: cambios en datos de cuenta (segment, owner, status). Emite: **CRM**. Consumidores: cualquier módulo que cachee o enriquezca cuentas.
- `ContactAdded` / `ContactUpdated` — Emite: **CRM**. Consumidores: **Opportunities**, **Sales Intelligence**.
- `ActivityLogged` — significado: se registró interacción con la cuenta/contacto. Emite: **CRM**. Consumidores: **Opportunities** (inferencia sobre probabilidad/stage), **Sales Intelligence** (señales), **Notifications**, **BI**.
- `OpportunityCreated` — Emite: **Opportunities**. Consumidores: **CRM** (referencial), **BI**, **Sales Intelligence**, **Notification**.
- `OpportunityStageChanged` — Emite: **Opportunities**. Consumidores: **Sales Intelligence**, **BI**, **Forecasting**, **Notifications**.
- `OpportunityWon` / `OpportunityLost` — Emite: **Opportunities**. Consumidores: **Finance**, **CRM**, **BI**, **AfterSales**.
- `OfferIssued` / `OfferApproved` — Emite: **Opportunities**. Consumidores: **Finance**, **CRM**, **Notifications**.
- Eventos de inteligencia cruzada (emitidos por Sales Intelligence / Agents): `AccountEngagementIncreased`, `OpportunityRiskDetected`, `SalesVelocityChanged` — Consumidores: **SalesOps**, **Opportunities**, **BI**, **Notifications**.

Reglas de dominio (resumen)
- Actividad (`Activity`) es append-only e inmutable.
- CRM no calcula ingresos ni probabilidades (regla arquitectónica).
- Opportunities no modifican entidades propietarias del CRM; interactúan por lectura o eventos.
- Cada entidad tiene un único módulo propietario responsable de las escrituras.

2) Definición de Bounded Contexts
---------------------------------

CRM Context (Customer Relationship Context) — límites y responsabilidades
- Responsabilidad principal: Identidad del cliente, contactos, registro de actividades, histórico de interacción, segmentación básica y registro de notas.
- Invariantes: actividades registradas son fuente de verdad; `Account` es el anchor para identidad empresarial.
- API pública (conceptual): cree/actualice cuentas, liste contactos, registre actividades, busque historial.
- No contiene lógica de pipeline, probabilidad ni forecasting.

Opportunities Context (Revenue / Pipeline Context)
- Responsabilidad principal: creación y gestión de oportunidades, cálculo de probabilidades, pipeline, ofertas, y coordinación con Finanzas/ERP al cierre.
- Invariantes: ownership de la hipótesis de ingreso (Opportunity); todas las decisiones de cierre y forecast se realizan aquí.
- Consumo de CRM: read-only via events (replicación eventual) o queries a API de CRM para datos en tiempo real cuando sea estrictamente necesario (anti-corruption layer si hay mismatch semántico).

Shared vs Owned entities
- Shared: Identifiers (AccountID, ContactID), Attachments references, Tags, basic timestamps and audit metadata.
- Owned:
  - CRM owns: `Account`, `Contact`, `Activity`.
  - Opportunities owns: `Opportunity`, `Stage`, `Offer`, `Forecast` (logical owner).

Context Map (relación entre contextos)
- CRM publishes events (publish‑subscribe) → Opportunities subscribes (Conformist/Upstream: CRM).
- Pattern recomendado: **CRM = Source of Truth** for identity; Opportunities keeps local read model (materialized view) para operaciones de pipeline.
- Anti-Corruption Layer (ACL): si Opportunities requiere un modelo semántico distinto, introducir un adaptador que transforme y valide datos antes de usarlos.

3) Modelo de Eventos (conceptual)
---------------------------------

Lista de eventos 'business‑level' y comportamiento esperado

- `AccountCreated` — meaning: nueva cuenta; emitted by: **CRM**; consumed by: **Opportunities**; side effects: crear read model en Opportunities, iniciar onboarding workflows.

- `AccountUpdated` — meaning: cambios en atributos clave; emitted by: **CRM**; consumed by: **Opportunities**, **SI**, **BI**.

- `ContactAdded` / `ContactUpdated` — meaning: nuevo contacto o cambio; emitted by: **CRM**; consumed by: **Opportunities**, **SI**.

- `ActivityLogged` — meaning: interacción registrada; emitted by: **CRM**; consumed by: **Opportunities** (heurísticas de impacto en probability/stage), **SI**, **BI**, **Notification**.

- `OpportunityCreated` — meaning: se inicia una hipótesis de venta; emitted by: **Opportunities**; consumed by: **CRM**, **BI**, **SI**, **Notifications**.

- `OpportunityStageChanged` — meaning: movimiento en pipeline; emitted by: **Opportunities**; consumed by: **SI**, **BI**, **Forecasting**, **Notifications**.

- `OpportunityWon` / `OpportunityLost` — meaning: cierre de la oportunidad; emitted by: **Opportunities**; consumed by: **Finance**, **CRM**, **AfterSales**, **BI**, **SI**.

- `OfferIssued` / `OfferApproved` — meaning: oferta emitida/aceptada; emitted by: **Opportunities**; consumed by: **Finance**, **CRM**.

- `AccountEngagementIncreased` — meaning: señal de engagement fuerte; emitted by: **Sales Intelligence / Agent**; consumed by: **Opportunities**, **SalesOps**, **Notifications**.

- `OpportunityRiskDetected` — meaning: IA detecta riesgo; emitted by: **Sales Intelligence / Agent**; consumed by: **Opportunity Owner**, **SalesOps**, **Notifications**.

Principios para el modelo de eventos (conceptual)
- Nombres en lenguaje de negocio (Ubiquitous Language) antes que nombres técnicos.
- Cada evento tiene un único owner/emisor.
- Los consumidores reaccionan; si necesitan cambio autoritativo, llaman a la API del owner.
- Mantener eventos pequeños y referenciar por id a artefactos pesados.

Checklist de aceptación (qué validar antes de avanzar a contratos técnicos)
- Owners de cada entidad claramente asignados.
- Agregados y límites de consistencia definidos.
- Eventos de negocio y responsables definidos.
- Regla arquitectónica principal aprobada (CRM no calcula ingresos).

Siguientes pasos propuestos (después de aprobación)
1. Formalizar Ubiquitous Language (glosario corto) y Context Map visual.
2. Definir read models y materialized views necesarias en Opportunities para performance.
3. Diseñar contratos de eventos (payloads, versiones) y OpenAPI solo tras aprobación del modelo.

Decisión temporal
-----------------
No generar OpenAPI ni contratos técnicos hasta tener sign‑off del modelo anterior y del Context Map.

Fin del documento
