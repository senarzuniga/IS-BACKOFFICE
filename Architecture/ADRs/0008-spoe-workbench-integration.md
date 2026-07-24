# ADR 0008 — SPOE Workbench Integration Strategy

Status: Accepted
Date: 2026-07-23

Context
-------
Mission requires a new Standard Product Offer Engine (SPOE) without replacing architecture and without interrupting current DIGHUB evolution.

Target baseline component analyzed
---------------------------------
Component: `backoffice/ui/workbench_framework`

Current purpose:
- Provide reusable workbench primitives.
- Namespaced state handling.
- Shared scoring helper and service adapters.

Reusability assessment:
- Reuse: high (clear shared contracts).
- Extend: high (new workbench can consume same primitives and coexist).
- Replace: low (would break migration continuity and increase risk).

Alternative comparison (Global Engineering Score)
-------------------------------------------------
Scoring dimensions: Maintainability, Scalability, Template Reuse, Engineering Accuracy, Commercial Flexibility, Knowledge Integration, Coordinator Integration, Future Products, EDT Compatibility.

1) Reuse as-is only
- Score: 83.11
- Pros: minimal change risk
- Cons: limited SPOE specialization

2) Extend baseline framework (selected)
- Score: 88.89
- Pros: preserves baseline, enables dedicated SPOE services and templates
- Cons: moderate coordination effort for docs/registry alignment

3) Replace framework with SPOE-specific architecture
- Score: 54.78
- Pros: full control
- Cons: violates continuity objective and increases migration risk

Decision
--------
Select **Extend baseline framework** with SPOE modules located in `backoffice/spoe` and UI entry in `pages/spoe_workbench.py`.

Consequences
------------
- Existing architecture remains stable.
- SPOE template architecture can scale to future products.
- No disruption to current DIGHUB tracks.
- Future templates can be added by package manifests and formulas without changing workbench core.
