from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Dict, Any

from fedops_api.deps import get_db
from fedops_core.db.models import Proposal, ProposalStage
from fedops_agents.document_analysis_agent import DocumentAnalysisAgent
from fedops_agents.writer_agent import WriterAgent

router = APIRouter(prefix="/workflow", tags=["Workflow"])

@router.get("/{proposal_id}/status")
async def get_workflow_status(proposal_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Proposal).where(Proposal.id == proposal_id))
    proposal = result.scalar_one_or_none()
    
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
        
    return {
        "current_stage": proposal.current_stage,
        "stage_status": proposal.stage_status
    }

@router.post("/{proposal_id}/transition/{target_stage}")
async def transition_stage(
    proposal_id: int, 
    target_stage: ProposalStage, 
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Proposal).where(Proposal.id == proposal_id))
    proposal = result.scalar_one_or_none()
    
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")

    # Update state
    proposal.current_stage = target_stage
    proposal.stage_status = "IN_PROGRESS"
    await db.commit()
    
    # Trigger Stage-Specific Agents
    background_tasks.add_task(handle_stage_transition, proposal.id, target_stage, db)

    return {"status": "transition_initiated", "new_stage": target_stage}

async def handle_stage_transition(proposal_id: int, stage: ProposalStage, db: AsyncSession):
    """
    Orchestrates agent actions based on the new stage.
    Note: In a real app, this should probably be a separate service or queuing system.
    """
    # Need a new session for background task
    async with db.begin(): 
        # Re-fetch proposal in this session context if needed or just pass ID
        pass

    # Logic to instantiate agents and run them
    # For now, we'll just log it. 
    # To properly implement this, we need to handle the DB session correctly for background tasks.
    # We will assume 'db' passed here might be closed if it comes from Depends. 
    # PROPER WAY: Create a new session factory in the specialized service.
    
    print(f"Handling transition to {stage} for proposal {proposal_id}")
    
    if stage == ProposalStage.DECOMPOSITION:
        # Trigger DocumentAnalysisAgent.decompose_rfp
        # We need a proper way to get a db session here. 
        # For this prototype step, we will defer complex async background logic 
        # until we have a proper BackgroundService pattern.
        pass
    elif stage == ProposalStage.DRAFTING:
        # Trigger WriterAgent
        pass
