"""Ingestion API routes."""
from __future__ import annotations
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse

from backoffice.ingestion import (
    EmailConnector, PDFConnector, WordConnector, ExcelConnector, TxtConnector
)
from backoffice.cleaning.pipeline import CleaningPipeline
from backoffice.extraction.engine import ExtractionEngine
from backoffice.extraction.review_queue import ReviewQueue
from api.state import graph_store, review_queue

router = APIRouter(prefix="/ingest", tags=["ingestion"])
_pipeline = CleaningPipeline()
_extractor = ExtractionEngine()

_CONNECTORS = {
    "pdf": PDFConnector(),
    "docx": WordConnector(),
    "xlsx": ExcelConnector(),
    "txt": TxtConnector(),
}


@router.post("/file")
async def ingest_file(file: UploadFile = File(...)):
    """Ingest an uploaded file (PDF, DOCX, XLSX, TXT)."""
    ext = (file.filename or "").rsplit(".", 1)[-1].lower()
    connector = _CONNECTORS.get(ext)
    if not connector:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: .{ext}")

    raw_bytes = await file.read()
    records = connector.ingest(raw_bytes)
    cleaned, report = _pipeline.run(records)

    extracted_results = []
    for rec in cleaned:
        result = _extractor.extract(rec)
        if result.needs_review:
            review_queue.enqueue(result)
        extracted_results.append(result.model_dump())

    return JSONResponse({
        "file": file.filename,
        "records_ingested": len(records),
        "cleaning_report": {
            "total_in": report.total_in,
            "total_out": report.total_out,
            "duplicates_removed": report.duplicates_removed,
            "validation_errors": len(report.validation_errors),
        },
        "extraction_results": extracted_results,
    })


@router.post("/email")
async def ingest_email(payload: dict):
    """Ingest a raw email (JSON with subject, sender, body)."""
    connector = EmailConnector()
    records = connector.ingest(payload)
    cleaned, report = _pipeline.run(records)
    results = []
    for rec in cleaned:
        result = _extractor.extract(rec)
        if result.needs_review:
            review_queue.enqueue(result)
        results.append(result.model_dump())
    return JSONResponse({"records": len(records), "results": results})
