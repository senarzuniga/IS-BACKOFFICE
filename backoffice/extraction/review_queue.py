"""Human review queue for low-confidence extractions."""
from __future__ import annotations
from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field
from backoffice.models.base import _uuid, _now
from .engine import ExtractionResult


class ReviewItem(BaseModel):
    item_id: str = Field(default_factory=_uuid)
    record_id: str
    result: ExtractionResult
    review_reasons: List[str] = []
    status: str = "pending"  # pending | approved | rejected | corrected
    created_at: datetime = Field(default_factory=_now)
    reviewed_at: Optional[datetime] = None
    reviewer_notes: Optional[str] = None


class ReviewQueue:
    """In-memory queue for items needing human review."""

    def __init__(self):
        self._items: List[ReviewItem] = []

    def enqueue(self, result: ExtractionResult) -> ReviewItem:
        item = ReviewItem(
            record_id=result.record_id,
            result=result,
            review_reasons=result.review_reasons,
        )
        self._items.append(item)
        return item

    def pending(self) -> List[ReviewItem]:
        return [i for i in self._items if i.status == "pending"]

    def approve(self, item_id: str, notes: str = "") -> bool:
        for item in self._items:
            if item.item_id == item_id:
                item.status = "approved"
                item.reviewed_at = datetime.now(timezone.utc)
                item.reviewer_notes = notes
                return True
        return False

    def reject(self, item_id: str, notes: str = "") -> bool:
        for item in self._items:
            if item.item_id == item_id:
                item.status = "rejected"
                item.reviewed_at = datetime.now(timezone.utc)
                item.reviewer_notes = notes
                return True
        return False

    def all_items(self) -> List[ReviewItem]:
        return list(self._items)
