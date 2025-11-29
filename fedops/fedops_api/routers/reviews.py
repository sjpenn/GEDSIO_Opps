from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from fedops_core.db.engine import get_db
from fedops_core.services.review_service import ReviewService

router = APIRouter(
    prefix="/reviews",
    tags=["reviews"]
)

# Pydantic Models
class CommentCreate(BaseModel):
    text: str
    comment_type: str  # COMPLIANCE, CLARITY, STRATEGY, TECHNICAL
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    reviewer_name: str
    section_reference: Optional[str] = None

class CommentUpdate(BaseModel):
    status: str  # OPEN, ADDRESSED, RESOLVED

class ReviewComplete(BaseModel):
    outcome: str  # PASS, FAIL, CONDITIONAL
    decision_by: str

class ReviewStart(BaseModel):
    user_id: str

@router.post("/proposals/{proposal_id}/{review_type}/start")
async def start_review(
    proposal_id: int,
    review_type: str,
    request: ReviewStart,
    db: AsyncSession = Depends(get_db)
):
    """Start or retrieve a review gate (PINK, RED, GOLD)"""
    try:
        gate = await ReviewService.get_or_create_review_gate(
            db, proposal_id, review_type, request.user_id
        )
        return gate
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/proposals/{proposal_id}/{review_type}")
async def get_active_review(
    proposal_id: int,
    review_type: str,
    db: AsyncSession = Depends(get_db)
):
    """Get the active review gate for a specific type"""
    # We reuse get_or_create but with a dummy user_id if we just want to check existence
    # Or better, implement a get_active_gate in service. 
    # For now, we'll use get_or_create which is safe (idempotent)
    try:
        gate = await ReviewService.get_or_create_review_gate(
            db, proposal_id, review_type, "System"
        )
        # Fetch comments
        comments = await ReviewService.get_review_comments(db, gate.id)
        return {
            "gate": gate,
            "comments": comments
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/gates/{gate_id}/comments")
async def add_comment(
    gate_id: int,
    comment: CommentCreate,
    db: AsyncSession = Depends(get_db)
):
    """Add a comment to a review"""
    try:
        new_comment = await ReviewService.add_comment(
            db,
            gate_id,
            comment.text,
            comment.comment_type,
            comment.severity,
            comment.reviewer_name,
            comment.section_reference
        )
        return new_comment
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/comments/{comment_id}")
async def update_comment(
    comment_id: int,
    update: CommentUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update comment status"""
    try:
        updated_comment = await ReviewService.update_comment_status(
            db, comment_id, update.status
        )
        return updated_comment
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/gates/{gate_id}/complete")
async def complete_review(
    gate_id: int,
    completion: ReviewComplete,
    db: AsyncSession = Depends(get_db)
):
    """Complete a review gate"""
    try:
        gate = await ReviewService.complete_review(
            db, gate_id, completion.outcome, completion.decision_by
        )
        return gate
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
