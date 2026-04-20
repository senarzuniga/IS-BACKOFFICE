# IS-BACKOFFICE

AI-powered Commercial Intelligence Back Office System for Strategic Consulting Firms.

## Overview

IS-BACKOFFICE is a modular, closed-loop intelligence platform that automatically:

- **Ingests** enterprise data (emails, PDFs, Word docs, Excel, TXT, folders)
- **Cleans** raw inputs (normalization, deduplication, validation)
- **Extracts** business entities (clients, contacts, offers, sales, opportunities)
- **Stores** everything in a knowledge graph with full traceability
- **Analyzes** pipeline, forecasts revenue, scores accounts, validates offers
- **Reports** executive summaries, client diagnostics, and sales performance

## Architecture

```
IS-BACKOFFICE/
├── main.py                  # FastAPI application entry point
├── requirements.txt
├── backoffice/
│   ├── models/              # Canonical data models (Pydantic)
│   ├── ingestion/           # Module 1: Data Ingestion Layer
│   ├── cleaning/            # Module 2: Data Processing & Cleaning
│   ├── extraction/          # Module 3: Entity Extraction Engine
│   ├── graph/               # Module 4: Knowledge Graph & Memory
│   ├── analytics/           # Module 5: AI Analytics Engine
│   └── reporting/           # Module 6: Output & Reporting
├── api/
│   └── routes/              # FastAPI route handlers
└── tests/
    └── test_backoffice.py   # Full test suite
```

## Quick Start

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

Open [http://localhost:8000/docs](http://localhost:8000/docs) for the interactive API.

## Running Tests

```bash
python -m unittest discover -s tests -q
```

## Modules

### 1. Data Ingestion Layer
Connectors for: Email (`.eml`/dict), PDF, Word (`.docx`), Excel (`.xlsx`), TXT, and folder scanning.
Each record includes: `source_type`, `timestamp`, `checksum`, `document_class`.

### 2. Data Processing & Cleaning
- Text normalization, currency/unit harmonization
- Duplicate detection (SHA-256 checksum)
- Number validation and missing-data detection

### 3. Entity Extraction Engine
Rule-based extraction with confidence scoring:
- Clients, Contacts, Offers, Opportunities, Sales
- Low-confidence items → **Review Queue** for human approval

### 4. Knowledge Graph & Memory
In-memory graph store with:
- Full entity CRUD (Client, Contact, Offer, Sale, Opportunity, Product, Document)
- Relationship mapping (CLIENT_HAS_OFFER, OFFER_LEADS_TO_SALE, etc.)
- Client timeline view
- TF-IDF semantic search

### 5. AI Analytics Engine
- **Pipeline Scoring**: Opportunity scoring by stage × value
- **Forecasting**: Linear trend revenue forecast + conversion probability
- **Account Health**: Multi-factor scoring (revenue, win rate, activity)
- **Offer Validation**: Anomaly detection vs. historical pricing
- **Portfolio Analysis**: Product lifecycle classification

### 6. Output & Reporting
- Executive summary dashboard
- Client diagnostic reports
- Sales performance reports
- JSON and HTML output formats

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/ingest/file` | Upload file (PDF/DOCX/XLSX/TXT) |
| POST | `/ingest/email` | Ingest email (JSON) |
| GET | `/graph/stats` | Knowledge graph stats |
| GET | `/graph/search?q=...` | Semantic search |
| GET | `/graph/clients` | List all clients |
| POST | `/graph/clients` | Create client |
| GET | `/analytics/pipeline` | Pipeline summary |
| GET | `/analytics/forecast` | Revenue forecast |
| GET | `/analytics/accounts/health` | All account health scores |
| GET | `/analytics/offers/validation` | Offer anomaly validation |
| GET | `/analytics/portfolio` | Product lifecycle analysis |
| GET | `/reports/executive` | Executive summary (JSON) |
| GET | `/reports/executive/html` | Executive summary (HTML) |
| GET | `/reports/sales-performance` | Sales report |
| GET | `/review/pending` | Pending human review items |
| POST | `/review/{id}/approve` | Approve a review item |
| POST | `/review/{id}/reject` | Reject a review item |
