# ADR 0001 — Modular Architecture

Status: Accepted

Context
-------
The repository contains overlapping responsibilities across multiple modules and simulation engines. We need a clear module ownership model.

Decision
--------
Adopt a module ownership model: each Business Module owns its data, APIs and emits events. Core Platform provides horizontal services only.

Consequences
------------
- Migrations scoped per module.
- DB-per-module or schema-per-module recommended.
- Events are the integration mechanism.
