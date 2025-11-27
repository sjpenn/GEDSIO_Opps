from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
import uuid

from fedops_core.db.engine import get_db
from fedops_core.db.models import Opportunity, OpportunityScore, Proposal, ProposalVolume
from pydantic import BaseModel

router = APIRouter(
    prefix="/proposals",
    tags=["proposals"]
)

class BlockUpdate(BaseModel):
    content: str

@router.post("/generate/{opportunity_id}")
async def generate_proposal(opportunity_id: int, db: AsyncSession = Depends(get_db)):
    """
    Generates a proposal draft based on the analysis from the agentic pipeline.
    Requires a 'GO' decision.
    """
    # 1. Check Decision
    result = await db.execute(select(OpportunityScore).where(OpportunityScore.opportunity_id == opportunity_id))
    score_entry = result.scalar_one_or_none()
    if not score_entry or score_entry.go_no_go_decision != "GO":
        raise HTTPException(status_code=400, detail="Cannot generate proposal: Decision is not GO or analysis incomplete.")

    # 2. Gather Data
    result = await db.execute(select(Opportunity).where(Opportunity.id == opportunity_id))
    opp = result.scalar_one_or_none()
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    # 3. Define Volumes and Blocks (Standard Proposal Response Template)
    volumes_data = [
        {
            "title": "Part I: Introduction & Credentials",
            "order": 1,
            "blocks": [
                {
                    "id": str(uuid.uuid4()), 
                    "title": "1.0 Title Page", 
                    "content": f"**Proposal for:** {opp.title}\n**Solicitation Number:** {opp.solicitation_number}\n**Submitted by:** [Company Name]\n**Date:** [Date]", 
                    "order": 1
                },
                {
                    "id": str(uuid.uuid4()), 
                    "title": "2.0 Cover Letter", 
                    "content": f"**Subject:** Proposal Submission for {opp.title}\n\nDear Contracting Officer,\n\nWe are pleased to submit this proposal... [Highlights main differentiator]", 
                    "order": 2
                },
                {
                    "id": str(uuid.uuid4()), 
                    "title": "3.0 Executive Summary", 
                    "content": "**Overview**\n\nOur solution provides the best value to the Government by...\n\n**Key Benefits:**\n- ...", 
                    "order": 3
                },
            ]
        },
        {
            "title": "Part II: Technical Volume",
            "order": 2,
            "blocks": [
                {
                    "id": str(uuid.uuid4()), 
                    "title": "1.0 Understanding the Requirement", 
                    "content": f"**Problem Statement**\n\nWe understand that the {opp.department} faces challenges in... [Analysis from DocumentAgent]\n\n**Key Risks:**\n- ...", 
                    "order": 1
                },
                {
                    "id": str(uuid.uuid4()), 
                    "title": "2.0 Technical Approach", 
                    "content": "**Methodology**\n\nOur step-by-step approach to executing the SOW/PWS...\n\n**Work Breakdown Structure (WBS):**\n1. Phase 1...\n2. Phase 2...", 
                    "order": 2
                },
                {
                    "id": str(uuid.uuid4()), 
                    "title": "3.0 Compliance Matrix", 
                    "content": "| Solicitation Section | Requirement | Proposal Section | Compliant? |\n|---|---|---|---|\n| C.1 | Scope | 1.0 | Yes |", 
                    "order": 3
                },
            ]
        },
        {
            "title": "Part III: Management Volume",
            "order": 3,
            "blocks": [
                {
                    "id": str(uuid.uuid4()), 
                    "title": "1.0 Key Personnel & Staffing", 
                    "content": "**Organizational Chart**\n\n[Insert Chart]\n\n**Key Personnel:**\n- Program Manager: [Name]\n- Technical Lead: [Name]", 
                    "order": 1
                },
                {
                    "id": str(uuid.uuid4()), 
                    "title": "2.0 Past Performance", 
                    "content": "**Case Study 1**\n\n- **Client:** ...\n- **Challenge:** ...\n- **Solution:** ...\n- **Results:** ...", 
                    "order": 2
                },
            ]
        },
        {
            "title": "Part IV: Pricing Volume",
            "order": 4,
            "blocks": [
                {
                    "id": str(uuid.uuid4()), 
                    "title": "1.0 Pricing Narrative", 
                    "content": "**Basis of Estimate**\n\nOur pricing is derived from...\n\n**Assumptions:**\n- ...", 
                    "order": 1
                },
                {
                    "id": str(uuid.uuid4()), 
                    "title": "2.0 Pricing Summary", 
                    "content": "| CLIN | Description | Unit Price | Total |\n|---|---|---|---|\n| 001 | Labor | $... | $... |", 
                    "order": 2
                },
            ]
        }
    ]
    
    # 4. Save to Database
    result = await db.execute(select(Proposal).where(Proposal.opportunity_id == opportunity_id))
    proposal = result.scalar_one_or_none()
    
    if not proposal:
        proposal = Proposal(opportunity_id=opportunity_id)
        db.add(proposal)
        await db.commit() # Commit to get ID
        await db.refresh(proposal)
    else:
        # Clear existing volumes for regeneration
        await db.execute(delete(ProposalVolume).where(ProposalVolume.proposal_id == proposal.id))
        proposal.version += 1
    
    for vol_data in volumes_data:
        vol = ProposalVolume(
            proposal_id=proposal.id,
            title=vol_data["title"],
            order=vol_data["order"],
            blocks=vol_data["blocks"]
        )
        db.add(vol)
    
    await db.commit()
    
    # Trigger requirement extraction in background
    try:
        from fedops_core.services.requirement_extraction_service import RequirementExtractionService
        extraction_service = RequirementExtractionService(db)
        await extraction_service.extract_requirements_from_proposal(proposal.id)
    except Exception as e:
        print(f"Warning: Requirement extraction failed: {e}")
        # Don't fail the whole request if extraction fails
    
    # Return full proposal with volumes
    return await get_proposal(opportunity_id, db)

@router.get("/{opportunity_id}")
async def get_proposal(opportunity_id: int, db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(
            select(Proposal)
            .options(selectinload(Proposal.volumes))
            .where(Proposal.opportunity_id == opportunity_id)
        )
        proposal = result.scalar_one_or_none()
        if not proposal:
            raise HTTPException(status_code=404, detail="Proposal not found")
        
        # Convert to dict for safe serialization
        proposal_dict = {
            "id": proposal.id,
            "opportunity_id": proposal.opportunity_id,
            "version": proposal.version,
            "created_at": proposal.created_at.isoformat() if proposal.created_at else None,
            "updated_at": proposal.updated_at.isoformat() if proposal.updated_at else None,
            "volumes": [
                {
                    "id": vol.id,
                    "title": vol.title,
                    "order": vol.order,
                    "blocks": vol.blocks or []
                }
                for vol in (proposal.volumes or [])
            ]
        }
        return proposal_dict
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error fetching proposal: {str(e)}")

@router.put("/{proposal_id}/volumes/{volume_id}/blocks/{block_id}")
async def update_proposal_block(proposal_id: int, volume_id: int, block_id: str, update: BlockUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ProposalVolume)
        .where(ProposalVolume.id == volume_id, ProposalVolume.proposal_id == proposal_id)
    )
    volume = result.scalar_one_or_none()
    if not volume:
        raise HTTPException(status_code=404, detail="Volume not found")
    
    updated = False
    new_blocks = []
    # volume.blocks is a list of dicts
    current_blocks = volume.blocks if volume.blocks else []
    
    for block in current_blocks:
        if block["id"] == block_id:
            block["content"] = update.content
            updated = True
        new_blocks.append(block)
    
    if not updated:
        raise HTTPException(status_code=404, detail="Block not found")
        
    # Force update for JSONB
    volume.blocks = list(new_blocks)
    await db.commit()
    
    return {"status": "success", "blocks": volume.blocks}


# ============================================================================
# AI-Powered Content Generation Endpoints
# ============================================================================

@router.post("/{proposal_id}/generate-requirements-matrix")
async def generate_requirements_matrix(proposal_id: int, db: AsyncSession = Depends(get_db)):
    """
    Generate a comprehensive requirements compliance matrix using AI.
    """
    from fedops_core.services.proposal_content_generator import ProposalContentGenerator
    
    generator = ProposalContentGenerator(db)
    result = await generator.generate_requirements_matrix(proposal_id)
    
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result.get("message", "Generation failed"))
    
    return result


@router.post("/{proposal_id}/generate-sow-decomposition")
async def generate_sow_decomposition(proposal_id: int, db: AsyncSession = Depends(get_db)):
    """
    Generate structured SOW/PWS decomposition and analysis using AI.
    """
    from fedops_core.services.proposal_content_generator import ProposalContentGenerator
    
    generator = ProposalContentGenerator(db)
    result = await generator.generate_sow_decomposition(proposal_id)
    
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result.get("message", "Generation failed"))
    
    return result


@router.post("/{proposal_id}/generate-past-performance")
async def generate_past_performance(proposal_id: int, db: AsyncSession = Depends(get_db)):
    """
    Generate past performance volume with relevant case studies using AI.
    """
    from fedops_core.services.proposal_content_generator import ProposalContentGenerator
    
    generator = ProposalContentGenerator(db)
    result = await generator.generate_past_performance_volume(proposal_id)
    
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result.get("message", "Generation failed"))
    
    return result


@router.post("/{proposal_id}/generate-ppqs")
async def generate_ppqs(proposal_id: int, db: AsyncSession = Depends(get_db)):
    """
    Generate Past Performance Questionnaire (PPQ) responses using AI.
    """
    from fedops_core.services.proposal_content_generator import ProposalContentGenerator
    
    generator = ProposalContentGenerator(db)
    result = await generator.generate_ppqs(proposal_id)
    
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result.get("message", "Generation failed"))
    
    return result


@router.post("/{proposal_id}/generate-all-content")
async def generate_all_content(proposal_id: int, db: AsyncSession = Depends(get_db)):
    """
    Generate all AI-powered content at once: requirements matrix, SOW decomposition,
    past performance volume, and PPQs.
    """
    from fedops_core.services.proposal_content_generator import ProposalContentGenerator
    
    generator = ProposalContentGenerator(db)
    
    results = {
        "requirements_matrix": await generator.generate_requirements_matrix(proposal_id),
        "sow_decomposition": await generator.generate_sow_decomposition(proposal_id),
        "past_performance": await generator.generate_past_performance_volume(proposal_id),
        "ppqs": await generator.generate_ppqs(proposal_id)
    }
    
    # Check if any failed
    failed = [key for key, result in results.items() if result.get("status") == "error"]
    
    return {
        "status": "partial" if failed else "success",
        "failed_items": failed,
        "results": results
    }
