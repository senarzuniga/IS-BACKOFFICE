"""Entity extraction engine — rule-based with confidence scoring."""
from __future__ import annotations
import re
from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel

from backoffice.ingestion.base import RawRecord
from backoffice.models.client import Client
from backoffice.models.contact import Contact
from backoffice.models.offer import Offer
from backoffice.models.opportunity import Opportunity
from backoffice.models.sale import Sale
from backoffice.cleaning.normalizer import Normalizer


# ── Confidence thresholds ─────────────────────────────────────────────────────
REVIEW_THRESHOLD = 0.6
FINANCIAL_REVIEW_THRESHOLD = 0.75

_normalizer = Normalizer()

# Patterns
_EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
_PHONE_RE = re.compile(r"(?:\+?\d[\d\s\-\.]{7,14}\d)")
_AMOUNT_RE = re.compile(r"(?:€|\$|£|EUR|USD|GBP|MAD)?\s*[\d\s]{1,3}(?:[.,]\d{3})*(?:[.,]\d{1,2})?(?:\s*(?:€|\$|£|EUR|USD|GBP|MAD))?")
_DATE_RE = re.compile(r"\b(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4}|\d{4}[/\-\.]\d{1,2}[/\-\.]\d{1,2})\b")
_CLIENT_RE = re.compile(r"(?:client|société|company|customer|account)\s*[:\-]?\s*([A-Z][A-Za-z0-9\s&,.-]{2,50})", re.IGNORECASE)
_OFFER_RE = re.compile(r"(?:offre|offer|devis|quotation|proposal)\s*(?:n°|#|no\.?)?\s*([\w\-/]+)", re.IGNORECASE)
_AMOUNT_VALUE_RE = re.compile(r"([\d\s]{1,3}(?:[.,]\d{3})*(?:[.,]\d{1,2})?)")


class ExtractionResult(BaseModel):
    record_id: str
    clients: List[Dict[str, Any]] = []
    contacts: List[Dict[str, Any]] = []
    offers: List[Dict[str, Any]] = []
    opportunities: List[Dict[str, Any]] = []
    sales: List[Dict[str, Any]] = []
    needs_review: bool = False
    review_reasons: List[str] = []


class ExtractionEngine:
    """Extracts business entities from raw records using rule-based NLP."""

    def extract(self, record: RawRecord) -> ExtractionResult:
        text = record.raw_text or ""
        result = ExtractionResult(record_id=record.record_id)

        # Extract clients
        for match in _CLIENT_RE.finditer(text):
            name = match.group(1).strip()
            confidence = 0.7 if len(name) > 3 else 0.4
            result.clients.append({
                "name": name,
                "normalized_name": _normalizer.normalize_name(name),
                "confidence": confidence,
                "source_trace_ids": [record.record_id],
                "needs_review": confidence < REVIEW_THRESHOLD,
            })

        # Extract contacts (email + phone)
        emails = _EMAIL_RE.findall(text)
        phones = _PHONE_RE.findall(text)
        for em in set(emails):
            parts = em.split("@")[0].split(".")
            first = parts[0].title() if parts else ""
            last = parts[1].title() if len(parts) > 1 else ""
            result.contacts.append({
                "email": em,
                "first_name": first,
                "last_name": last,
                "confidence": 0.85,
                "source_trace_ids": [record.record_id],
                "client_id": "",
            })

        # Extract offers
        for match in _OFFER_RE.finditer(text):
            ref = match.group(1).strip()
            amounts = self._extract_amounts(text)
            total = amounts[0] if amounts else None
            confidence = 0.75 if total is not None else 0.5
            result.offers.append({
                "title": f"Offer {ref}",
                "total_value": total,
                "currency": _normalizer.detect_currency(text),
                "confidence": confidence,
                "source_trace_ids": [record.record_id],
                "client_id": "",
                "needs_review": confidence < FINANCIAL_REVIEW_THRESHOLD,
            })

        # Flag for review if financial data is uncertain
        for offer in result.offers:
            if offer.get("needs_review"):
                result.needs_review = True
                result.review_reasons.append(f"Offer confidence low: {offer['title']}")

        if not result.clients and not result.offers:
            result.needs_review = True
            result.review_reasons.append("No entities extracted")

        return result

    def _extract_amounts(self, text: str) -> List[float]:
        results = []
        for match in _AMOUNT_VALUE_RE.finditer(text):
            val = _normalizer.parse_number(match.group(1))
            if val is not None and val > 0:
                results.append(val)
        return results
