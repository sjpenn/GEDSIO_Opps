from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from fedops_core.db.engine import get_db
from fedops_core.db.models import OpportunityPipeline, Opportunity

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
def watch_opportunity(opportunity_id: int, db: Session = Depends(get_db)):
    # Check if opportunity exists
    opp = db.query(Opportunity).filter(Opportunity.id == opportunity_id).first()
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")
        
    # Check if already watching
    existing = db.query(OpportunityPipeline).filter(OpportunityPipeline.opportunity_id == opportunity_id).first()
    if existing:
        return {"message": "Already watching this opportunity", "id": existing.id}
        
    pipeline_item = OpportunityPipeline(
        opportunity_id=opportunity_id,
        status="WATCHING",
        stage="QUALIFICATION"
    )
    db.add(pipeline_item)
    db.commit()
    db.refresh(pipeline_item)
    return pipeline_item

@router.get("/")
def get_pipeline(db: Session = Depends(get_db)):
    items = db.query(OpportunityPipeline).all()
    # Enrich with opportunity details
    result = []
    for item in items:
        opp = db.query(Opportunity).filter(Opportunity.id == item.opportunity_id).first()
        result.append({
            "pipeline": item,
            "opportunity": opp
        })
    return result

@router.get("/{opportunity_id}")
def get_pipeline_item(opportunity_id: int, db: Session = Depends(get_db)):
    item = db.query(OpportunityPipeline).filter(OpportunityPipeline.opportunity_id == opportunity_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Pipeline item not found")
    return item

@router.put("/{opportunity_id}")
def update_pipeline_item(opportunity_id: int, update_data: PipelineItemUpdate, db: Session = Depends(get_db)):
    item = db.query(OpportunityPipeline).filter(OpportunityPipeline.opportunity_id == opportunity_id).first()
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
        
    db.commit()
    db.refresh(item)
    return item

@router.delete("/{opportunity_id}")
def unwatch_opportunity(opportunity_id: int, db: Session = Depends(get_db)):
    item = db.query(OpportunityPipeline).filter(OpportunityPipeline.opportunity_id == opportunity_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Pipeline item not found")
        
    db.delete(item)
    db.commit()
    return {"message": "Stopped watching opportunity"}
