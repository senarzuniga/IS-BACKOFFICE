# ADR 0004 — Event‑Driven Communication

Status: Accepted

Decision
--------
Adopt an Event Bus (Kafka or managed equivalent) with versioned event schemas and a lightweight schema registry. Events are the primary integration mechanism between modules.

Consequences
------------
- Encourages asynchronous decoupling and replayability.
- Requires schema governance and contract tests.
