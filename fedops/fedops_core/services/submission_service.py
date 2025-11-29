"""
Submission Service for Phase 6: Submission & Post-Submittal
Handles proposal submission, award tracking, and lessons learned
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional, Dict, Any
from datetime import datetime

from fedops_core.db.shipley_models import Submission, Award, LessonsLearned
from fedops_core.db.models import Proposal


class SubmissionService:
    """Service to manage proposal submissions, awards, and lessons learned"""
    
    @staticmethod
    async def submit_proposal(
        db: AsyncSession,
        proposal_id: int,
        submission_date: datetime,
        method: str,
        submitted_by: str,
        tracking_number: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Submission:
        """Record proposal submission"""
        # Check if already submitted
        result = await db.execute(
            select(Submission).where(Submission.proposal_id == proposal_id)
        )
        submission = result.scalar_one_or_none()
        
        if submission:
            # Update existing submission
            submission.submission_date = submission_date
            submission.submission_method = method
            submission.tracking_number = tracking_number
            submission.submitted_by = submitted_by
            submission.submission_notes = notes
            submission.updated_at = datetime.utcnow()
        else:
            # Create new submission
            submission = Submission(
                proposal_id=proposal_id,
                submission_date=submission_date,
                submission_method=method,
                tracking_number=tracking_number,
                submitted_by=submitted_by,
                submission_notes=notes
            )
            db.add(submission)
        
        await db.commit()
        await db.refresh(submission)
        return submission

    @staticmethod
    async def record_award(
        db: AsyncSession,
        proposal_id: int,
        status: str,
        award_date: Optional[datetime] = None,
        contract_number: Optional[str] = None,
        contract_value: Optional[float] = None,
        notes: Optional[str] = None
    ) -> Award:
        """Record award outcome"""
        result = await db.execute(
            select(Award).where(Award.proposal_id == proposal_id)
        )
        award = result.scalar_one_or_none()
        
        if award:
            # Update existing award
            award.status = status
            award.award_date = award_date
            award.contract_number = contract_number
            award.contract_value = contract_value
            award.award_notes = notes
            award.updated_at = datetime.utcnow()
        else:
            # Create new award
            award = Award(
                proposal_id=proposal_id,
                status=status,
                award_date=award_date,
                contract_number=contract_number,
                contract_value=contract_value,
                award_notes=notes
            )
            db.add(award)
        
        await db.commit()
        await db.refresh(award)
        return award

    @staticmethod
    async def record_debrief(
        db: AsyncSession,
        proposal_id: int,
        debrief_date: datetime,
        notes: str
    ) -> Award:
        """Add debrief notes to award"""
        result = await db.execute(
            select(Award).where(Award.proposal_id == proposal_id)
        )
        award = result.scalar_one_or_none()
        
        if not award:
            raise ValueError(f"Award record for proposal {proposal_id} not found")
        
        award.debrief_date = debrief_date
        award.debrief_notes = notes
        award.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(award)
        return award

    @staticmethod
    async def add_lesson_learned(
        db: AsyncSession,
        proposal_id: int,
        category: str,
        observation: str,
        recorded_by: str,
        impact: Optional[str] = None,
        recommendation: Optional[str] = None
    ) -> LessonsLearned:
        """Add a lesson learned"""
        lesson = LessonsLearned(
            proposal_id=proposal_id,
            category=category,
            observation=observation,
            impact=impact,
            recommendation=recommendation,
            recorded_by=recorded_by
        )
        db.add(lesson)
        await db.commit()
        await db.refresh(lesson)
        return lesson

    @staticmethod
    async def get_lessons_learned(
        db: AsyncSession,
        proposal_id: int
    ) -> List[LessonsLearned]:
        """Get all lessons learned for a proposal"""
        result = await db.execute(
            select(LessonsLearned).where(LessonsLearned.proposal_id == proposal_id)
        )
        return result.scalars().all()

    @staticmethod
    async def get_submission_details(
        db: AsyncSession,
        proposal_id: int
    ) -> Dict[str, Any]:
        """Get all Phase 6 details for a proposal"""
        # Get submission
        submission_result = await db.execute(
            select(Submission).where(Submission.proposal_id == proposal_id)
        )
        submission = submission_result.scalar_one_or_none()
        
        # Get award
        award_result = await db.execute(
            select(Award).where(Award.proposal_id == proposal_id)
        )
        award = award_result.scalar_one_or_none()
        
        # Get lessons
        lessons = await SubmissionService.get_lessons_learned(db, proposal_id)
        
        return {
            "submission": submission,
            "award": award,
            "lessons_learned": lessons
        }
