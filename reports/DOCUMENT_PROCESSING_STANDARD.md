DOCUMENT PROCESSING STANDARD

Purpose
-------
Standardize the ingestion pipeline so every uploaded artifact becomes a managed, indexed and project-linked knowledge asset suitable for AI-driven workflows and Truth Graph insertion.

Pipeline stages (end-to-end)
---------------------------
1. Ingest (upload)
   - Store binary in Object Store (S3 or local `data/` for dev).
   - Compute SHA256 (`compute_sha256` exists in [services/project_closeout_service.py](services/project_closeout_service.py)).

2. OCR (if required)
   - Run OCR for scanned PDFs (Tesseract or commercial OCR for scale).

3. Text extraction
   - Extract text and basic entities (use or extend [services/project_closeout_extractor.py](services/project_closeout_extractor.py)).

4. Metadata enrichment
   - Extract dates, amounts, emails, equipment ids, supplier names.

5. Classification
   - Classify document type (contract, invoice, drawing, report) and confidence.

6. Entity & relationship extraction
   - Extract named entities and candidate relations (document → project, supplier → PO, etc.).

7. Truth Graph ingestion
   - Create `graph_node` for document and `graph_edges` linking to project, suppliers, invoices.
   - Evidence: Graph primitives recommended in reports/PROJECT_DATABASE_SCHEMA_V2.md

8. Embedding & Knowledge Memory
   - Produce embeddings and upsert into Chroma/VectorDB with metadata including `project_id` and `confidence` (see `KnowledgeMemory` implementation).

9. AI summary & insight
   - Generate short auto-summary and candidate tags (LLM). Persist as `AI Insight` with `confidence` and `references`.

10. Project Assignment & indexing
   - Assign or recommend `canonical_project_id`.
   - If assignment confidence < threshold, flag for human review.

Required metadata model (minimum)
- `project_id` (canonical_project_id) — optional initially, required after assignment
- `customer_id` — optional
- `supplier_id` — optional
- `date` — best-effort extracted date
- `equipment` — extracted equipment id or name
- `tags` — suggested tags
- `confidence` — pipeline confidence score
- `source` — uploader or ingestion system
- `truth_status` — unverified/verified/disputed
- `file_hash`, `object_store_url`, `mime_type`, `size`

Idempotency and deduplication
------------------------------
- Use `file_hash` to detect duplicates; if duplicate exists, attach new provenance but do not re-ingest.

Error handling & quarantine
---------------------------
- Failed extractions are written to a `quarantine` area with a human review ticket. Keep original binary and logs.

Data contracts & APIs
--------------------
- POST /ingest/document → returns `{document_id, suggested_project_id, confidence}`
- GET /ingest/status/{id}
- POST /ingest/validate/{document_id} {project_id, validated_by}

Mapping to current repo
-----------------------
- Current lightweight extractor: [services/project_closeout_extractor.py](services/project_closeout_extractor.py) — suitable for prototypes but must be replaced by a resilient pipeline with OCR and entity extraction.
- `save_document` already computes hash and writes files ([services/project_closeout_service.py](services/project_closeout_service.py)) — extend to trigger ingestion pipeline and index into KnowledgeMemory.

Acceptance criteria
-------------------
- Any uploaded file must be searchable via project-scoped semantic search within 60 seconds for small files (<10MB) in dev.
- Documents with `confidence` < 0.6 must be flagged for review before being used as authoritative evidence.
