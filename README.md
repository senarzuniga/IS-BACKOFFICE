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

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- Docker and Docker Compose
- Node.js and npm (for frontend development)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/is-backoffice.git
   cd is-backoffice
   ```

2. **Set up a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Build and run Docker containers:**
   ```bash
   docker compose up --build
   ```

5. **Access the application:**
   - FastAPI: [http://localhost:8000/docs](http://localhost:8000/docs)
   - Streamlit: [http://localhost:8501](http://localhost:8501)

### Configuration

- **Environment Variables:**
  - Create a `.env` file in the root directory to configure environment variables.
  - Example:
    ```
    DATABASE_URL=postgresql://user:password@localhost/dbname
    REDIS_URL=redis://localhost:6379
    OPENAI_API_KEY=your-openai-api-key
    ```

- **Frontend Configuration:**
  - Navigate to the `frontend` directory and install dependencies:
    ```bash
    cd frontend
    npm install
    ```
  - Start the frontend development server:
    ```bash
    npm start
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
| POST | `/ingest/file` | Upload a PDF, DO
