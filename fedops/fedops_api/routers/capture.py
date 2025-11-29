from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

from fedops_core.db.engine import get_db
from fedops_core.db.shipley_models import CapturePlan
from fedops_core.db.models import Proposal

router = APIRouter(
    prefix="/capture",
    tags=["capture"]
)

class CapturePlanUpdate(BaseModel):
    win_strategy: Optional[str] = None
    executive_summary_theme: Optional[str] = None
    customer_hot_buttons: Optional[List[Dict[str, Any]]] = None
    discriminators: Optional[List[Dict[str, Any]]] = None
    key_themes: Optional[List[str]] = None
    competitor_analysis_summary: Optional[str] = None
    teaming_strategy: Optional[str] = None
    partners: Optional[List[Dict[str, Any]]] = None
    action_items: Optional[List[Dict[str, Any]]] = None

@router.get("/proposals/{proposal_id}")
async def get_capture_plan(
    proposal_id: int,
    db: AsyncSession = Depends(get_db)
):
    # Check if proposal exists
    result = await db.execute(select(Proposal).where(Proposal.id == proposal_id))
    proposal = result.scalar_one_or_none()
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")

    # Get capture plan
    result = await db.execute(select(CapturePlan).where(CapturePlan.proposal_id == proposal_id))
    capture_plan = result.scalar_one_or_none()

    if not capture_plan:
        # Create empty plan if it doesn't exist
        capture_plan = CapturePlan(proposal_id=proposal_id)
        db.add(capture_plan)
        await db.commit()
        await db.refresh(capture_plan)

    return capture_plan

@router.patch("/proposals/{proposal_id}")
async def update_capture_plan(
    proposal_id: int,
    update_data: CapturePlanUpdate,
    db: AsyncSession = Depends(get_db)
):
    # Get capture plan
    result = await db.execute(select(CapturePlan).where(CapturePlan.proposal_id == proposal_id))
    capture_plan = result.scalar_one_or_none()

    if not capture_plan:
        # Should have been created by get, but just in case
        capture_plan = CapturePlan(proposal_id=proposal_id)
        db.add(capture_plan)
    
    # Update fields
    update_dict = update_data.dict(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(capture_plan, key, value)
    
    capture_plan.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(capture_plan)
    
    return capture_plan
