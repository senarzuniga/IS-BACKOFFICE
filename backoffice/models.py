from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
import uuid


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


@dataclass
class RawRecord:
    source_type: str
    content: str
    source_id: str
    timestamp: str = field(default_factory=utc_now_iso)
    client_reference: str | None = None
    classification: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Opportunity:
    id: str
    client: str
    description: str
    amount: float
    close_date: str | None


@dataclass
class Offer:
    id: str
    client: str
    description: str
    price: float
    date: str | None


@dataclass
class Sale:
    id: str
    client: str
    product: str
    value: float
    date: str | None


@dataclass
class Customer:
    id: str
    name: str
    contacts: list[str] = field(default_factory=list)


@dataclass
class ProcessingResult:
    cleaned_records: list[RawRecord]
    dropped_duplicates: int
    missing_fields: list[str]
    validation_errors: list[str]


@dataclass
class EntityBundle:
    customers: list[Customer]
    opportunities: list[Opportunity]
    offers: list[Offer]
    sales: list[Sale]
