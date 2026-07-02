# Governance — Pull Request Rules

- Every PR touching business behavior must reference an ADR.
- No duplicated business logic across modules.
- All AI Agents must be registered in `AGENT_REGISTRY.md` before merging.
- DB schema changes must include entity model updates and migration scripts.
- UI may only contain presentation code; any logic must be justified and approved.
- CI must run architecture-validator checking presence of Architecture files.
