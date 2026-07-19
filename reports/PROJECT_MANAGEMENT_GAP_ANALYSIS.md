Project Management — Gap Analysis (evidence)

Purpose: enumerate concrete gaps between the repository implementation and industrial Project Management expectations. Each gap includes evidence (file references) present in the repository.

1) Missing functionality
- Canonical Project Registry / Global Project ID
  - Evidence: Closeout uses local `projects` table (services/project_closeout_service.py) while ERP has a separate `projects` table (erp_facturacion/erp.py). No synchronization code found.
- Schedule/Tasks/Milestones (Gantt/CPM)
  - Evidence: No `milestones` or `tasks` table, no Gantt UI in pages/project_closeout.py; reporter produces simple JSON/HTML only (services/project_closeout_reporter.py).
- Resource Planning and Assignment
  - Evidence: No resources or assignments in data model.
- Project Financial Reconciliation & P&L
  - Evidence: ERP stores invoices/payments (erp_facturacion/erp.py) but closeout reports do not consume ERP financials.
- Approval workflows and audit trail (CO, invoices, closeout sign-off)
  - Evidence: change_orders table exists but lacks approval workflow fields or state machine beyond an `approved` flag (services/project_closeout_service.py).
- Document versioning / controlled drawing register
  - Evidence: documents saved and hashed (services/project_closeout_service.py) but no version history table or revision metadata.
- Risk Register & Risk Scoring
  - Evidence: no `risks` table or risk UI.
- Traceability across engineering → procurement → manufacturing → commissioning
  - Evidence: GraphStore contains offers/opportunities but does not include `project` entities and closeout does not upsert links into GraphStore.

2) Missing workflows
- CO approval workflows with roles and timestamps (evidence: change_orders minimal schema)
- Commissioning acceptance and SAT sign-off (evidence: installation tab supports uploads but no sign-off)
- Lessons-learned publication to Knowledge Hub (evidence: KnowledgeMemory exists but no ingestion from closeout)
- Supplier performance tracking & claims management (no tables/flows)

3) Missing reports
- Project-level P&L / Cash Flow Forecast — no implementation (reporter lacks financial inputs)
- Risk Heatmap — no implementation
- Executive Steering Committee Pack — project-level executive pack not generated (system-level executive report exists but lacks project integration)

4) Missing dashboards / visualizations
- Interactive Gantt / Critical Path / Milestone tracker
- Project KPI dashboard with color-coded statuses and trends

5) Missing traceability / linkage
- No canonical IDs or mapping between ERP projects and Closeout projects
- Documents not linked to ERP purchase orders, manufacturing orders or GraphStore entities

6) Missing document control
- No versioning, no check-in/check-out, no drawing revision metadata

7) Missing engineering management features
- No deliverable acceptance workflows, no versioned deliverables, no test-report linking to deliverable acceptance

8) Missing project governance features
- No role-based approvals, no audit trail for approvals, no sign-off export (PDF/SIGNED) capability

This gap analysis is intentionally concise and references repository evidence. Use PROJECT_MANAGEMENT_ROADMAP.md and IMPLEMENTATION_PLAN for remediations and estimates.
