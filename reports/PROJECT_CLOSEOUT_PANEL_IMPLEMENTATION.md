# Project Closeout Panel — Implementation Summary

This report summarises the initial V1 implementation of the `Project Closeout` panel
added to IS-BACKOFFICE.

Files added
- `pages/project_closeout.py` — Streamlit UI with 8 tabs (Master Data, Contract, Engineering, Installation, Punch List, Feedback, Financial, Closeout Report).
- `services/project_closeout_service.py` — SQLite-backed persistence and import utilities (projects, documents, issues, change orders, reports).
- `services/project_closeout_extractor.py` — Lightweight text extraction and heuristic entity extraction (dates, amounts, emails).
- `services/project_closeout_reporter.py` — Simple reporter to generate HTML + JSON closeout exports.
- `scripts/generate_demo_project.py` — Creates a demo project and imports a sample punch list.

How to run (quick validation)

1. Start the backoffice UI (Windows):

```
.\run.bat
```

2. In the sidebar select `Project Closeout` (added under the main navigation).

3. Create a project using the sidebar form or run the demo data generator:

```
.venv\Scripts\python.exe scripts\generate_demo_project.py
```

4. Open the `PUNCH LIST & ISSUES` tab and import the generated CSV at `data/project_closeout/demo/demo_punchlist.csv`.

5. Generate a closeout report in the `CLOSEOUT REPORT & GANTT` tab (HTML + JSON will be written under `data/project_closeout/reports`).

Notes and next steps
- Extraction is intentionally heuristic and conservative — all extracted fields are 'draft' and must be reviewed.
- The Gantt view is left for a follow-up iteration (the reporter produces structured JSON that a Gantt renderer can consume).
- Improvements desired: OCR for scanned PDFs, richer entity extraction (contract clauses, acceptance criteria), interactive change-control table, advanced AI assistance.
