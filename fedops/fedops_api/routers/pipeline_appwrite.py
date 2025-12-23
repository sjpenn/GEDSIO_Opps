"""
Pipeline Router - Appwrite Version

API endpoints for pipeline management using Appwrite database.
Manages opportunities being tracked and moved through the proposal process.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from datetime import datetime
import logging

from fedops_core.services.additional_repositories import OpportunityPipelinesRepository
from fedops_core.services.opportunities_repository import OpportunitiesRepository
from fedops_core.services.proposals_repository import ProposalsRepository
from fedops_core.services.additional_repositories import OpportunityScoresRepository
from pydantic import BaseModel

router = APIRouter()
logger = logging.getLogger(__name__)


class PipelineItemUpdate(BaseModel):
    status: Optional[str] = None
    stage: Optional[str] = None
    questions_due_date: Optional[datetime] = None
    proposal_due_date: Optional[datetime] = None
    submission_instructions: Optional[str] = None
    notes: Optional[str] = None


@router.get("/")
async def get_pipeline(include_archived: bool = Query(False)):
    """
    Get all pipeline items with enriched opportunity and proposal data.
    
    Filters archived items by default unless explicitly requested.
    """
    pipeline_repo = OpportunityPipelinesRepository()
    opp_repo = OpportunitiesRepository()
    proposals_repo = ProposalsRepository()
    scores_repo = OpportunityScoresRepository()
    
    try:
        # Build queries to filter archived items
        from appwrite.query import Query as AppwriteQuery
        
        queries = []
        if not include_archived:
            queries.append(AppwriteQuery.equal("archived", False))
        
        # Get pipeline items with filtering
        result = await pipeline_repo.list(queries=queries, limit=1000)
        items = result.get("documents", [])
        
        enriched_result = []
        
        for item in items:
            opportunity_id = item.get("opportunity_id")
            
            # Get opportunity data
            opportunity = await opp_repo.get(opportunity_id)
            
            # Get proposal data if exists
            proposal = await proposals_repo.get_by_opportunity(opportunity_id)
            
            # Get score data if exists
            score = await scores_repo.get_by_opportunity(opportunity_id)
            
            # Prioritize scores: 1) Submitted bid_decision_score, 2) Automated analysis score
            display_score = None
            score_source = None
            if proposal and proposal.get("bid_decision_score") is not None:
                display_score = proposal["bid_decision_score"]
                score_source = "bid_decision"
            elif score and score.get("weighted_score") is not None:
                display_score = score["weighted_score"]
                score_source = "automated_analysis"
            
            enriched_result.append({
                "pipeline": item,
                "opportunity": opportunity,
                "proposal": {
                    "id": proposal.get("id") if proposal else None,
                    "current_stage": proposal.get("current_stage") if proposal else None,
                    "bid_decision_score": proposal.get("bid_decision_score") if proposal else None
                } if proposal else None,
                "score": {
                    "weighted_score": score.get("weighted_score") if score else None,
                    "go_no_go_decision": score.get("go_no_go_decision") if score else None
                } if score else None,
                "display_score": display_score,
                "score_source": score_source
            })
        
        return enriched_result
        
    except Exception as e:
        logger.error(f"Error getting pipeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/archived")
async def get_archived_pipeline():
    """Get only archived pipeline items."""
    return await get_pipeline(include_archived=True)


@router.get("/{opportunity_id}")
async def get_pipeline_item(opportunity_id: str):
    """
    Get pipeline item for a specific opportunity.
    
    Returns None instead of 404 to avoid browser console errors when checking status.
    """
    pipeline_repo = OpportunityPipelinesRepository()
    
    try:
        item = await pipeline_repo.get_by_opportunity(opportunity_id)
        return item  # Returns None if not found
    except Exception as e:
        logger.error(f"Error getting pipeline item for opportunity {opportunity_id}: {e}")
        return None


@router.post("/{opportunity_id}/watch")
async def watch_opportunity(opportunity_id: str):
    """
    Add an opportunity to the pipeline (start watching it).
    
    Returns existing entry if already watching.
    """
    opp_repo = OpportunitiesRepository()
    pipeline_repo = OpportunityPipelinesRepository()
    
    # Verify opportunity exists
    opportunity = await opp_repo.get(opportunity_id)
    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    
    # Check if already watching
    existing = await pipeline_repo.get_by_opportunity(opportunity_id)
    if existing:
        return {
            "message": "Already watching this opportunity",
            "id": existing["id"]
        }
    
    try:
        # Create pipeline entry
        pipeline_item = await pipeline_repo.create({
            "opportunity_id": opportunity_id,
            "status": "WATCHING",
            "stage": "QUALIFICATION",
            "archived": False
        })
        
        return pipeline_item
        
    except Exception as e:
        logger.error(f"Error watching opportunity {opportunity_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{opportunity_id}")
async def update_pipeline_item(opportunity_id: str, update_data: PipelineItemUpdate):
    """Update a pipeline item's status, stage, notes, etc."""
    pipeline_repo = OpportunityPipelinesRepository()
    
    # Get existing item
    item = await pipeline_repo.get_by_opportunity(opportunity_id)
    if not item:
        raise HTTPException(status_code=404, detail="Pipeline item not found")
    
    try:
        # Build update dict with only provided fields
        update_dict = {}
        
        if update_data.status is not None:
            update_dict["status"] = update_data.status
        if update_data.stage is not None:
            update_dict["stage"] = update_data.stage
        if update_data.questions_due_date is not None:
            update_dict["questions_due_date"] = update_data.questions_due_date.isoformat()
        if update_data.proposal_due_date is not None:
            update_dict["proposal_due_date"] = update_data.proposal_due_date.isoformat()
        if update_data.submission_instructions is not None:
            update_dict["submission_instructions"] = update_data.submission_instructions
        if update_data.notes is not None:
            update_dict["notes"] = update_data.notes
        
        # Update the item
        updated_item = await pipeline_repo.update(item["id"], update_dict)
        return updated_item
        
    except Exception as e:
        logger.error(f"Error updating pipeline item for opportunity {opportunity_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{opportunity_id}")
async def unwatch_opportunity(opportunity_id: str):
    """Remove an opportunity from the pipeline (stop watching)."""
    pipeline_repo = OpportunityPipelinesRepository()
    
    item = await pipeline_repo.get_by_opportunity(opportunity_id)
    if not item:
        raise HTTPException(status_code=404, detail="Pipeline item not found")
    
    try:
        await pipeline_repo.delete(item["id"])
        return {"message": "Stopped watching opportunity"}
        
    except Exception as e:
        logger.error(f"Error unwatching opportunity {opportunity_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{opportunity_id}/archive")
async def archive_opportunity(opportunity_id: str, archived_by: str = Query("system")):
    """Archive a pipeline item - removes from active view but keeps the record."""
    pipeline_repo = OpportunityPipelinesRepository()
    
    item = await pipeline_repo.get_by_opportunity(opportunity_id)
    if not item:
        raise HTTPException(status_code=404, detail="Pipeline item not found")
    
    try:
        updated_item = await pipeline_repo.update(item["id"], {
            "archived": True,
            "archived_at": datetime.utcnow().isoformat(),
            "archived_by": archived_by
        })
        
        return {
            "message": "Opportunity archived",
            "item": updated_item
        }
        
    except Exception as e:
        logger.error(f"Error archiving opportunity {opportunity_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{opportunity_id}/unarchive")
async def unarchive_opportunity(opportunity_id: str):
    """Unarchive a pipeline item - returns it to active view."""
    pipeline_repo = OpportunityPipelinesRepository()
    
    item = await pipeline_repo.get_by_opportunity(opportunity_id)
    if not item:
        raise HTTPException(status_code=404, detail="Pipeline item not found")
    
    try:
        updated_item = await pipeline_repo.update(item["id"], {
            "archived": False,
            "archived_at": None,
            "archived_by": None
        })
        
        return {
            "message": "Opportunity unarchived",
            "item": updated_item
        }
        
    except Exception as e:
        logger.error(f"Error unarchiving opportunity {opportunity_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
