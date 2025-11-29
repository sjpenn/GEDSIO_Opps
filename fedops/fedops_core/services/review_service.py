"""
Review Service for Shipley Proposal Reviews
Handles Pink Team, Red Team, and Gold Team review logic
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import List, Optional, Dict, Any
from datetime import datetime

from fedops_core.db.shipley_models import ReviewGate, ReviewComment
from fedops_core.db.models import Proposal

class ReviewService:
    """Service to manage proposal reviews and comments"""
    
    @staticmethod
    async def get_or_create_review_gate(
        db: AsyncSession,
        proposal_id: int,
        review_type: str,  # PINK, RED, GOLD
        user_id: str
    ) -> ReviewGate:
        """Get existing review gate or create a new one"""
        # Check for existing open gate
        result = await db.execute(
            select(ReviewGate).where(
                ReviewGate.proposal_id == proposal_id,
                ReviewGate.review_type == review_type,
                ReviewGate.gate_type == "REVIEW"
            )
        )
        gate = result.scalar_one_or_none()
        
        if not gate:
            # Create new gate
            gate = ReviewGate(
                proposal_id=proposal_id,
                gate_type="REVIEW",
                review_type=review_type,
                outcome="PENDING",
                decision_by=user_id,
                details={
                    "status": "IN_PROGRESS",
                    "started_at": datetime.utcnow().isoformat()
                }
            )
            db.add(gate)
            await db.commit()
            await db.refresh(gate)
            
        return gate

    @staticmethod
    async def get_review_comments(
        db: AsyncSession,
        gate_id: int
    ) -> List[ReviewComment]:
        """Get all comments for a review gate"""
        result = await db.execute(
            select(ReviewComment).where(ReviewComment.review_gate_id == gate_id)
        )
        return result.scalars().all()

    @staticmethod
    async def add_comment(
        db: AsyncSession,
        gate_id: int,
        text: str,
        comment_type: str,
        severity: str,
        reviewer_name: str,
        section_reference: Optional[str] = None
    ) -> ReviewComment:
        """Add a new review comment"""
        comment = ReviewComment(
            review_gate_id=gate_id,
            comment_text=text,
            comment_type=comment_type,
            severity=severity,
            reviewer_name=reviewer_name,
            section_reference=section_reference,
            status="OPEN"
        )
        db.add(comment)
        await db.commit()
        await db.refresh(comment)
        return comment

    @staticmethod
    async def update_comment_status(
        db: AsyncSession,
        comment_id: int,
        status: str
    ) -> ReviewComment:
        """Update comment status (e.g. RESOLVED)"""
        result = await db.execute(
            select(ReviewComment).where(ReviewComment.id == comment_id)
        )
        comment = result.scalar_one_or_none()
        
        if not comment:
            raise ValueError(f"Comment {comment_id} not found")
            
        comment.status = status
        comment.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(comment)
        return comment

    @staticmethod
    async def complete_review(
        db: AsyncSession,
        gate_id: int,
        outcome: str,
        decision_by: str
    ) -> ReviewGate:
        """Complete a review gate"""
        result = await db.execute(
            select(ReviewGate).where(ReviewGate.id == gate_id)
        )
        gate = result.scalar_one_or_none()
        
        if not gate:
            raise ValueError(f"Gate {gate_id} not found")
            
        gate.outcome = outcome
        gate.decision_by = decision_by
        gate.decision_date = datetime.utcnow()
        
        # Update details
        details = gate.details or {}
        details["status"] = "COMPLETED"
        details["completed_at"] = datetime.utcnow().isoformat()
        gate.details = details  # Reassign to trigger update if needed
        
        await db.commit()
        await db.refresh(gate)
        return gate
