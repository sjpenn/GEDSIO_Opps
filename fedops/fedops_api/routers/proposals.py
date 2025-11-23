from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import Dict, Any, List
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
async def generate_proposal(opportunity_id: int, db: Session = Depends(get_db)):
    """
    Generates a proposal draft based on the analysis from the agentic pipeline.
    Requires a 'GO' decision.
    """
    # 1. Check Decision
    score_entry = db.query(OpportunityScore).filter(OpportunityScore.opportunity_id == opportunity_id).first()
    if not score_entry or score_entry.go_no_go_decision != "GO":
        raise HTTPException(status_code=400, detail="Cannot generate proposal: Decision is not GO or analysis incomplete.")

    # 2. Gather Data
    opp = db.query(Opportunity).filter(Opportunity.id == opportunity_id).first()
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
                    "content": f"**Proposal for:** {opp.title}\n**Solicitation Number:** {opp.notice_id}\n**Submitted by:** [Company Name]\n**Date:** [Date]", 
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
    proposal = db.query(Proposal).filter(Proposal.opportunity_id == opportunity_id).first()
    if not proposal:
        proposal = Proposal(opportunity_id=opportunity_id)
        db.add(proposal)
        db.commit() # Commit to get ID
    else:
        # Clear existing volumes for regeneration
        db.query(ProposalVolume).filter(ProposalVolume.proposal_id == proposal.id).delete()
        proposal.version += 1
    
    for vol_data in volumes_data:
        vol = ProposalVolume(
            proposal_id=proposal.id,
            title=vol_data["title"],
            order=vol_data["order"],
            blocks=vol_data["blocks"]
        )
        db.add(vol)
    
    db.commit()
    
    # Return full proposal with volumes
    return get_proposal(opportunity_id, db)

@router.get("/{opportunity_id}")
def get_proposal(opportunity_id: int, db: Session = Depends(get_db)):
    proposal = db.query(Proposal).options(joinedload(Proposal.volumes)).filter(Proposal.opportunity_id == opportunity_id).first()
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    return proposal

@router.put("/{proposal_id}/volumes/{volume_id}/blocks/{block_id}")
async def update_proposal_block(proposal_id: int, volume_id: int, block_id: str, update: BlockUpdate, db: Session = Depends(get_db)):
    volume = db.query(ProposalVolume).filter(ProposalVolume.id == volume_id, ProposalVolume.proposal_id == proposal_id).first()
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
    db.commit()
    
    return {"status": "success", "blocks": volume.blocks}
