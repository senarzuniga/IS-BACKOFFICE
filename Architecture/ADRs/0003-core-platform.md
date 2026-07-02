# ADR 0003 — Core Platform Responsibilities

Status: Accepted

Decision
--------
Define Core Platform to provide only horizontal technical services: Auth, Authorization, Workflow, Event Bus, Notification, Search, AI Orchestrator, Config, Feature Flags, Observability.

Consequences
------------
- Business logic must be moved out of Core.
- Core must be lightweight and well-tested.
