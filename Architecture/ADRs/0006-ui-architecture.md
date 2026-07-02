# ADR 0006 — UI Architecture

Status: Proposed

Decision
--------
UI must be a thin presentation layer using shared component library. No domain logic or calculations in UI; all such behaviors live in modules or Core.

Consequences
------------
- Cleaner separation of concerns and easier testing.
