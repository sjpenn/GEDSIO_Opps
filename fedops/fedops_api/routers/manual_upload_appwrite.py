"""
Manual Upload Router - Appwrite Version

API endpoints for manually uploading opportunities using Appwrite database.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks
from typing import Optional, List
from pydantic import BaseModel
import logging
import uuid
from datetime import datetime

from fedops_core.services.opportunities_repository import OpportunitiesRepository
from fedops_core.services.files_repository import FilesRepository
from fedops_core.services.additional_repositories import OpportunityPipelinesRepository

router = APIRouter()
logger = logging.getLogger(__name__)


class ManualOpportunityCreate(BaseModel):
    title: str
    department: Optional[str] = None
    office: Optional[str] = None
    type: str = "RFP"
    response_deadline: Optional[str] = None
    naics_code: Optional[str] = None
    description: Optional[str] = None
    incumbent_vendor: Optional[str] = None
    incumbent_contract_number: Optional[str] = None
    incumbent_value: Optional[str] = None
    incumbent_expiration_date: Optional[str] = None


@router.post("/opportunity")
async def create_manual_opportunity(data: ManualOpportunityCreate):
    """Create a manually entered opportunity."""
    repo = OpportunitiesRepository()
    pipelines_repo = OpportunityPipelinesRepository()
    
    try:
        # Generate a unique notice ID for manual uploads
        notice_id = f"MANUAL-{uuid.uuid4().hex[:8].upper()}"
        
        opp_data = {
            "notice_id": notice_id,
            "title": data.title,
            "department": data.department,
            "office": data.office,
            "type": data.type,
            "posted_date": datetime.utcnow().isoformat(),
            "response_deadline": data.response_deadline,
            "naics_code": data.naics_code,
            "description": data.description,
            "source": "Manual",
            "active": "Yes",
            "incumbent_vendor": data.incumbent_vendor,
            "incumbent_contract_number": data.incumbent_contract_number,
            "incumbent_value": data.incumbent_value,
            "incumbent_expiration_date": data.incumbent_expiration_date
        }
        
        opportunity = await repo.create(opp_data)
        
        # Create pipeline entry
        await pipelines_repo.create({
            "opportunity_id": opportunity["id"],
            "status": "WATCHING",
            "stage": "QUALIFICATION"
        })
        
        return opportunity
        
    except Exception as e:
        logger.error(f"Error creating manual opportunity: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/opportunity/with-documents")
async def create_opportunity_with_documents(
    title: str = Form(...),
    department: Optional[str] = Form(None),
    office: Optional[str] = Form(None),
    type: str = Form("RFP"),
    response_deadline: Optional[str] = Form(None),
    naics_code: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    incumbent_vendor: Optional[str] = Form(None),
    files: List[UploadFile] = File(...)
):
    """Create a manual opportunity with attached documents."""
    opp_repo = OpportunitiesRepository()
    files_repo = FilesRepository()
    pipelines_repo = OpportunityPipelinesRepository()
    
    try:
        # Create the opportunity
        notice_id = f"MANUAL-{uuid.uuid4().hex[:8].upper()}"
        
        opportunity = await opp_repo.create({
            "notice_id": notice_id,
            "title": title,
            "department": department,
            "office": office,
            "type": type,
            "posted_date": datetime.utcnow().isoformat(),
            "response_deadline": response_deadline,
            "naics_code": naics_code,
            "description": description,
            "source": "Manual",
            "active": "Yes",
            "incumbent_vendor": incumbent_vendor
        })
        
        opportunity_id = opportunity["id"]
        
        # Upload files
        uploaded_files = []
        for file in files:
            content = await file.read()
            stored = await files_repo.upload_from_bytes(
                content=content,
                filename=file.filename,
                opportunity_id=opportunity_id
            )
            uploaded_files.append(stored)
        
        # Create pipeline entry
        await pipelines_repo.create({
            "opportunity_id": opportunity_id,
            "status": "WATCHING",
            "stage": "QUALIFICATION"
        })
        
        return {
            "opportunity": opportunity,
            "files": uploaded_files,
            "message": f"Created opportunity with {len(uploaded_files)} documents"
        }
        
    except Exception as e:
        logger.error(f"Error creating opportunity with documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/opportunity/{opportunity_id}/documents")
async def upload_opportunity_documents(
    opportunity_id: str,
    files: List[UploadFile] = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """Upload documents to an existing opportunity."""
    opp_repo = OpportunitiesRepository()
    files_repo = FilesRepository()
    
    opportunity = await opp_repo.get(opportunity_id)
    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    
    try:
        uploaded_files = []
        for file in files:
            content = await file.read()
            stored = await files_repo.upload_from_bytes(
                content=content,
                filename=file.filename,
                opportunity_id=opportunity_id
            )
            uploaded_files.append(stored)
        
        return {
            "files": uploaded_files,
            "message": f"Uploaded {len(uploaded_files)} documents"
        }
        
    except Exception as e:
        logger.error(f"Error uploading documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/opportunity/{opportunity_id}")
async def update_manual_opportunity(opportunity_id: str, data: ManualOpportunityCreate):
    """Update a manually created opportunity."""
    repo = OpportunitiesRepository()
    
    opportunity = await repo.get(opportunity_id)
    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    
    # Only allow updates to manual opportunities
    if opportunity.get("source") != "Manual":
        raise HTTPException(status_code=400, detail="Can only update manually created opportunities")
    
    try:
        update_data = {k: v for k, v in data.dict().items() if v is not None}
        updated = await repo.update(opportunity_id, update_data)
        return updated
    except Exception as e:
        logger.error(f"Error updating opportunity: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/opportunities")
async def list_manual_opportunities(skip: int = 0, limit: int = 25):
    """List all manually created opportunities."""
    repo = OpportunitiesRepository()
    
    result = await repo.get_by_source("Manual", limit=limit, offset=skip)
    return {
        "items": result.get("documents", []),
        "total": result.get("total", 0)
    }
