"""Review queue API routes."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from api.state import review_queue

router = APIRouter(prefix="/review", tags=["review"])


class ReviewDecision(BaseModel):
    notes: str = ""


@router.get("/pending")
def list_pending():
    return [i.model_dump() for i in review_queue.pending()]


@router.post("/{item_id}/approve")
def approve(item_id: str, body: ReviewDecision = ReviewDecision()):
    if not review_queue.approve(item_id, body.notes):
        raise HTTPException(status_code=404, detail="Review item not found")
    return {"status": "approved", "item_id": item_id}


@router.post("/{item_id}/reject")
def reject(item_id: str, body: ReviewDecision = ReviewDecision()):
    if not review_queue.reject(item_id, body.notes):
        raise HTTPException(status_code=404, detail="Review item not found")
    return {"status": "rejected", "item_id": item_id}
