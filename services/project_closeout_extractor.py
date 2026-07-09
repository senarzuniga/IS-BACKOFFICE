"""Simple extraction utilities for Project Closeout documents.

This is intentionally lightweight: it uses PyPDF2 when available and
falls back to reading plain text. Entity extraction is heuristic-based
and returns draft candidates for human review.
"""
from __future__ import annotations

import re
from typing import Dict, List


def _extract_entities(text: str) -> Dict[str, List[str]]:
    # Dates like 2026-07-07 or 07/07/2026 or 7/7/26
    date_rx = re.compile(r"\b\d{4}-\d{2}-\d{2}\b|\b\d{1,2}/\d{1,2}/\d{2,4}\b")
    # Amounts with currency symbols like €5,000.00 or $1200
    amount_rx = re.compile(r"[€$£]\s*[\d\.\,]+|\d[\d\.,]+\s*(?:EUR|USD|€|€)\b")
    # Simple email matcher
    email_rx = re.compile(r"[\w.\-]+@[\w.\-]+\.[a-zA-Z]{2,}")

    dates = list({m.group(0) for m in date_rx.finditer(text)})
    amounts = list({m.group(0) for m in amount_rx.finditer(text)})
    emails = list({m.group(0) for m in email_rx.finditer(text)})

    return {"dates": dates, "amounts": amounts, "emails": emails}


def extract_text_from_path(path: str) -> str:
    """Try to extract text from common document types.

    For PDFs this uses PyPDF2 if available. For other files we attempt
    a simple text decode.
    """
    try:
        from PyPDF2 import PdfReader

        if path.lower().endswith(".pdf"):
            reader = PdfReader(path)
            pages = []
            for p in reader.pages:
                try:
                    t = p.extract_text() or ""
                except Exception:
                    t = ""
                pages.append(t)
            return "\n".join(pages)
    except Exception:
        # PyPDF2 not available or PDF parsing failed; fall back
        pass

    # generic text fallback
    try:
        with open(path, "rb") as f:
            data = f.read()
            try:
                return data.decode("utf-8")
            except Exception:
                try:
                    return data.decode("latin-1")
                except Exception:
                    return ""
    except Exception:
        return ""


def extract_text_and_entities_from_file(path: str) -> Dict:
    text = extract_text_from_path(path)
    entities = _extract_entities(text)
    return {"text_preview": text[:4000], "entities": entities}
