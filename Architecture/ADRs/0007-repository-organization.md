# ADR 0007 — Repository Organization

Status: Proposed

Decision
--------
Adopt monorepo layout with clear ownership files and an `Architecture/` hub. Modules live under `modules/` or similar and core under `core/`. CI enforces architecture presence.

Consequences
------------
- Easier changes across modules; requires CI discipline.
