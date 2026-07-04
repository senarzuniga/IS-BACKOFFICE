Module Summary — IS-BACKOFFICE

Overview:
- UI: Streamlit pages under `pages/` and `backoffice/ui/` command center.
- ERP: `erp_facturacion/` provides invoice DB, PDF generation, and CRUD.
- Knowledge Hub: `knowledge_hub/` and `agents/knowledge_intelligence/` for competitive intelligence and agent workflows.
- Simulators: `ingetrans-reel-simulator/`, `plant_simulator/`, `agents/Reel_load_simulator/`.
- Core libs: `backoffice/`, `backoffice/ingestion/`, `backoffice/analytics/`.
- API backend: `api/` with FastAPI routes.
- Reports: `reports/` contains templates and this new `reconciliation/` folder.

Critical files and health checks:
- `erp_facturacion/database.db` — ensure recent backups exist.
- `streamlit_app.py` & `start_backoffice.py` — verify Streamlit entrypoints and port availability.
- `backoffice/ui/command_center.py` — check sidebar items mapping to pages.

Next steps:
1. Produce file lists for the directories below.
2. Run unit tests and capture failures.
3. Validate DB backups and list recent manual changes (git diff).
4. Create a findings report with high/medium/low risk items and remediation suggestions.
