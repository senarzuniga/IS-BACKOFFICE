Offers Extractor Orchestrator
================================

This orchestrator (`offers_extractor_orchestrator.py`) is an execution entrypoint to perform
targeted discovery and extraction of commercial terms from a folder of offers.

How to run (PowerShell recommended):

& 'c:/Users/Inaki Senar/Documents/GitHub/IS-BACKOFFICE/.venv/Scripts/python.exe' knowledge_hub/competitive_intel/offers_extractor_orchestrator.py "C:\Users\Inaki Senar\OneDrive\INGECART\OFERTAS INGECART\OFERTAS ENVIADAS 2026"

Outputs are stored under `knowledge_hub/outputs/`.

Notes:
- The script uses optional dependencies for better parsing (pdfplumber, PyPDF2, docx, openpyxl, pytesseract).
- It is conservative about claims: missing fields are marked, and evidence snippets are stored.
