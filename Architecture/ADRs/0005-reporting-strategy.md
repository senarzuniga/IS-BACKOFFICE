# ADR 0005 — Reporting Strategy

Status: Proposed

Decision
--------
Adopt a dedicated Reporting Engine for executing scheduled reports and ETL to a Data Warehouse. BI reads from DW; modules publish events and optionally materialized views for DW ingestion.

Consequences
------------
- Reporting logic remains separate from domain services.
- Data quality checks must be introduced.
