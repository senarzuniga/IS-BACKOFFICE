PROJECT UI WIREFRAMES V2

Goal
----
Define the Project Digital Twin UI: a single page per project exposing Overview, Dashboard, Timeline/Gantt, Documents, Risks, Issues, Financials, Procurement, Installation, Commissioning, Knowledge Hub, Truth Graph and AI Assistant.

Layout principles
-----------------
- Responsive single-page layout with top header (project selector + key actions) and tabbed main content.
- Left column (optional) contextual navigation for quick filters and KPIs.
- Right column (optional) contextual widgets (AI Assistant, quick actions, recent activity).

Top-level page structure
------------------------
- Header: project selector, canonical_project_id, status badge, last updated, quick actions (Generate report, Export, Add document)
- KPI row (cards): Overall Health Score, Financial Health, Schedule Health, Engineering Health, Outstanding Actions, Open Risks, Cash Position
- Tabs: Overview | Dashboard | Timeline | Gantt | Engineering | Documents | Meetings | Risks | Issues | Actions | Financial | Payments | Procurement | Installation | Commissioning | Punch List | Warranty | Knowledge Hub | Truth Graph | AI Assistant | Executive Reports

Wireframe (ASCII - desktop)

---------------------------------------------------------------------------------
| HEADER: [Project Selector ▼]  PRJ-2026-001  | Status: Execution | [Generate Report] |
---------------------------------------------------------------------------------
| KPI1 | KPI2 | KPI3 | KPI4 | KPI5 | KPI6 |
---------------------------------------------------------------------------------
| Tab bar: Overview | Dashboard | Timeline | Gantt | ...                       |
---------------------------------------------------------------------------------
| Left column (filters) | Main content area (tab content)                      | Right column (AI/Notes) |
| - Quick filters         | - content changes per tab                              | - AI Assistant chat box  |
---------------------------------------------------------------------------------

Tab details and components
--------------------------
Overview (default)
- Executive summary text (editable)
- Key dates (start, FAT, shipment, planned_install, SAT)
- Top 5 risks & top 5 actions
- Quick links to last documents and recent meetings

Dashboard
- Time-series charts: cashflow, cost vs budget, schedule % complete
- Bar charts: supplier performance, invoice ageing
- Gauge: project health, schedule adherence, financial buffer

Timeline
- Interactive timeline showing phases and milestones
- Click milestone → open modal with details and linked documents

Gantt
- Interactive Gantt (zoom, drag-resize tasks)
- Task editor modal with dependencies, assignments and durations

Engineering
- Deliverables table with status, owner, due date, linked drawings
- Drawing viewer, file version history

Documents
- Searchable list with filters: doc_type, tags, date, supplier, confidence
- Upload control: drag & drop, metadata form (auto-extract fields, link to equipment, milestone)
- Document details panel: preview, extracted entities, link to Knowledge Hub entry, provenance

Meetings
- Meeting list with participants, minutes (view/download), action items quick-add

Risks
- Risk register table with risk score, mitigation, history, owner
- Risk heatmap visualization

Issues/Punch List
- Kanban or table view: open / in progress / closed
- Import CSV/XLSX and map columns to canonical fields

Actions
- Action register with due date, owner, status, linked decision

Financial
- P&L summary, invoiced vs budget vs cost to complete
- Invoice list (linked to ERP), payment forecast chart

Payments
- Invoice and payment register, certificate attachments

Procurement
- POs linked to suppliers, status, receipts, related drawing/deliverable

Installation / Commissioning
- Site reports timeline, commissioning checklist, test reports, SAT acceptance form

Warranty / Claims
- Warranty register and claims tracker

Knowledge Hub
- Project-scoped search UI (semantic + keyword) showing evidence snippets and linked documents

Truth Graph
- Graph viewer showing `project` node and connected documents/risks/people/suppliers

AI Assistant
- Right-side dockable chat interface
- When user asks a question: show system pipeline trace, ranked evidence references, confidence score, and clickable sources

Executive Reports
- Auto-generated list (daily/weekly) with download links (PDF/HTML/MD) and 'Regenerate' action

UX: document upload flow
------------------------
1. User uploads file → temporary stored in object store
2. Extractor runs (background) and returns extracted metadata & suggested tags
3. UI shows extracted preview and allows editing fields: Project (auto-detected), Customer, Supplier, Equipment, Date, Tags
4. User confirms → document metadata saved, indexer runs to update Knowledge Hub and Truth Graph

Acceptance criteria (per feature)
-------------------------------
- Any uploaded document must be linkable to canonical_project_id and appear in Knowledge Hub search within configurable window (e.g., 30s).
- Gantt changes must persist and affect schedule health scoring.
- AI assistant responses must always include a list of referenced documents and a confidence metric.

APIs required (high level)
-------------------------
- GET/POST /projects, /projects/{id}/documents, /projects/{id}/tasks, /projects/{id}/issues, /projects/{id}/risks, /projects/{id}/reports

Accessibility & responsive
--------------------------
- Ensure keyboard navigation for lists and modals; charts have high-contrast color palettes and textual equivalents.

Notes for engineers
-------------------
- Start with the existing Streamlit `pages/project_closeout.py` UI and progressively migrate to richer UI frameworks only where necessary (Plotly for Gantt, custom React for graph view) to prevent full rewrite.
