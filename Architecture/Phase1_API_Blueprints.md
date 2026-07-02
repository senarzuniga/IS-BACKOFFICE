# Phase 1 API Blueprints — CRM + Opportunities

This file provides concise OpenAPI-style blueprints and event schema examples for Phase 1 migration: CRM and Opportunities modules.

CRM API (minimal blueprint)

POST /crm/accounts
Request:
{
  "name": "string",
  "external_id": "string",
  "address": { "line1": "", "city": "", "country": "" },
  "owner_id": "string"
}

Response: 201 Created
{
  "id": "uuid",
  "name": "string",
  "external_id": "string"
}

Events emitted:
- account.created
  payload:
  {
    "account_id": "uuid",
    "name": "string",
    "external_id": "string",
    "timestamp": "iso8601"
  }

Opportunities API (minimal blueprint)

POST /opportunities
Request:
{
  "title": "string",
  "account_id": "uuid",
  "value": { "currency": "EUR", "amount": 10000 },
  "stage": "lead",
  "owner_id": "string",
  "close_date": "YYYY-MM-DD"
}

Response: 201 Created
{
  "id": "uuid",
  "title": "string",
  "account_id": "uuid"
}

Events emitted:
- opportunity.created
  payload:
  {
    "opportunity_id": "uuid",
    "account_id": "uuid",
    "stage": "string",
    "value": { "amount": 0, "currency": "EUR" },
    "timestamp": "iso8601"
  }

- opportunity.updated
  payload similar plus `changes` map.

Event schema notes
- Use namespaced event types: `com.ingecart.crm.account.created`.
- Include `schema_version` in events.
- Maintain small payloads and link to full artifacts by id.

Contract testing
- For each event producer, publish a consumer contract (pact or similar).

Security
- All APIs authenticated via Core Auth (JWT/OIDC). Services must use mTLS inside cluster for internal calls.

Backwards compatibility
- Events must be versioned; consumers should tolerate unknown fields.
