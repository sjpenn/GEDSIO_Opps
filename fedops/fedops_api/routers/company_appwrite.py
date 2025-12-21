"""
Company Router - Appwrite Version

API endpoints for company profile management using Appwrite database.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks
from typing import Optional, List
from pydantic import BaseModel
import logging
import os

from fedops_core.services.additional_repositories import (
    CompanyProfilesRepository,
    CompanyProfileDocumentsRepository,
    PastPerformancesRepository
)
from fedops_core.services.entities_repository import EntitiesRepository
from fedops_core.services.files_repository import FilesRepository
from appwrite.query import Query as AppwriteQuery

router = APIRouter()
logger = logging.getLogger(__name__)


# Pydantic models
class CompanyProfileCreate(BaseModel):
    uei: str
    company_name: str
    entity_uei: Optional[str] = None
    target_naics: Optional[List[str]] = []
    target_keywords: Optional[List[str]] = []
    target_set_asides: Optional[List[str]] = []


class CompanyProfileUpdate(BaseModel):
    company_name: Optional[str] = None
    target_naics: Optional[List[str]] = None
    target_keywords: Optional[List[str]] = None
    target_set_asides: Optional[List[str]] = None


@router.post("/")
async def create_company_profile(profile: CompanyProfileCreate):
    """Create a new company profile."""
    repo = CompanyProfilesRepository()
    
    # Check if UEI already exists
    existing = await repo.get_by_uei(profile.uei)
    if existing:
        raise HTTPException(status_code=409, detail="Company profile with this UEI already exists")
    
    try:
        new_profile = await repo.create(profile.dict())
        return new_profile
    except Exception as e:
        logger.error(f"Error creating company profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def get_company_profiles(skip: int = 0, limit: int = 10):
    """List all company profiles."""
    repo = CompanyProfilesRepository()
    
    try:
        result = await repo.list(
            queries=[AppwriteQuery.order_desc("created_at")],
            limit=limit,
            offset=skip
        )
        return {
            "items": result.get("documents", []),
            "total": result.get("total", 0)
        }
    except Exception as e:
        logger.error(f"Error listing company profiles: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/uei/{uei}")
async def get_company_profile(uei: str):
    """Get a company profile by UEI."""
    repo = CompanyProfilesRepository()
    entities_repo = EntitiesRepository()
    
    profile = await repo.get_by_uei(uei)
    if not profile:
        raise HTTPException(status_code=404, detail="Company profile not found")
    
    # Enrich with entity data if linked
    entity_data = None
    if profile.get("entity_uei"):
        entity_data = await entities_repo.get_by_uei(profile["entity_uei"])
    
    return {
        **profile,
        "entity": entity_data
    }


@router.put("/uei/{uei}")
async def update_company_profile(uei: str, profile_update: CompanyProfileUpdate):
    """Update a company profile."""
    repo = CompanyProfilesRepository()
    
    profile = await repo.get_by_uei(uei)
    if not profile:
        raise HTTPException(status_code=404, detail="Company profile not found")
    
    try:
        update_data = {k: v for k, v in profile_update.dict().items() if v is not None}
        updated = await repo.update(profile["id"], update_data)
        return updated
    except Exception as e:
        logger.error(f"Error updating company profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/uei/{uei}")
async def delete_company_profile(uei: str):
    """Delete a company profile."""
    repo = CompanyProfilesRepository()
    
    profile = await repo.get_by_uei(uei)
    if not profile:
        raise HTTPException(status_code=404, detail="Company profile not found")
    
    try:
        await repo.delete(profile["id"])
        return {"ok": True, "message": "Company profile deleted"}
    except Exception as e:
        logger.error(f"Error deleting company profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ Entity Selection Endpoints ============

@router.post("/set-entity/{entity_uei}")
async def set_entity_as_profile(entity_uei: str, background_tasks: BackgroundTasks):
    """
    Set an entity from SAM.gov as the active company profile.
    Creates a company profile if one doesn't exist for this entity.
    """
    entities_repo = EntitiesRepository()
    profiles_repo = CompanyProfilesRepository()
    
    # Verify entity exists
    entity = await entities_repo.get_by_uei(entity_uei)
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    
    # Set as primary entity
    await entities_repo.set_primary_entity(entity_uei)
    
    # Check if company profile exists
    profile = await profiles_repo.get_by_uei(entity_uei)
    
    if not profile:
        # Create new profile from entity
        profile = await profiles_repo.create({
            "uei": entity_uei,
            "company_name": entity.get("legal_business_name", ""),
            "entity_uei": entity_uei
        })
    
    return {
        "message": "Entity set as active company profile",
        "profile": profile
    }


# ============ Document Management Endpoints ============

@router.post("/uei/{company_uei}/documents")
async def upload_company_document(
    company_uei: str,
    file: UploadFile = File(...),
    document_type: str = Form(...),
    title: str = Form(...),
    description: Optional[str] = Form(None)
):
    """Upload a document for the company profile."""
    profiles_repo = CompanyProfilesRepository()
    docs_repo = CompanyProfileDocumentsRepository()
    files_repo = FilesRepository()
    
    profile = await profiles_repo.get_by_uei(company_uei)
    if not profile:
        raise HTTPException(status_code=404, detail="Company profile not found")
    
    try:
        # Read file content
        content = await file.read()
        
        # Upload to storage
        stored_file = await files_repo.upload_from_bytes(
            content=content,
            filename=file.filename
        )
        
        # Create document record
        doc = await docs_repo.create({
            "company_uei": company_uei,
            "document_type": document_type,
            "title": title,
            "description": description,
            "file_path": "",
            "storage_file_id": stored_file.get("storage_file_id"),
            "file_size": len(content),
            "status": "COMPLETED"
        })
        
        return doc
        
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/uei/{company_uei}/documents")
async def get_company_documents(
    company_uei: str,
    document_type: Optional[str] = None
):
    """Get all documents for a company profile."""
    docs_repo = CompanyProfileDocumentsRepository()
    
    result = await docs_repo.get_by_company(company_uei, document_type)
    return result.get("documents", [])


@router.delete("/uei/{company_uei}/documents/{doc_id}")
async def delete_company_document(company_uei: str, doc_id: str):
    """Delete a document from the company profile."""
    docs_repo = CompanyProfileDocumentsRepository()
    
    doc = await docs_repo.get(doc_id)
    if not doc or doc.get("company_uei") != company_uei:
        raise HTTPException(status_code=404, detail="Document not found")
    
    try:
        await docs_repo.delete(doc_id)
        return {"ok": True, "message": "Document deleted"}
    except Exception as e:
        logger.error(f"Error deleting document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ Past Performance Endpoints ============

@router.get("/uei/{company_uei}/past-performances")
async def get_company_past_performances(company_uei: str):
    """Get all past performances for a company."""
    pp_repo = PastPerformancesRepository()
    result = await pp_repo.get_by_entity(company_uei)
    return result.get("documents", [])
