# INGECART HUB — AS-IS ARCHITECTURE REPORT

Date: 2026-06-29

Summary
-------
- Repository: IS-BACKOFFICE (monorepo)
- Purpose: AI-powered commercial intelligence and simulation platform (Streamlit UI + FastAPI backend + agent orchestration)
- Scope of this report: complete folder inventory, agents inventory, API endpoints, simulation engines, risks, technical debt and prioritized recommendations.

Top-level inventory (selected)
- agents/ — agent families: knowledge_intelligence, competitive_intelligence, Reel_load_simulator (49 files)
- backoffice/ — ingestion, cleaning, extraction, graph, analytics, reporting, UI (114 files)
- core/ — simulation cores and shared models (18 files)
- api/routes/ — FastAPI endpoints (13 files)
- plant_simulator/ — lightweight simulation workbench (11 files)
- ingetrans-reel-simulator/ — separate project with full architecture docs (87 files)
- frontend/ & streamlit pages — multiple Streamlit pages under pages/ and frontend/ (UI)

Key findings
-----------
- CI expects an architecture scanner under `tools/architecture_assistant/check_architecture.py` producing `Architecture/AI/architecture_report.json` but that scanner is not present locally. I created `Architecture/AI/architecture_report.json` as an initial As-Is artifact.
- Dependency file `requirements.txt` contains contradictory pins for `supabase` and many optional heavy deps; `requirements-dev.txt` is referenced in CI but missing.
- There are multiple simulation implementations (core and ingetrans project plus plant_simulator) — duplication of logic and maintenance overhead.
- Agents are rich and numerous but there's no central Agent Registry or formal contract definitions — risk of interface drift.
- The product exposes FastAPI routes (see [main.py](main.py#L1)) and Streamlit UIs; orchestration endpoints and simulation APIs exist.

Risks & Technical Debt
----------------------
- Dependency conflicts and lack of dev requirements: High risk for CI and developer onboarding.
- Architecture drift across agent families: Medium risk; mitigated by agent registry and ADRs.
- Duplicate simulation code: Medium risk; refactor to shared components.

Prioritized recommendations (short-term)
-------------------------------------
1. Approve this As-Is report before any change.
2. Create an Architecture Hub (`Architecture/`) containing: this As-Is report, Agent Registry draft, ADR templates, and To-Be architecture artifacts.
3. Add `requirements-dev.txt` and consolidate `requirements.txt` (runtime vs dev separation).
4. Decide canonical simulation implementation (or extract shared core) to eliminate duplication.
5. Add CI job to validate Architecture/ presence and basic checks (no enforcement of behavior yet).

Next steps (after approval)
--------------------------
- Produce detailed To-Be architecture (component diagrams, data flows, module ownership, non-functional requirements and migration plan).
- Build Agent Registry document listing: agent name, responsibilities, inputs, outputs, API/contract, owner, tests, maturity.
- Create ADR templates and initial ADRs covering: simulation canonicalization, dependency pinning policy, agent registry adoption, CI governance.

Contact
-------
Chief Architect (acting): INGECART Enterprise Architecture Team
