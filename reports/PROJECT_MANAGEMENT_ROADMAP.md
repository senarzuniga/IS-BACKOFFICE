Project Management — Prioritised Roadmap (practical estimates)

Goal: bring repository Project Management capabilities to industrial readiness for Ingecart.

Priority 1 — Critical missing functionality (must have)
1. Canonical Project Registry + ERP synchronization
   - Deliverable: single canonical `projects` registry and sync mechanism mapping ERP `projects` ↔ Closeout projects.
   - Affected modules: services/project_closeout_service.py, erp_facturacion/erp.py, API layer (new endpoints), pages/project_closeout.py
   - Estimate: 6–12 dev days
   - Dependencies: database migration, small API, mapping rules

2. Project financial reconciliation & P&L
   - Deliverable: aggregated project P&L using ERP invoices/payments/POs and closeout attachments; project financial summary in closeout report.
   - Affected: erp_facturacion/erp.py, backoffice/reporting/generator.py, services/project_closeout_reporter.py
   - Estimate: 10–18 dev days
   - Dependencies: canonical project registry

3. Schedule model + interactive Gantt (tasks, milestones, dependencies)
   - Deliverable: DB tables for tasks/milestones, task editor, plotly/plotly.express Gantt in pages/project_closeout.py consuming task JSON from reporter.
   - Affected: services/project_closeout_service.py (new tables), pages/project_closeout.py, services/project_closeout_reporter.py
   - Estimate: 12–25 dev days
   - Dependencies: canonical project registry

4. Change-order approval workflow & audit trail
   - Deliverable: extend change_orders with states/roles, approval endpoints, UI flow.
   - Affected: services/project_closeout_service.py, pages/project_closeout.py
   - Estimate: 4–8 dev days

5. Document versioning / drawing register
   - Deliverable: versioned documents table, drawing metadata, view history, linkable revision IDs.
   - Affected: services/project_closeout_service.py, pages/project_closeout.py
   - Estimate: 5–10 dev days

Priority 2 — High-value improvements
1. Ingest Closeout docs into Knowledge Hub (KnowledgeMemory / Chroma) and tag by project
   - Estimate: 7–14 dev days
2. Integrate AI Orchestrator to auto-generate executive summaries, risk analysis, and closeout drafts
   - Estimate: 7–14 dev days
3. Risk register, Action register, Decision register (structured tables + UI)
   - Estimate: 7–12 dev days
4. Project KPI dashboard with thresholds, colors, and alerts
   - Estimate: 6–12 dev days

Priority 3 — Future enhancements
1. Resource planning & leveling; integration with manufacturing/work orders (heavy)
   - Estimate: 20–40 dev days
2. Truth Graph ingestion for projects and full cross-domain linking
   - Estimate: 10–20 dev days

Estimated total (to reach industrial readiness ~85/100): 600–1200 dev-hours (~4–9 person-months depending on team size and parallel work).

Notes: begin with canonical registry and financial reconciliation (P1) — they unlock downstream reporting and AI ingestion.
