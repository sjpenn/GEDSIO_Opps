"""
Proposals Router - Appwrite Version

API endpoints for proposal management using Appwrite database.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Optional, List, Dict, Any
import uuid
import logging

from fedops_core.services.proposals_repository import ProposalsRepository, ProposalVolumesRepository
from fedops_core.services.opportunities_repository import OpportunitiesRepository
from fedops_core.services.files_repository import FilesRepository
from fedops_core.services.additional_repositories import (
    DocumentSectionsRepository,
    DocumentChunksRepository
)
from appwrite.query import Query as AppwriteQuery
from pydantic import BaseModel

router = APIRouter()
logger = logging.getLogger(__name__)


class BlockUpdate(BaseModel):
    content: str


class VolumeCreate(BaseModel):
    title: str
    order: int = 0


class BlockCreate(BaseModel):
    title: str
    content: str


@router.get("/generate/{opportunity_id}")
async def generate_proposal(
    opportunity_id: str,
    background_tasks: BackgroundTasks
):
    """
    Generates a proposal draft for an opportunity.
    Creates the proposal structure with standard volumes.
    """
    opp_repo = OpportunitiesRepository()
    proposals_repo = ProposalsRepository()
    volumes_repo = ProposalVolumesRepository()
    
    # Verify opportunity exists
    opportunity = await opp_repo.get(opportunity_id)
    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    
    try:
        # Get or create proposal
        proposal = await proposals_repo.get_or_create(opportunity_id)
        proposal_id = proposal["id"]
        
        # Check if volumes already exist
        existing_volumes = await volumes_repo.get_by_proposal(proposal_id)
        if existing_volumes.get("documents"):
            return {
                "proposal_id": proposal_id,
                "opportunity_id": opportunity_id,
                "volumes": existing_volumes["documents"],
                "message": "Proposal already exists"
            }
        
        # Create standard volumes
        standard_volumes = [
            {"title": "Volume I: Technical Approach", "order": 1},
            {"title": "Volume II: Management Approach", "order": 2},
            {"title": "Volume III: Past Performance", "order": 3},
            {"title": "Volume IV: Cost/Price", "order": 4}
        ]
        
        created_volumes = []
        for vol in standard_volumes:
            new_volume = await volumes_repo.create_volume(
                proposal_id=proposal_id,
                title=vol["title"],
                order=vol["order"],
                blocks=[]
            )
            created_volumes.append(new_volume)
        
        # Update proposal stage
        await proposals_repo.update_stage(proposal_id, "DECOMPOSITION")
        
        return {
            "proposal_id": proposal_id,
            "opportunity_id": opportunity_id,
            "volumes": created_volumes,
            "message": "Proposal created successfully"
        }
        
    except Exception as e:
        logger.error(f"Error generating proposal: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{opportunity_id}")
async def get_proposal(opportunity_id: str):
    """Get proposal for an opportunity."""
    proposals_repo = ProposalsRepository()
    volumes_repo = ProposalVolumesRepository()
    
    proposal = await proposals_repo.get_by_opportunity(opportunity_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    
    # Get volumes
    volumes = await volumes_repo.get_by_proposal(proposal["id"])
    
    return {
        **proposal,
        "volumes": volumes.get("documents", [])
    }


@router.get("/by-id/{proposal_id}")
async def get_proposal_by_id(proposal_id: str):
    """Get proposal by ID."""
    proposals_repo = ProposalsRepository()
    volumes_repo = ProposalVolumesRepository()
    
    proposal = await proposals_repo.get(proposal_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    
    volumes = await volumes_repo.get_by_proposal(proposal_id)
    
    return {
        **proposal,
        "volumes": volumes.get("documents", [])
    }


@router.post("/{proposal_id}/volumes")
async def create_volume(proposal_id: str, volume: VolumeCreate):
    """Create a new volume for a proposal."""
    proposals_repo = ProposalsRepository()
    volumes_repo = ProposalVolumesRepository()
    
    proposal = await proposals_repo.get(proposal_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    
    try:
        new_volume = await volumes_repo.create_volume(
            proposal_id=proposal_id,
            title=volume.title,
            order=volume.order
        )
        return new_volume
    except Exception as e:
        logger.error(f"Error creating volume: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{proposal_id}/volumes")
async def get_volumes(proposal_id: str):
    """Get all volumes for a proposal."""
    volumes_repo = ProposalVolumesRepository()
    result = await volumes_repo.get_by_proposal(proposal_id)
    return result.get("documents", [])


@router.put("/{proposal_id}/volumes/{volume_id}/blocks/{block_id}")
async def update_proposal_block(
    proposal_id: str, 
    volume_id: str, 
    block_id: str, 
    update: BlockUpdate
):
    """Update a content block within a volume."""
    volumes_repo = ProposalVolumesRepository()
    
    volume = await volumes_repo.get(volume_id)
    if not volume:
        raise HTTPException(status_code=404, detail="Volume not found")
    
    blocks = volume.get("blocks", [])
    
    # Find and update the block
    block_found = False
    for block in blocks:
        if block.get("id") == block_id:
            block["content"] = update.content
            block_found = True
            break
    
    if not block_found:
        raise HTTPException(status_code=404, detail="Block not found")
    
    try:
        await volumes_repo.update_blocks(volume_id, blocks)
        return {"ok": True, "message": "Block updated"}
    except Exception as e:
        logger.error(f"Error updating block: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{proposal_id}/volumes/{volume_id}/blocks")
async def add_block(proposal_id: str, volume_id: str, block: BlockCreate):
    """Add a new content block to a volume."""
    volumes_repo = ProposalVolumesRepository()
    
    volume = await volumes_repo.get(volume_id)
    if not volume:
        raise HTTPException(status_code=404, detail="Volume not found")
    
    blocks = volume.get("blocks", [])
    
    new_block = {
        "id": str(uuid.uuid4()),
        "title": block.title,
        "content": block.content,
        "order": len(blocks) + 1
    }
    
    blocks.append(new_block)
    
    try:
        await volumes_repo.update_blocks(volume_id, blocks)
        return new_block
    except Exception as e:
        logger.error(f"Error adding block: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{proposal_id}/volumes/{volume_id}/blocks/{block_id}")
async def delete_block(proposal_id: str, volume_id: str, block_id: str):
    """Delete a content block from a volume."""
    volumes_repo = ProposalVolumesRepository()
    
    volume = await volumes_repo.get(volume_id)
    if not volume:
        raise HTTPException(status_code=404, detail="Volume not found")
    
    blocks = volume.get("blocks", [])
    new_blocks = [b for b in blocks if b.get("id") != block_id]
    
    if len(new_blocks) == len(blocks):
        raise HTTPException(status_code=404, detail="Block not found")
    
    try:
        await volumes_repo.update_blocks(volume_id, new_blocks)
        return {"ok": True, "message": "Block deleted"}
    except Exception as e:
        logger.error(f"Error deleting block: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{proposal_id}/stage")
async def update_stage(proposal_id: str, stage: str, status: str = "IN_PROGRESS"):
    """Update the proposal stage."""
    proposals_repo = ProposalsRepository()
    
    try:
        proposal = await proposals_repo.update_stage(proposal_id, stage, status)
        return proposal
    except Exception as e:
        logger.error(f"Error updating stage: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{proposal_id}")
async def delete_proposal(proposal_id: str):
    """Delete a proposal and all its volumes."""
    proposals_repo = ProposalsRepository()
    volumes_repo = ProposalVolumesRepository()
    
    proposal = await proposals_repo.get(proposal_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    
    try:
        # Delete volumes first
        volumes = await volumes_repo.get_by_proposal(proposal_id)
        for volume in volumes.get("documents", []):
            await volumes_repo.delete(volume["id"])
        
        # Delete proposal
        await proposals_repo.delete(proposal_id)
        
        return {"ok": True, "message": "Proposal deleted"}
    except Exception as e:
        logger.error(f"Error deleting proposal: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def list_proposals(
    skip: int = 0,
    limit: int = 25,
    stage: Optional[str] = None
):
    """List all proposals with optional filtering."""
    proposals_repo = ProposalsRepository()
    
    queries = []
    if stage:
        queries.append(AppwriteQuery.equal("current_stage", stage))
    
    queries.append(AppwriteQuery.order_desc("created_at"))
    
    try:
        result = await proposals_repo.list(queries=queries, limit=limit, offset=skip)
        return {
            "items": result.get("documents", []),
            "total": result.get("total", 0)
        }
    except Exception as e:
        logger.error(f"Error listing proposals: {e}")
        raise HTTPException(status_code=500, detail=str(e))
