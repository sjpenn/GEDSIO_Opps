from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from fedops_core.db.engine import get_db
from fedops_core.db.models import OpportunityPipeline, Opportunity, OpportunityScore

router = APIRouter(
    prefix="/api/v1/pipeline",
    tags=["pipeline"]
)

class PipelineItemCreate(BaseModel):
    opportunity_id: int
    status: str = "WATCHING"
    stage: str = "QUALIFICATION"

class PipelineItemUpdate(BaseModel):
    status: Optional[str] = None
    stage: Optional[str] = None
    questions_due_date: Optional[datetime] = None
    proposal_due_date: Optional[datetime] = None
    submission_instructions: Optional[str] = None
    notes: Optional[str] = None
    required_artifacts: Optional[List[str]] = None

@router.post("/{opportunity_id}/watch")
async def watch_opportunity(opportunity_id: int, db: AsyncSession = Depends(get_db)):
    # Check if opportunity exists
    result = await db.execute(select(Opportunity).filter(Opportunity.id == opportunity_id))
    opp = result.scalar_one_or_none()
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")
        
    # Check if already watching
    result = await db.execute(select(OpportunityPipeline).filter(OpportunityPipeline.opportunity_id == opportunity_id))
    existing = result.scalar_one_or_none()
    if existing:
        return {"message": "Already watching this opportunity", "id": existing.id}
        
    pipeline_item = OpportunityPipeline(
        opportunity_id=opportunity_id,
        status="WATCHING",
        stage="QUALIFICATION"
    )
    db.add(pipeline_item)
    await db.commit()
    await db.refresh(pipeline_item)
    return pipeline_item

@router.get("/")
async def get_pipeline(include_archived: bool = Query(False), db: AsyncSession = Depends(get_db)):
    # Filter archived items unless explicitly requested
    query = select(OpportunityPipeline)
    if not include_archived:
        query = query.filter(OpportunityPipeline.archived == False)
    
    result = await db.execute(query)
    items = result.scalars().all()
    # Enrich with opportunity and proposal details
    enriched_result = []
    for item in items:
        opp_result = await db.execute(select(Opportunity).filter(Opportunity.id == item.opportunity_id))
        opp = opp_result.scalar_one_or_none()
        
        # Get proposal if exists
        from fedops_core.db.models import Proposal
        proposal_result = await db.execute(select(Proposal).filter(Proposal.opportunity_id == item.opportunity_id))
        proposal = proposal_result.scalar_one_or_none()
        
        # Get opportunity score if exists
        score_result = await db.execute(select(OpportunityScore).filter(OpportunityScore.opportunity_id == item.opportunity_id))
        score = score_result.scalar_one_or_none()
        
        # Get bid criteria if exists (this is the score shown on Bid Decision page)
        from fedops_core.db.shipley_models import BidNoGidCriteria
        bid_criteria_result = await db.execute(select(BidNoGidCriteria).filter(BidNoGidCriteria.opportunity_id == item.opportunity_id))
        bid_criteria = bid_criteria_result.scalar_one_or_none()
        
        # Prioritize scores: 1) Submitted bid_decision_score, 2) Bid Criteria score, 3) Automated analysis score
        display_score = None
        score_source = None
        if proposal and proposal.bid_decision_score is not None:
            # User has submitted their official decision - use that score
            display_score = proposal.bid_decision_score
            score_source = "bid_decision"
        elif bid_criteria and bid_criteria.weighted_score is not None:
            # Bid criteria exists (shown on Bid Decision page) - use that
            display_score = bid_criteria.weighted_score  
            score_source = "bid_criteria"
        elif score and score.weighted_score is not None:
            # Fall back to initial automated analysis score
            display_score = score.weighted_score
            score_source = "automated_analysis"
        
        enriched_result.append({
            "pipeline": item,
            "opportunity": opp,
            "proposal": {
                "id": proposal.id if proposal else None,
                "shipley_phase": proposal.shipley_phase if proposal else None,
                "capture_manager_id": proposal.capture_manager_id if proposal else None,
                "bid_decision_score": proposal.bid_decision_score if proposal else None
            } if proposal else None,
            "score": {
                "weighted_score": score.weighted_score if score else None,
                "go_no_go_decision": score.go_no_go_decision if score else None
            } if score else None,
            "display_score": display_score,
            "score_source": score_source
        })
    return enriched_result

@router.get("/{opportunity_id}")
async def get_pipeline_item(opportunity_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(OpportunityPipeline).filter(OpportunityPipeline.opportunity_id == opportunity_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Pipeline item not found")
    return item

@router.put("/{opportunity_id}")
async def update_pipeline_item(opportunity_id: int, update_data: PipelineItemUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(OpportunityPipeline).filter(OpportunityPipeline.opportunity_id == opportunity_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Pipeline item not found")
        
    if update_data.status is not None:
        item.status = update_data.status
    if update_data.stage is not None:
        item.stage = update_data.stage
    if update_data.questions_due_date is not None:
        item.questions_due_date = update_data.questions_due_date
    if update_data.proposal_due_date is not None:
        item.proposal_due_date = update_data.proposal_due_date
    if update_data.submission_instructions is not None:
        item.submission_instructions = update_data.submission_instructions
    if update_data.notes is not None:
        item.notes = update_data.notes
    if update_data.required_artifacts is not None:
        item.required_artifacts = update_data.required_artifacts
        
    await db.commit()
    await db.refresh(item)
    return item

@router.delete("/{opportunity_id}")
async def unwatch_opportunity(opportunity_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(OpportunityPipeline).filter(OpportunityPipeline.opportunity_id == opportunity_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Pipeline item not found")
        
    await db.delete(item)
    await db.commit()
    return {"message": "Stopped watching opportunity"}

@router.post("/{opportunity_id}/archive")
async def archive_opportunity(opportunity_id: int, archived_by: str = Query("system"), db: AsyncSession = Depends(get_db)):
    """Archive a pipeline item - removes from active view but keeps the record"""
    result = await db.execute(select(OpportunityPipeline).filter(OpportunityPipeline.opportunity_id == opportunity_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Pipeline item not found")
    
    item.archived = True
    item.archived_at = datetime.utcnow()
    item.archived_by = archived_by
    
    await db.commit()
    await db.refresh(item)
    return {"message": "Opportunity archived", "item": item}

@router.post("/{opportunity_id}/unarchive")
async def unarchive_opportunity(opportunity_id: int, db: AsyncSession = Depends(get_db)):
    """Unarchive a pipeline item - returns it to active view"""
    result = await db.execute(select(OpportunityPipeline).filter(OpportunityPipeline.opportunity_id == opportunity_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Pipeline item not found")
    
    item.archived = False
    item.archived_at = None
    item.archived_by = None
    
    await db.commit()
    await db.refresh(item)
    return {"message": "Opportunity unarchived", "item": item}

@router.get("/archived")
async def get_archived_pipeline(db: AsyncSession = Depends(get_db)):
    """Get only archived pipeline items"""
    result = await db.execute(select(OpportunityPipeline).filter(OpportunityPipeline.archived == True))
    items = result.scalars().all()
    
    # Enrich with opportunity details
    enriched_result = []
    for item in items:
        opp_result = await db.execute(select(Opportunity).filter(Opportunity.id == item.opportunity_id))
        opp = opp_result.scalar_one_or_none()
        
        enriched_result.append({
            "pipeline": item,
            "opportunity": opp
        })
    
    return enriched_result
