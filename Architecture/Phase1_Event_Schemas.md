# Phase 1 Event Schemas — CRM + Opportunities

Example: `com.ingecart.crm.account.created` (v1)

{
  "event_type": "com.ingecart.crm.account.created",
  "schema_version": "1",
  "occurred_at": "2026-06-29T12:00:00Z",
  "data": {
    "account_id": "uuid",
    "name": "string",
    "external_id": "string",
    "owner_id": "string"
  }
}

Example: `com.ingecart.opportunity.created` (v1)

{
  "event_type": "com.ingecart.opportunity.created",
  "schema_version": "1",
  "occurred_at": "2026-06-29T12:00:00Z",
  "data": {
    "opportunity_id": "uuid",
    "account_id": "uuid",
    "title": "string",
    "stage": "lead",
    "value": { "amount": 10000, "currency": "EUR" }
  }
}

Schema governance
- All events stored in a schema registry (Confluent Schema Registry or equivalent).
- Event producers must register schemas and include `schema_version` in event envelope.

Consumer contract guidance
- Consumers should record the event version they support.
- Backward compatible changes: add optional fields, avoid removing required fields.
