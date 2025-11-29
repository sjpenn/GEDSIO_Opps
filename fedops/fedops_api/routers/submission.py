from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from fedops_core.db.engine import get_db
from fedops_core.services.submission_service import SubmissionService

router = APIRouter(
    prefix="/submission",
    tags=["submission"]
)

# Pydantic Models
class SubmissionCreate(BaseModel):
    submission_date: datetime
    method: str
    submitted_by: str
    tracking_number: Optional[str] = None
    notes: Optional[str] = None

class AwardCreate(BaseModel):
    status: str
    award_date: Optional[datetime] = None
    contract_number: Optional[str] = None
    contract_value: Optional[float] = None
    notes: Optional[str] = None

class DebriefCreate(BaseModel):
    debrief_date: datetime
    notes: str

class LessonCreate(BaseModel):
    category: str
    observation: str
    recorded_by: str
    impact: Optional[str] = None
    recommendation: Optional[str] = None


@router.post("/proposals/{proposal_id}/submit")
async def submit_proposal(
    proposal_id: int,
    submission: SubmissionCreate,
    db: AsyncSession = Depends(get_db)
):
    """Record proposal submission"""
    try:
        result = await SubmissionService.submit_proposal(
            db,
            proposal_id,
            submission.submission_date,
            submission.method,
            submission.submitted_by,
            submission.tracking_number,
            submission.notes
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/proposals/{proposal_id}/award")
async def record_award(
    proposal_id: int,
    award: AwardCreate,
    db: AsyncSession = Depends(get_db)
):
    """Record award outcome"""
    try:
        result = await SubmissionService.record_award(
            db,
            proposal_id,
            award.status,
            award.award_date,
            award.contract_number,
            award.contract_value,
            award.notes
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/proposals/{proposal_id}/debrief")
async def record_debrief(
    proposal_id: int,
    debrief: DebriefCreate,
    db: AsyncSession = Depends(get_db)
):
    """Add debrief notes"""
    try:
        result = await SubmissionService.record_debrief(
            db,
            proposal_id,
            debrief.debrief_date,
            debrief.notes
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/proposals/{proposal_id}/lessons")
async def add_lesson_learned(
    proposal_id: int,
    lesson: LessonCreate,
    db: AsyncSession = Depends(get_db)
):
    """Add a lesson learned"""
    try:
        result = await SubmissionService.add_lesson_learned(
            db,
            proposal_id,
            lesson.category,
            lesson.observation,
            lesson.recorded_by,
            lesson.impact,
            lesson.recommendation
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/proposals/{proposal_id}")
async def get_submission_details(
    proposal_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get all Phase 6 details for a proposal"""
    try:
        result = await SubmissionService.get_submission_details(db, proposal_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
