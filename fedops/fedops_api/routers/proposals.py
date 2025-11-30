from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
import uuid

from fedops_core.db.engine import get_db, AsyncSessionLocal
from fedops_core.db.models import Opportunity, OpportunityScore, Proposal, ProposalVolume
from pydantic import BaseModel

router = APIRouter(
    prefix="/proposals",
    tags=["proposals"]
)

class BlockUpdate(BaseModel):
    content: str

async def process_proposal_assets(opportunity_id: int, proposal_id: int):
    """
    Background task to import documents and extract requirements.
    """
    print(f"Starting background processing for proposal {proposal_id} (Opportunity {opportunity_id})")
    async with AsyncSessionLocal() as db:
        # Import documents from SAM.gov if not already imported
        try:
            from fedops_core.services.file_service import FileService
            from fedops_core.db.models import StoredFile
            
            file_service = FileService(db)
            
            # Check if documents already exist
            result = await db.execute(
                select(StoredFile).where(StoredFile.opportunity_id == opportunity_id)
            )
            existing_files = result.scalars().all()
            
            if not existing_files:
                # Import documents from SAM.gov
                print(f"No documents found for opportunity {opportunity_id}, importing from SAM.gov...")
                imported_files = await file_service.import_opportunity_resources(opportunity_id)
                print(f"Imported {len(imported_files)} documents for opportunity {opportunity_id}")
                
                # Process each imported file to extract content
                for file in imported_files:
                    try:
                        print(f"Processing file: {file.filename}")
                        await file_service.process_file(file.id)
                    except Exception as e:
                        print(f"Warning: Failed to process file {file.filename}: {e}")
            else:
                print(f"Using {len(existing_files)} existing documents for opportunity {opportunity_id}")
        except Exception as e:
            print(f"Warning: Document import failed: {e}")
            # Continue anyway - extraction will show helpful error if no docs
        
        # Trigger requirement extraction
        try:
            from fedops_core.services.requirement_extraction_service import RequirementExtractionService
            extraction_service = RequirementExtractionService(db)
            result = await extraction_service.extract_requirements_from_proposal(proposal_id)
            print(f"Requirements extraction completed: {result.get('requirements_count', 0)} requirements, {result.get('artifacts_count', 0)} artifacts")
        except Exception as e:
            print(f"Warning: Requirement extraction failed: {e}")

@router.post("/generate/{opportunity_id}")
async def generate_proposal(opportunity_id: int, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    """
    Generates a proposal draft based on the analysis from the agentic pipeline.
    """
    # 1. Check Decision - REMOVED to allow proposal generation for all opportunities
    # result = await db.execute(select(OpportunityScore).where(OpportunityScore.opportunity_id == opportunity_id))
    # score_entry = result.scalar_one_or_none()
    # if not score_entry or score_entry.go_no_go_decision != "GO":
    #     raise HTTPException(status_code=400, detail="Cannot generate proposal: Decision is not GO or analysis incomplete.")

    # 2. Gather Data
    result = await db.execute(select(Opportunity).where(Opportunity.id == opportunity_id))
    opp = result.scalar_one_or_none()
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    # 2a. Fetch Primary Entity for company information
    from fedops_core.db.models import Entity
    entity_result = await db.execute(select(Entity).where(Entity.is_primary == True))
    primary_entity = entity_result.scalar_one_or_none()
    
    # Extract entity data from SAM.gov response
    entity_data = {}
    if primary_entity and primary_entity.full_response:
        entity_reg = primary_entity.full_response.get("entityRegistration", {})
        core_data = primary_entity.full_response.get("coreData", {})
        
        entity_data = {
            "legal_name": entity_reg.get("legalBusinessName", ""),
            "dba_name": entity_reg.get("dbaName"),
            "uei": entity_reg.get("ueiSAM", ""),
            "cage_code": entity_reg.get("cageCode", ""),
            "physical_address": core_data.get("physicalAddress", {}),
            "website": core_data.get("entityInformation", {}).get("entityURL", ""),
            "business_types": core_data.get("businessTypes", {}).get("businessTypeList", []),
            "sba_certifications": core_data.get("businessTypes", {}).get("sbaBusinessTypeList", []),
            "logo_url": primary_entity.logo_url
        }
    
    # Build title page content
    address = entity_data.get("physical_address", {})
    address_line1 = address.get("addressLine1", "")
    address_line2 = address.get("addressLine2", "")
    city = address.get("city", "")
    state = address.get("stateOrProvinceCode", "")
    zip_code = address.get("zipCode", "")
    zip_plus4 = address.get("zipCodePlus4", "")
    
    # Format address
    street = address_line1
    if address_line2:
        street += f", {address_line2}"
    full_zip = zip_code
    if zip_plus4:
        full_zip += f"-{zip_plus4}"
    
    # Extract certifications
    certifications = []
    for cert in entity_data.get("sba_certifications", []):
        certifications.append(cert.get("sbaBusinessTypeDesc", ""))
    for biz_type in entity_data.get("business_types", []):
        desc = biz_type.get("businessTypeDesc", "")
        # Include relevant socioeconomic statuses
        if any(keyword in desc.lower() for keyword in ["small", "disadvantaged", "woman", "veteran", "hubzone", "8(a)"]):
            if desc not in certifications:
                certifications.append(desc)
    
    from datetime import datetime
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    title_page_content = f"""# Technical and Management Proposal

{f"![Company Logo]({entity_data.get('logo_url')})" if entity_data.get('logo_url') else ""}

**For:** {opp.title}

---

## Solicitation Information
- **Solicitation Number:** {opp.solicitation_number or 'N/A'}
- **Agency:** {opp.department or 'N/A'}
- **NAICS Code:** {opp.naics_code or 'N/A'}
- **Proposal Type:** Prime

---

## Offeror Information
**Legal Name:** {entity_data.get('legal_name', '[Company Name]')}  
**UEI:** {entity_data.get('uei', '[UEI]')}  
**CAGE Code:** {entity_data.get('cage_code', '[CAGE]')}  

**Business Address:**  
{street}  
{city}, {state} {full_zip}

**Website:** {entity_data.get('website', 'N/A')}

---

## Small Business & Certifications
{chr(10).join(f'- {cert}' for cert in certifications) if certifications else '- N/A'}

---

**Submission Date:** {current_date}  
**Submitted by:** {entity_data.get('legal_name', '[Company Name]')}
"""

    # 3. Define Volumes and Blocks (Standard Proposal Response Template)
    volumes_data = [
        {
            "title": "Part I: Introduction & Credentials",
            "order": 1,
            "blocks": [
                {
                    "id": str(uuid.uuid4()),
                    "title": "0.0 Cover Page",
                    "content": "![Cover Page](/static/covers/space_metrics_cover.png)",
                    "order": 0
                },
                {
                    "id": str(uuid.uuid4()), 
                    "title": "1.0 Title Page", 
                    "content": title_page_content,
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
    
    # 5. Trigger Background Processing (Documents & Requirements)
    background_tasks.add_task(process_proposal_assets, opportunity_id, proposal.id)
    
    # Return full proposal with volumes immediately
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

@router.post("/{proposal_id}/extract-requirements")
async def extract_requirements(proposal_id: int, db: AsyncSession = Depends(get_db)):
    """
    Trigger AI extraction of requirements from all associated documents.
    """
    from fedops_core.services.requirement_extraction_service import RequirementExtractionService
    
    service = RequirementExtractionService(db)
    result = await service.extract_requirements_from_proposal(proposal_id)
    
    if result["status"] == "failed":
        raise HTTPException(status_code=400, detail=result.get("error", "Extraction failed"))
    
    return result
