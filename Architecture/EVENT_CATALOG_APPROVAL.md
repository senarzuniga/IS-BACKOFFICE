# Event Catalog — Approval Checklist

Purpose: ensure the canonical `Architecture/EVENT_CATALOG.md` is review-ready and has explicit owner sign-off before any Business Event payloads or contracts are produced.

Acceptance criteria (all must be satisfied):

- **Completeness:** every event listed includes the required attributes: canonical name, category, business meaning, owning bounded context, aggregate root, producer(s), consumer(s), trigger conditions, delivery guarantees, versioning strategy, compatibility rules.
- **Owners:** each event has a named business owner and a technical owner (team/individual) responsible for payload changes.
- **Bounded Context mapping:** each event is mapped to a single owning bounded context and any cross-context consumers are documented with translation/ACL requirements.
- **Delivery semantics:** delivery guarantees (at_least_once / exactly_once / best_effort), idempotency guidance, and correlation keys are explicit.
- **Versioning & compatibility:** strategy for minor/major versions, schema evolution rules and deprecation policy are documented.
- **Privacy & PII:** any sensitive fields are marked and handling rules are documented.
- **Testing gating:** a plan for contract tests (consumer-driven), staging validation, and monitoring (alerting on schema drift) is present.

Review checklist

- [ ] I confirm the event catalog fields are complete and correct.
- [ ] I confirm the owning bounded context and producers/consumers are accurate.
- [ ] I confirm delivery semantics and idempotency guidance are acceptable.
- [ ] I confirm versioning and compatibility rules meet platform policy.
- [ ] I approve proceeding to Business Event payloads (v1) after addressing any comments.

Sign-off table

| Event Catalog Owner (Business) | Name | Signature | Date |
|---|---:|---|---|
| | | | |

| Event Catalog Owner (Tech) | Name | Signature | Date |
|---|---:|---|---|
| | | | |

Guidance for next step (after sign-off):

1. Produce lightweight Business Event payloads (v1) for the Business Events defined in Phase 2.
2. Submit payloads as PRs with example messages and schema descriptions; do not generate OpenAPI or server stubs yet.
3. Run contract tests in a staging environment before merging.
