# ADR 0002 — AI Agent Framework

Status: Accepted

Decision
--------
Introduce a central Agent Registry and AI Orchestrator. Agents must be registered, versioned and sandboxed. Agent outputs must be persisted to Knowledge Graph or Event Store.

Consequences
------------
- Easier governance and auditing for AI components.
- Clear lifecycle for agents (register -> validate -> deploy -> monitor -> retire).
