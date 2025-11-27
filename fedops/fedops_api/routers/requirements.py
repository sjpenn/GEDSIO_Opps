"""
Requirements API Router

Endpoints for managing proposal requirements, responses, and artifacts.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from typing import List, Optional
from pydantic import BaseModel

from fedops_core.db.engine import get_db
from fedops_core.db.models import (
    ProposalRequirement, 
    RequirementResponse, 
    DocumentArtifact,
    Proposal,
    StoredFile,
    Opportunity
)
from fedops_core.services.requirement_extraction_service import RequirementExtractionService

router = APIRouter(
    prefix="/requirements",
    tags=["requirements"]
)


# Pydantic models for request/response
class RequirementResponseUpdate(BaseModel):
    response_text: Optional[str] = None
    proposal_section_ref: Optional[str] = None
    assigned_to: Optional[str] = None
    status: Optional[str] = None


class RequirementStatusUpdate(BaseModel):
    compliance_status: str


class ArtifactStatusUpdate(BaseModel):
    status: str
    file_id: Optional[int] = None


@router.post("/proposals/{proposal_id}/extract")
async def extract_requirements(proposal_id: int, db: AsyncSession = Depends(get_db)):
    """
    Trigger requirement extraction from all documents associated with the proposal's opportunity.
    This is typically called automatically after proposal generation.
    """
    service = RequirementExtractionService(db)
    result = await service.extract_requirements_from_proposal(proposal_id)
    return result


@router.get("/proposals/{proposal_id}/requirements")
async def get_requirements(
    proposal_id: int,
    requirement_type: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    compliance_status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all requirements for a proposal with optional filters.
    """
    query = select(ProposalRequirement).where(ProposalRequirement.proposal_id == proposal_id)
    
    if requirement_type:
        query = query.where(ProposalRequirement.requirement_type == requirement_type)
    if priority:
        query = query.where(ProposalRequirement.priority == priority)
    if compliance_status:
        query = query.where(ProposalRequirement.compliance_status == compliance_status)
    
    result = await db.execute(query.order_by(ProposalRequirement.id))
    requirements = result.scalars().all()
    
    # Convert to dict for JSON serialization
    return [
        {
            "id": req.id,
            "proposal_id": req.proposal_id,
            "requirement_text": req.requirement_text,
            "requirement_type": req.requirement_type,
            "source_document_id": req.source_document_id,
            "source_section": req.source_section,
            "source_location": req.source_location,
            "priority": req.priority,
            "compliance_status": req.compliance_status,
            "created_at": req.created_at.isoformat() if req.created_at else None,
            "updated_at": req.updated_at.isoformat() if req.updated_at else None
        }
        for req in requirements
    ]


@router.get("/proposals/{proposal_id}/requirements/{requirement_id}")
async def get_requirement(proposal_id: int, requirement_id: int, db: AsyncSession = Depends(get_db)):
    """
    Get a specific requirement with its response.
    """
    # Get requirement
    result = await db.execute(
        select(ProposalRequirement).where(
            ProposalRequirement.id == requirement_id,
            ProposalRequirement.proposal_id == proposal_id
        )
    )
    requirement = result.scalar_one_or_none()
    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")
    
    # Get response if exists
    result = await db.execute(
        select(RequirementResponse).where(RequirementResponse.requirement_id == requirement_id)
    )
    response = result.scalar_one_or_none()
    
    return {
        "requirement": {
            "id": requirement.id,
            "proposal_id": requirement.proposal_id,
            "requirement_text": requirement.requirement_text,
            "requirement_type": requirement.requirement_type,
            "source_document_id": requirement.source_document_id,
            "source_section": requirement.source_section,
            "source_location": requirement.source_location,
            "priority": requirement.priority,
            "compliance_status": requirement.compliance_status,
        },
        "response": {
            "id": response.id if response else None,
            "response_text": response.response_text if response else None,
            "proposal_section_ref": response.proposal_section_ref if response else None,
            "assigned_to": response.assigned_to if response else None,
            "status": response.status if response else None,
        } if response else None
    }


@router.put("/proposals/{proposal_id}/requirements/{requirement_id}/response")
async def update_requirement_response(
    proposal_id: int,
    requirement_id: int,
    update_data: RequirementResponseUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update or create a response for a requirement.
    """
    # Verify requirement exists
    result = await db.execute(
        select(ProposalRequirement).where(
            ProposalRequirement.id == requirement_id,
            ProposalRequirement.proposal_id == proposal_id
        )
    )
    requirement = result.scalar_one_or_none()
    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")
    
    # Get or create response
    result = await db.execute(
        select(RequirementResponse).where(RequirementResponse.requirement_id == requirement_id)
    )
    response = result.scalar_one_or_none()
    
    if not response:
        response = RequirementResponse(requirement_id=requirement_id)
        db.add(response)
    
    # Update fields
    if update_data.response_text is not None:
        response.response_text = update_data.response_text
    if update_data.proposal_section_ref is not None:
        response.proposal_section_ref = update_data.proposal_section_ref
    if update_data.assigned_to is not None:
        response.assigned_to = update_data.assigned_to
    if update_data.status is not None:
        response.status = update_data.status
    
    await db.commit()
    await db.refresh(response)
    
    return {
        "id": response.id,
        "requirement_id": response.requirement_id,
        "response_text": response.response_text,
        "proposal_section_ref": response.proposal_section_ref,
        "assigned_to": response.assigned_to,
        "status": response.status
    }


@router.put("/proposals/{proposal_id}/requirements/{requirement_id}/status")
async def update_requirement_status(
    proposal_id: int,
    requirement_id: int,
    update_data: RequirementStatusUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update the compliance status of a requirement.
    """
    result = await db.execute(
        select(ProposalRequirement).where(
            ProposalRequirement.id == requirement_id,
            ProposalRequirement.proposal_id == proposal_id
        )
    )
    requirement = result.scalar_one_or_none()
    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")
    
    requirement.compliance_status = update_data.compliance_status
    await db.commit()
    
    return {"status": "success", "compliance_status": requirement.compliance_status}


@router.get("/proposals/{proposal_id}/artifacts")
async def get_artifacts(proposal_id: int, db: AsyncSession = Depends(get_db)):
    """
    Get all required artifacts for a proposal.
    """
    result = await db.execute(
        select(DocumentArtifact).where(DocumentArtifact.proposal_id == proposal_id)
    )
    artifacts = result.scalars().all()
    
    return [
        {
            "id": art.id,
            "proposal_id": art.proposal_id,
            "artifact_type": art.artifact_type,
            "title": art.title,
            "description": art.description,
            "source_section": art.source_section,
            "required": art.required,
            "status": art.status,
            "file_id": art.file_id,
            "created_at": art.created_at.isoformat() if art.created_at else None
        }
        for art in artifacts
    ]


@router.put("/proposals/{proposal_id}/artifacts/{artifact_id}")
async def update_artifact(
    proposal_id: int,
    artifact_id: int,
    update_data: ArtifactStatusUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update artifact status and optionally attach a file.
    """
    result = await db.execute(
        select(DocumentArtifact).where(
            DocumentArtifact.id == artifact_id,
            DocumentArtifact.proposal_id == proposal_id
        )
    )
    artifact = result.scalar_one_or_none()
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")
    
    artifact.status = update_data.status
    if update_data.file_id is not None:
        artifact.file_id = update_data.file_id
    
    await db.commit()
    
    return {
        "id": artifact.id,
        "status": artifact.status,
        "file_id": artifact.file_id
    }


@router.get("/proposals/{proposal_id}/workspace")
async def get_workspace_data(proposal_id: int, db: AsyncSession = Depends(get_db)):
    """
    Get all workspace data for a proposal including requirements, artifacts, documents, and opportunity details.
    This is the main endpoint for loading the proposal workspace UI.
    """
    # Get proposal
    result = await db.execute(
        select(Proposal).options(selectinload(Proposal.volumes)).where(Proposal.id == proposal_id)
    )
    proposal = result.scalar_one_or_none()
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    
    # Get opportunity details
    result = await db.execute(
        select(Opportunity).where(Opportunity.id == proposal.opportunity_id)
    )
    opportunity = result.scalar_one_or_none()
    
    # Get requirements
    result = await db.execute(
        select(ProposalRequirement).where(ProposalRequirement.proposal_id == proposal_id)
    )
    requirements = result.scalars().all()
    
    # Get artifacts
    result = await db.execute(
        select(DocumentArtifact).where(DocumentArtifact.proposal_id == proposal_id)
    )
    artifacts = result.scalars().all()
    
    # Get source documents
    result = await db.execute(
        select(StoredFile).where(StoredFile.opportunity_id == proposal.opportunity_id)
    )
    documents = result.scalars().all()
    
    return {
        "proposal": {
            "id": proposal.id,
            "opportunity_id": proposal.opportunity_id,
            "version": proposal.version,
            "volumes": [
                {
                    "id": vol.id,
                    "title": vol.title,
                    "order": vol.order,
                    "blocks": vol.blocks or []
                }
                for vol in (proposal.volumes or [])
            ]
        },
        "opportunity": {
            "id": opportunity.id if opportunity else None,
            "title": opportunity.title if opportunity else "Unknown",
            "notice_id": opportunity.notice_id if opportunity else None,
            "solicitation_number": opportunity.solicitation_number if opportunity else None,
            "department": opportunity.department if opportunity else None,
            "sub_tier": opportunity.sub_tier if opportunity else None,
            "office": opportunity.office if opportunity else None,
            "description": opportunity.description if opportunity else None,
            "posted_date": opportunity.posted_date.isoformat() if opportunity and opportunity.posted_date else None,
            "response_deadline": opportunity.response_deadline.isoformat() if opportunity and opportunity.response_deadline else None,
            "naics_code": opportunity.naics_code if opportunity else None,
            "type_of_set_aside": opportunity.type_of_set_aside if opportunity else None,
            "place_of_performance": opportunity.place_of_performance if opportunity else None,
            "point_of_contact": opportunity.point_of_contact if opportunity else None,
        } if opportunity else None,
        "requirements": [
            {
                "id": req.id,
                "requirement_text": req.requirement_text,
                "requirement_type": req.requirement_type,
                "source_document_id": req.source_document_id,
                "source_section": req.source_section,
                "source_location": req.source_location,
                "priority": req.priority,
                "compliance_status": req.compliance_status
            }
            for req in requirements
        ],
        "artifacts": [
            {
                "id": art.id,
                "artifact_type": art.artifact_type,
                "title": art.title,
                "description": art.description,
                "source_section": art.source_section,
                "required": art.required,
                "status": art.status,
                "file_id": art.file_id
            }
            for art in artifacts
        ],
        "documents": [
            {
                "id": doc.id,
                "filename": doc.filename,
                "file_type": doc.file_type,
                "file_size": doc.file_size,
                "parsed_content": doc.parsed_content
            }
            for doc in documents
        ]
    }
