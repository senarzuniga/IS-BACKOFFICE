# IS-BACKOFFICE

AI-powered Commercial Intelligence Back Office System for Strategic Consulting Firms.

## Overview

IS-BACKOFFICE is a modular, closed-loop intelligence platform with two server processes:

- **FastAPI** backend — REST API covering data ingestion, entity extraction, knowledge graph, analytics, reporting, and multi-agent orchestration
- **Streamlit** frontend — interactive UI with a module command center, document analysis page, and natural language instruction panel

The system runs fully without an OpenAI API key; AI enhancement is optional and degrades gracefully.

---

## Architecture

```
IS-BACKOFFICE/
├── main.py                        # FastAPI entry point
├── streamlit_app.py               # Streamlit entry point → backoffice/ui/app.py
├── requirements.txt
├── docker-compose.yml             # backend + frontend + redis + postgres
│
├── backoffice/
│   ├── models/                    # Canonical Pydantic data models
│   ├── ingestion/                 # Module 1: Data Ingestion Layer
│   ├── cleaning/                  # Module 2: Data Processing & Cleaning
│   ├── extraction/                # Module 3: Entity Extraction Engine
│   ├── graph/                     # Module 4: Knowledge Graph & Memory
│   ├── analytics/                 # Module 5: AI Analytics Engine
│   ├── reporting/                 # Module 6: Output & Reporting
│   ├── agents/                    # Module 7: Multi-Agent Orchestrator
│   ├── ui/                        # Streamlit UI shell + components
│   ├── orchestration.py           # CommercialIntelligenceOS top-level runner
│   └── runtime_components.py      # Lightweight in-memory runtime primitives
│
├── api/
│   ├── state.py                   # Shared GraphStore + ReviewQueue singletons
│   └── routes/                    # FastAPI route handlers per domain
│
├── document_analysis/             # Standalone document analysis pipeline
│   ├── folder_reader.py           # File discovery (60+ extensions)
│   ├── document_parser.py         # Text extraction (50+ file types)
│   ├── content_extractor.py       # NER + topic extraction
│   ├── context_analyzer.py        # Cross-document analysis
│   ├── output_generator.py        # 10 output format generators
│   ├── ai_enhancer.py             # Optional GPT enhancement
│   └── cache.py                   # SHA-256 file-based processing cache
│
├── instruction_panel/             # Natural language command interpreter
│   ├── instruction_parser.py      # Regex + optional LLM instruction parsing
│   └── executor.py                # Step-by-step instruction executor
│
├── models/                        # Shared Pydantic instruction/output models
├── frontend/                      # API-driven Streamlit control tower (Docker)
├── shared/                        # Shared request/response schemas
└── tests/                         # Full test suite (42 tests)
```

---

## Quick Start

```bash
pip install -r requirements.txt

# Start the API (http://localhost:8000/docs)
uvicorn main:app --reload

# Start the Streamlit UI (http://localhost:8501)
streamlit run streamlit_app.py
```

### Docker (full stack)

```bash
docker compose up --build
```

Starts: backend (8000), frontend (8501), Redis (6379), PostgreSQL (5432).

### Running Tests

```bash
python -m unittest discover -s tests -q
```

---

## Streamlit UI

The UI is a multipage Streamlit application with three pages.

### Main App (`streamlit_app.py` → `backoffice/ui/app.py`)

**Sidebar — System Status panel:**
- Green/red health indicators per module (Ingestion, Cleaning, Extraction, Graph, Analytics, Reporting)
- Memory usage progress bar
- Last activity timestamp
- Processing statistics (entities, memory %)

**Sidebar — Command Center panel:**
- Module selector (Ingestion / Cleaning / Extraction / Graph / Analytics / Reporting)
- Context-sensitive action inputs for each module:
  - **Ingestion**: file upload, URL + method, folder watch path + schedule toggle, bulk upload, scraper URL list + depth
  - **Cleaning**: entity type + deduplication threshold, standardization rule preset, quality audit dataset, outlier column + method, fuzzy merge threshold + review mode
  - **Extraction**: text area, PDF upload, batch folder path + entity type multiselect, few-shot examples, table detection toggle
  - **Graph**: search query, entity explorer (ID + depth), path finder (from/to), community toggle, subgraph visualization
  - **Analytics**: dataset + insight type, natural language query, forecast metric + horizon + model, what-if price/conversion sliders, dashboard template
  - **Reporting**: template selector, date range picker, schedule frequency + recipients + format, export format, email template, report history toggle
- **Run Selected Action** button
- **Quick Actions**: Document Analysis, Instruction Panel, Process All New Files, Today's Dashboard, Ask AI Assistant, Create Summary, Settings

**Main content area:**
- Default dashboard: 4 KPI metrics (files processed, entities extracted, reports generated, pending tasks), recent activity feed table, quick module health overview
- Section result panels:
  - **Ingestion**: file list table, bulk progress bar, schema preview
  - **Cleaning**: before/after data comparison, quality score metric, issue list with accept/reject actions
  - **Extraction**: entity table, confidence histogram, relationship adjacency table, JSON download
  - **Graph**: interactive network HTML preview, node details, path table, graph JSON export
  - **Analytics**: revenue + forecast line chart, insight callouts, account health table with download
  - **Reporting**: report HTML preview, PDF/Excel/PPT/DOCX download buttons, email/schedule status

---

### Document Analysis Page (`pages/document_analysis.py`)

Full-featured document analysis workflow:

1. **Folder Selection** — enter any local path
2. **Options** — recursive scan toggle, max file size slider (1–200 MB), processing cache toggle, AI enhancement toggle (requires `OPENAI_API_KEY`)
3. **Discover Files** — lists all supported files with type/size; shows stats per document type
4. **Process All Files** — parses each file, enriches with NER + topics, shows progress bar + per-file status log
5. **Generate Output** — 10 output format options:
   - Summary, Executive Summary, Full Report, Presentation Outline, Document List, Database Entry (JSON), Knowledge Graph Export, Intelligence Brief, Comparison Table, Timeline
6. **Export** — Download as Markdown or structured JSON
7. **Clear Results** — resets all session state

---

### Instruction Panel (`pages/instruction_panel.py`)

Natural language command center for folder-based document intelligence:

- **Instruction input** — free-text area; accepts instructions like:
  - *"Check C:\Documents\Contracts and list all files"*
  - *"Read all PDFs and create an executive summary"*
  - *"Extract names and dates and make a timeline"*
  - *"Analyze all contracts and create a generic model"*
- **Example instructions** — one-click templates: Explore Folder, Summarize Docs, Extract & Timeline, Executive Analysis, Compare Specs
- **Quick Folder Browser** — one-click shortcuts for Documents, Desktop, Downloads, and custom paths
- **Execute** — parses the instruction (intent, folder path, output type, file filters), then runs step-by-step with live progress bar and status messages
- **Results** — renders output as markdown, step execution log with durations, download as Markdown or TXT
- **Instruction History** — last 10 instructions with timestamps and re-run buttons
- **Diagnose Folder** — inspects any folder path from the instruction, shows a table of every file with extension, size, detected type, and support status; unknown extensions are flagged as raw-text fallback candidates

---

## FastAPI REST API

Interactive docs: [http://localhost:8000/docs](http://localhost:8000/docs)

### Ingestion — `/ingest`

| Method | Path | Description |
|--------|------|-------------|
| POST | `/ingest/file` | Upload a PDF, DOCX, XLSX, or TXT file; runs full cleaning + extraction pipeline; returns cleaning report + extracted entities |
| POST | `/ingest/email` | Ingest a JSON email payload (subject, sender, body); same pipeline |

### Knowledge Graph — `/graph`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/graph/stats` | Entity counts for all 7 entity types in the in-memory graph |
| GET | `/graph/search?q=&top_k=` | TF-IDF semantic search across clients, offers, and opportunities |
| GET | `/graph/clients` | List all client entities |
| GET | `/graph/clients/{client_id}/timeline` | Full activity timeline for a client (offers, sales, opportunities) |
| POST | `/graph/clients` | Create or upsert a Client entity |
| POST | `/graph/offers` | Create or upsert an Offer entity |
| POST | `/graph/sales` | Create or upsert a Sale entity |
| POST | `/graph/opportunities` | Create or upsert an Opportunity entity |
| POST | `/graph/products` | Create or upsert a Product entity |

### Analytics — `/analytics`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/analytics/pipeline` | Pipeline summary: opportunities by stage, weighted value, top-5 list |
| GET | `/analytics/forecast?periods=3` | Linear-trend revenue forecast for next N months |
| GET | `/analytics/conversion` | Lead-to-sale conversion probability from closed opportunity history |
| GET | `/analytics/accounts/health` | Account health scores for all clients (0–100, sorted descending) |
| GET | `/analytics/accounts/{client_id}/health` | Health score for a single client with upsell/cross-sell flags |
| GET | `/analytics/offers/validation` | 3-sigma pricing anomaly detection on all offers vs. historical sales |
| GET | `/analytics/portfolio` | Product lifecycle classification (commodity / growth / decline / innovation) |

### Reporting — `/reports`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/reports/executive` | Full executive summary JSON (pipeline, forecast, top accounts, portfolio, anomalies) |
| GET | `/reports/executive/html` | Same executive summary rendered as an HTML table |
| GET | `/reports/clients/{client_id}/diagnostic` | Client diagnostic: health score + timeline + offer anomaly validation |
| GET | `/reports/sales-performance` | Monthly revenue + pipeline summary + all account health scores |

### Review Queue — `/review`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/review/pending` | List all extraction results pending human review |
| POST | `/review/{item_id}/approve` | Approve a review item (optional notes) |
| POST | `/review/{item_id}/reject` | Reject a review item (optional notes) |

### Orchestration — `/orchestration`

| Method | Path | Description |
|--------|------|-------------|
| POST | `/orchestration/run` | Full cycle: ingest one record through `CommercialIntelligenceOS`; supports `proactive_mode`, `autolearning_mode`, `strict_mode` flags |
| POST | `/orchestration/agents/run` | Same record through the 9-agent `MultiAgentOrchestrator`; returns pipeline trace + alerts list |

---

## Core Backend Modules

### Module 1 — Data Ingestion (`backoffice/ingestion/`)

| Connector | File Types | Notes |
|-----------|-----------|-------|
| `EmailConnector` | `.eml`, dict | Parses raw email bytes or JSON dict (subject/sender/body) |
| `PDFConnector` | `.pdf` | Text extraction via PyMuPDF; page count |
| `WordConnector` | `.docx` | Paragraph text via python-docx |
| `ExcelConnector` | `.xlsx`, `.csv` | Tabular data via pandas |
| `TxtConnector` | `.txt` | Charset auto-detection via chardet |
| `FolderScanner` | All above | Recursive directory walk; dispatches by extension; captures per-file errors |

Every `RawRecord` carries: `source_type`, `timestamp`, SHA-256 `checksum`, `document_class` (offer / contract / report / invoice / other).

---

### Module 2 — Data Processing & Cleaning (`backoffice/cleaning/`)

- **`Deduplicator`** — removes duplicate records by SHA-256 checksum; also deduplicates dicts by any named field
- **`Normalizer`** — strips accents from names, normalizes whitespace, converts EU/US number formats, detects and normalizes currencies to EUR
- **`Validator`** — validates numeric ranges, email addresses (regex), required fields, currency codes
- **`CleaningPipeline`** — orchestrates dedup → normalize → validate; returns cleaned records and a `CleaningReport` (counts per step)

---

### Module 3 — Entity Extraction (`backoffice/extraction/`)

- **`ExtractionEngine`** — rule-based NLP extraction with confidence scoring:
  - Clients (name regex patterns)
  - Contacts (email + phone regex)
  - Offers (reference + amount)
  - Opportunities (amount + stage keywords: qualification, proposal, negotiation, closed_won, closed_lost)
  - Low-confidence results automatically flagged for human review
- **`ReviewQueue`** — in-memory queue for items needing human approval; supports enqueue / approve / reject with timestamps
- **`EntityExtractionStructuringEngine`** — alternative key=value parser used by the `CommercialIntelligenceOS` runtime; produces `EntityBundle` (customers, opportunities, offers, sales)

---

### Module 4 — Knowledge Graph & Memory (`backoffice/graph/`)

- **`GraphStore`** — in-memory dict-based entity store for all 7 types (Client, Contact, Offer, Sale, Opportunity, Product, Document); full CRUD upsert; client timeline query; entity stats
- **`SemanticSearch`** — TF-IDF keyword scoring across entity text fields; returns ranked results
- **`Relation` / `RelationType`** — 9 typed relation types: `CLIENT_HAS_CONTACT`, `CLIENT_HAS_OFFER`, `OFFER_LEADS_TO_SALE`, `OFFER_LEADS_TO_OPPORTUNITY`, `OPPORTUNITY_HAS_SALE`, `CLIENT_HAS_SALE`, `SALE_INCLUDES_PRODUCT`, `CLIENT_INTERESTED_IN_PRODUCT`, `DOCUMENT_MENTIONS_CLIENT`

---

### Module 5 — AI Analytics Engine (`backoffice/analytics/`)

| Component | Function |
|-----------|----------|
| `PipelineScorer` | Scores opportunities by stage probability; pipeline summary with stage breakdown and top-5 weighted list |
| `Forecaster` | Aggregates monthly revenue; linear regression forecast for N periods; conversion probability from closed history |
| `AccountHealthScorer` | Composite 0–100 score: revenue (40 pts) + win rate (30 pts) + open opportunities (20 pts) + offer count (10 pts); detects upsell/cross-sell flags |
| `OfferValidator` | 3-sigma anomaly detection on offer pricing vs. historical client sales; flags missing prices |
| `PortfolioAnalyzer` | Classifies products into commodity / growth / decline / innovation lifecycle stages by revenue share |
| `AIAnalyticsEngine` | Alternative analytics engine for `CommercialIntelligenceOS`; supports pluggable extra agents via `register_agent()` |

---

### Module 6 — Output & Reporting (`backoffice/reporting/`)

`ReportGenerator` composes all analytics engines into three report types:

- **`executive_summary()`** — pipeline + forecast + top accounts + portfolio + anomalies
- **`client_diagnostic()`** — health score + timeline + offer validation for one client
- **`sales_performance()`** — monthly revenue + pipeline summary + all account health scores

All reports available as JSON (`to_json()`) and HTML table (`to_html()`).

---

### Module 7 — Multi-Agent Orchestrator (`backoffice/agents/`)

`MultiAgentOrchestrator` runs 9 sequential agents for a single record:

1. **IngestionAgent** — validates and ingests the raw record
2. **DataCleaningAgent** — deduplication + normalization
3. **ExtractionAgent** — entity extraction with confidence scoring
4. **KnowledgeGraphAgent** — upserts extracted entities to the graph store
5. **AnalyticsAgent** — runs pipeline scoring and account health
6. **ForecastAgent** — revenue forecast and conversion probability
7. **AnomalyAgent** — pricing anomaly detection; raises alerts on anomalies
8. **ReportAgent** — generates executive summary
9. **ReviewAgent** — checks for proactive signals; raises alerts

Each agent appends its name to the `AgentContext.trace`. The full trace, alert list, and result dict are returned to the caller.

---

### Top-Level Orchestrator (`backoffice/orchestration.py`)

`CommercialIntelligenceOS` owns all runtime components and executes the full data cycle:

```
ingest → process/clean → extract entities → upsert to graph
→ analytics → reporting → proactive signals
```

Run modes:
- `proactive_mode` — generates proactive pipeline, anomaly, and forecast signals
- `autolearning_mode` — accumulates signals into the knowledge memory system
- `strict_mode` — raises `InvalidValueError` instead of silently continuing on bad data

---

## Document Analysis Pipeline (`document_analysis/`)

### Supported File Types (60+ extensions)

| Category | Extensions |
|----------|-----------|
| Documents | `.pdf`, `.docx`, `.doc`, `.docm`, `.rtf`, `.odt`, `.wpd`, `.wps`, `.pages` |
| Spreadsheets | `.xlsx`, `.xls`, `.xlsm`, `.xlsb`, `.ods`, `.numbers`, `.csv`, `.tsv`, `.tab` |
| Presentations | `.pptx`, `.ppt`, `.pptm`, `.odp`, `.key` |
| Text | `.txt`, `.md`, `.rst`, `.log`, `.text` |
| Email | `.eml`, `.msg`, `.emlx` |
| Structured | `.json`, `.xml`, `.yaml`, `.yml` |
| Web | `.html`, `.htm`, `.mht`, `.mhtml` |
| Images (OCR) | `.png`, `.jpg`, `.jpeg`, `.tiff`, `.tif`, `.bmp`, `.gif`, `.webp`, `.heic` |
| Archives | `.zip`, `.rar`, `.7z` |

Unknown extensions trigger a multi-encoding raw text fallback (`utf-8 → latin-1 → cp1252 → iso-8859-1 → cp850`).

### Components

| Component | Functionality |
|-----------|--------------|
| `FolderReader` | Recursive discovery; size/date/type filters; compute `FolderStats`; excludes only system files (Thumbs.db, .DS_Store, desktop.ini) |
| `DocumentParser` | Per-file text + table extraction; 50+ format parsers; graceful fallback chain for legacy formats (`.doc`, `.xls`, `.ppt`, `.rtf`); LibreOffice conversion path when available |
| `ContentExtractor` | spaCy NER (optional) or regex fallback for emails, phones, dates, money amounts, organizations; word-frequency topic extraction |
| `ContextAnalyzer` | Cross-document shared theme detection; entity cross-reference mapping; chronological timeline building; narrative summary; content gap and contradiction detection |
| `OutputGenerator` | 10 output formats: `summary`, `executive_summary`, `report`, `presentation`, `list`, `database_entry`, `knowledge_graph`, `new_brief`, `comparison`, `timeline` |
| `AIEnhancer` | Optional GPT-4o-mini wrapper: `enhance_output()` (prose rewriting), `generate_insights()` (strategic insights), `summarize_document()` (per-document summaries) |
| `ProcessingCache` | SHA-256 file-based cache at `~/.cache/is_backoffice/doc_analysis/`; get / set / invalidate / clear |

---

## Natural Language Instruction System (`instruction_panel/`)

### `InstructionParser`

Converts free-text instructions into structured action plans:

- **Path extraction** — quoted Windows/Unix paths, greedy + trimmed unquoted paths, named patterns (`check`, `read`, `analyze`, `inside`)
- **File type detection** — keyword mapping: pdf, word, excel, csv, text, JSON, XML, HTML, PowerPoint
- **Output type detection** — verb/noun mapping: summarize → summary, compare → comparison, timeline, report, table, list, JSON, CSV, database
- **Intent detection** — 11 intents: explore_folder, extract_info, analyze_documents, generate_output, compare_documents, find_specific, structure_data, create_report, create_presentation, summarize, custom
- **LLM enrichment** — optional OpenAI call (GPT-4o-mini by default) for richer intent + action plan; graceful fallback to rule-based if no API key

### `InstructionExecutor`

Executes parsed instructions step-by-step with progress callbacks:

| Action | What it does |
|--------|-------------|
| `read_folder` | Runs `FolderReader.discover_files()` + `get_folder_stats()` |
| `parse_documents` | Parses each file via `DocumentParser` + enriches via `ContentExtractor` |
| `extract_entities` | Collects all entities from parsed documents |
| `analyze_content` | Runs `ContextAnalyzer.analyze_folder()` (themes, relationships, timeline, narrative) |
| `generate_output` | Generates the requested output format via `OutputGenerator`; optionally enhances with AI |
| `search` | Keyword search across all parsed document text |

---

## Data Models (`backoffice/models/`)

| Model | Key Fields |
|-------|-----------|
| `Client` | name, industry, country, currency, tags, annual_revenue, account_health_score |
| `Contact` | client_id, first_name, last_name, email, phone, role, is_decision_maker |
| `Offer` | client_id, title, status (draft/sent/accepted/rejected/expired), total_value, currency, items, valid_until, pricing_anomaly |
| `Opportunity` | client_id, title, stage (qualification/proposal/negotiation/closed_won/closed_lost), estimated_value, probability, expected_close_date |
| `Sale` | client_id, opportunity_id, offer_id, amount, currency, amount_eur (normalized), sale_date, product_ids, validated |
| `Product` | name, category, lifecycle_stage, unit_price, currency, tags |
| `Document` | source_type, file_path, document_class, raw_text, word_count, client_ref, language |
| `BaseEntity` | id (UUID), created_at, confidence, needs_review, source_trace_ids |

---

## Docker Deployment

`docker-compose.yml` defines four services:

| Service | Port | Notes |
|---------|------|-------|
| `backend` | 8000 | FastAPI; depends on redis + db |
| `frontend` | 8501 | Streamlit control tower (API-driven); env `IS_BACKOFFICE_API_URL=http://backend:8000` |
| `redis` | 6379 | Declared; not yet wired in code (future persistence) |
| `postgres` | 5432 | Declared; not yet wired in code (future persistence) |

The `frontend/app.py` control tower UI provides:
- Backend health check display
- One-click Pipeline and Forecast analytics fetchers
- Multi-agent cycle runner with source type selector, content input, and all mode flags

---

## Tests

42 tests across 13 test classes:

| Test Class | Coverage |
|-----------|----------|
| `TestModels` | All 7 canonical models (defaults, field values, enums) |
| `TestIngestion` | EmailConnector, TxtConnector, checksum, document class detection |
| `TestCleaning` | Normalizer (name/number/currency), Deduplicator, Validator, CleaningPipeline |
| `TestExtraction` | ExtractionEngine (all entity types, needs_review flag), ReviewQueue (enqueue/approve/reject) |
| `TestGraph` | GraphStore (upsert/get/stats/timeline), SemanticSearch, Relation model |
| `TestAnalytics` | PipelineScorer, Forecaster, AccountHealthScorer, OfferValidator, PortfolioAnalyzer |
| `TestReporting` | ReportGenerator (all 3 report types, JSON + HTML serialization) |
| `TestIngestionConnectors` | PDFConnector, WordConnector, ExcelConnector (bytes ingestion) |
| `TestOrchestration` | CommercialIntelligenceOS (full cycle, strict mode, error handling) |
| `TestMultiAgent` | MultiAgentOrchestrator (pipeline trace, alerts, status) |
| `TestRuntime` | DataIngestionLayer, DataProcessingCleaningLayer, KnowledgeGraphMemorySystem |
| `TestSchemas` | RunCycleRequest defaults, AgentRunResponse fields |
| API tests | `POST /orchestration/run` + `POST /orchestration/agents/run` via FastAPI test client |

---

## Key Dependencies

| Package | Role |
|---------|------|
| `fastapi` + `uvicorn` | REST API server |
| `pydantic` | Data models and validation |
| `streamlit` | UI framework |
| `pandas` + `numpy` | Data manipulation |
| `PyMuPDF` (fitz) | PDF text extraction |
| `python-docx` | Word document parsing |
| `openpyxl` + `xlrd` | Excel parsing (.xlsx and .xls) |
| `pdfplumber` | Alternative PDF parser |
| `python-pptx` | PowerPoint parsing |
| `beautifulsoup4` | HTML parsing |
| `chardet` | Charset auto-detection |
| `openai` | Optional AI enhancement |
| `pytesseract` + `Pillow` | OCR for image files |
| `striprtf` | RTF document parsing |
| `extract-msg` | Outlook `.msg` email parsing |
| `odfpy` | OpenDocument (.odt/.odp/.ods) parsing |
| `python-multipart` | Multipart file upload for FastAPI |
| `scikit-learn` | Available for future ML features |
| `spaCy` *(optional)* | Improved NER; install separately: `pip install spacy && python -m spacy download en_core_web_sm` |
