"""
Files Router - Appwrite Version

API endpoints for file management using Appwrite Storage.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Query
from fastapi.responses import StreamingResponse
from typing import Optional, List
import logging
import io

from fedops_core.services.files_repository import FilesRepository
from fedops_core.services.opportunities_repository import OpportunitiesRepository
from appwrite.query import Query as AppwriteQuery

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/")
async def list_files(
    skip: int = 0,
    limit: int = 25,
    opportunity_id: Optional[str] = Query(None, description="Filter by opportunity ID")
):
    """List stored files with optional filtering."""
    repo = FilesRepository()
    
    queries = []
    if opportunity_id:
        queries.append(AppwriteQuery.equal("opportunity_id", opportunity_id))
    
    queries.append(AppwriteQuery.order_desc("created_at"))
    
    try:
        result = await repo.list(queries=queries, limit=limit, offset=skip)
        return {
            "items": result.get("documents", []),
            "total": result.get("total", 0)
        }
    except Exception as e:
        logger.error(f"Error listing files: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{id}")
async def get_file(id: str):
    """Get file metadata by ID."""
    repo = FilesRepository()
    
    file = await repo.get(id)
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    return file


@router.get("/{id}/download")
async def download_file(id: str):
    """Download a file from Appwrite Storage."""
    repo = FilesRepository()
    
    file = await repo.get(id)
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    content = await repo.download_file(id)
    if content is None:
        raise HTTPException(status_code=404, detail="File content not found in storage")
    
    filename = file.get("filename", "download")
    file_type = file.get("file_type", "")
    
    # Determine content type
    content_type_map = {
        "pdf": "application/pdf",
        "doc": "application/msword",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "xls": "application/vnd.ms-excel",
        "txt": "text/plain",
        "zip": "application/zip"
    }
    content_type = content_type_map.get(file_type, "application/octet-stream")
    
    return StreamingResponse(
        io.BytesIO(content),
        media_type=content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )


@router.get("/{id}/view")
async def view_file(id: str):
    """Get a view URL for a file (for PDFs, etc)."""
    repo = FilesRepository()
    
    file = await repo.get(id)
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    url = await repo.get_file_url(id)
    if not url:
        raise HTTPException(status_code=404, detail="File not available for viewing")
    
    return {"url": url}


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    opportunity_id: Optional[str] = Query(None, description="Associate with opportunity")
):
    """Upload a file to Appwrite Storage."""
    repo = FilesRepository()
    
    # Validate opportunity exists if provided
    if opportunity_id:
        opp_repo = OpportunitiesRepository()
        opportunity = await opp_repo.get(opportunity_id)
        if not opportunity:
            raise HTTPException(status_code=404, detail="Opportunity not found")
    
    try:
        content = await file.read()
        result = await repo.upload_from_bytes(
            content=content,
            filename=file.filename,
            opportunity_id=opportunity_id
        )
        return result
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{id}")
async def delete_file(id: str):
    """Delete a file from both database and storage."""
    repo = FilesRepository()
    
    file = await repo.get(id)
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        success = await repo.delete_with_storage(id)
        if success:
            return {"ok": True, "message": "File deleted"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete file")
    except Exception as e:
        logger.error(f"Error deleting file: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/opportunity/{opportunity_id}")
async def get_files_by_opportunity(opportunity_id: str, limit: int = 100):
    """Get all files for a specific opportunity."""
    repo = FilesRepository()
    
    result = await repo.get_by_opportunity(opportunity_id, limit)
    return result.get("documents", [])
