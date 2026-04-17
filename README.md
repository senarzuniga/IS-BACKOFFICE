# IS-BACKOFFICE

Modular AI-powered Back Office System for strategic consulting operations.

## Architecture

The implementation provides 6 core modules:

1. **Data Ingestion Layer** (`backoffice/ingestion.py`)
   - Supports: Outlook-style email payloads, PDF/Word/Excel/TXT metadata ingestion, folder scanning, and optional CRM source type.
2. **Data Processing & Cleaning Layer** (`backoffice/processing.py`)
   - Normalizes content, removes duplicates, validates numeric fields, and detects missing data.
3. **Entity Extraction & Structuring Engine** (`backoffice/extraction.py`)
   - Extracts normalized customers, opportunities, offers, and sales entities.
4. **Knowledge Graph & Memory System** (`backoffice/knowledge_graph.py`)
   - Builds relationships (client↔offers/sales/opportunities), stores timeline, and supports semantic search + learning feedback.
5. **AI Analytics Engine** (`backoffice/analytics.py`)
   - Generates pipeline/deal/forecast insights, portfolio classification, key account intelligence, and offer validation anomalies.
6. **Output & Reporting Engine** (`backoffice/reporting.py`)
   - Produces executive report structures, diagnostics, strategic opportunities, presentation slides, and traceability to source records.

## Closed-loop behavior

`CommercialIntelligenceOS` (`backoffice/orchestration.py`) orchestrates:

- continuous capture input (records or folder scan)
- automatic cleaning + validation
- entity structuring
- knowledge graph update
- analytics generation
- reporting output
- learning signals fed back into memory

## Run tests

```bash
python -m unittest discover -s tests -q
```
