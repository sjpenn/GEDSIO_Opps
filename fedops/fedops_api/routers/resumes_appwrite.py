"""
Resumes Router - Appwrite Version

API endpoints for resume management using Appwrite database.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, BackgroundTasks
from typing import Optional
from pydantic import BaseModel
import logging

from fedops_core.services.additional_repositories import ResumesRepository
from fedops_core.services.files_repository import FilesRepository
from appwrite.query import Query as AppwriteQuery

router = APIRouter()
logger = logging.getLogger(__name__)


class ResumeUpdate(BaseModel):
    status: Optional[str] = None
    parsed_data: Optional[dict] = None
    formatted_content_html: Optional[str] = None


@router.post("/upload")
async def upload_resume(
    file: UploadFile = File(...),
    user_id: Optional[str] = None,
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """Upload a resume file."""
    files_repo = FilesRepository()
    resumes_repo = ResumesRepository()
    
    try:
        # Upload file
        content = await file.read()
        stored_file = await files_repo.upload_from_bytes(
            content=content,
            filename=file.filename
        )
        
        # Create resume record
        resume = await resumes_repo.create({
            "user_id": user_id,
            "stored_file_id": stored_file["id"],
            "status": "UPLOADED"
        })
        
        return {
            "resume": resume,
            "file": stored_file
        }
        
    except Exception as e:
        logger.error(f"Error uploading resume: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{resume_id}")
async def get_resume(resume_id: str):
    """Get a resume by ID."""
    repo = ResumesRepository()
    
    resume = await repo.get(resume_id)
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    return resume


@router.get("/")
async def list_resumes(
    skip: int = 0,
    limit: int = 25,
    user_id: Optional[str] = None
):
    """List resumes with optional filtering."""
    repo = ResumesRepository()
    
    queries = []
    if user_id:
        queries.append(AppwriteQuery.equal("user_id", user_id))
    
    queries.append(AppwriteQuery.order_desc("created_at"))
    
    try:
        result = await repo.list(queries=queries, limit=limit, offset=skip)
        return {
            "items": result.get("documents", []),
            "total": result.get("total", 0)
        }
    except Exception as e:
        logger.error(f"Error listing resumes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{resume_id}")
async def update_resume(resume_id: str, data: ResumeUpdate):
    """Update a resume."""
    repo = ResumesRepository()
    
    resume = await repo.get(resume_id)
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    try:
        update_data = {k: v for k, v in data.dict().items() if v is not None}
        updated = await repo.update(resume_id, update_data)
        return updated
    except Exception as e:
        logger.error(f"Error updating resume: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{resume_id}")
async def delete_resume(resume_id: str):
    """Delete a resume and its file."""
    resumes_repo = ResumesRepository()
    files_repo = FilesRepository()
    
    resume = await resumes_repo.get(resume_id)
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    try:
        # Delete associated file
        if resume.get("stored_file_id"):
            await files_repo.delete_with_storage(resume["stored_file_id"])
        
        # Delete resume
        await resumes_repo.delete(resume_id)
        
        return {"ok": True, "message": "Resume deleted"}
    except Exception as e:
        logger.error(f"Error deleting resume: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user/{user_id}")
async def get_user_resumes(user_id: str):
    """Get all resumes for a user."""
    repo = ResumesRepository()
    result = await repo.get_by_user(user_id)
    return result.get("documents", [])
