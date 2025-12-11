from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from fedops_core.db.engine import get_db
from fedops_core.services.resume_service import ResumeService
from fedops_core.db.models import StoredFile, Resume
from fedops_core.schemas.resume_schemas import ResumeData
import shutil
import os
import uuid
from datetime import datetime

router = APIRouter(
    prefix="/resumes",
    tags=["resumes"]
)

VALID_EXTENSIONS = {'.pdf', '.docx', '.doc', '.txt'}

from fastapi import BackgroundTasks
from typing import List

@router.get("/")
async def list_resumes(
    user_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
    skip: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """
    List all resumes with optional filtering.
    """
    query = select(Resume)
    
    if user_id:
        query = query.where(Resume.user_id == user_id)
    if status:
        query = query.where(Resume.status == status)
    
    # Order by newest first
    query = query.order_by(Resume.created_at.desc()).offset(skip).limit(limit)
    
    result = await db.execute(query)
    resumes = result.scalars().all()
    
    return resumes


@router.post("/upload")
async def upload_resume(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user_id: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Uploads a resume file and initiates parsing in the background.
    """
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in VALID_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Invalid file type. Allowed: {VALID_EXTENSIONS}")

    # Save file
    safe_filename = f"{uuid.uuid4()}{ext}"
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, safe_filename)
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")

    # Create StoredFile entry
    stored_file = StoredFile(
        filename=file.filename,
        file_path=os.path.abspath(file_path),
        file_type=ext,
        file_size=os.path.getsize(file_path),
        s3_uri=None, # Not using S3 for now
        created_at=datetime.utcnow()
    )
    db.add(stored_file)
    await db.commit()
    await db.refresh(stored_file)

    # create resume entry
    service = ResumeService(db)
    resume = await service.create_resume_entry(stored_file.id, user_id)
    
    # Trigger async parsing in background
    # Note: We need to ensure a new DB session is used in the background task if ResumeService depends on it
    # But ResumeService takes 'db' in init. Passing the current async session context to background task 
    # might be problematic if the session closes after request. 
    # Ideally we'd use a dependency injection approach for bg tasks or handle session inside.
    # For now, let's assume we can't easily pass the scoped session. 
    # We'll create a standalone wrapper function that creates a new session.
    
    background_tasks.add_task(run_parsing_task, resume.id)
    
    return resume

async def run_parsing_task(resume_id: int):
    # This needs to create its own session
    from fedops_core.db.engine import AsyncSessionLocal
    import traceback
    
    try:
        async with AsyncSessionLocal() as db:
            service = ResumeService(db)
            await service.parse_resume(resume_id)
    except Exception as e:
        # If we can't even get the DB session or service fails catastrophically
        print(f"CRITICAL BACKGROUND TASK ERROR: {e}")
        traceback.print_exc()
        # Try to update status if we can get a session
        try:
             async with AsyncSessionLocal() as db:
                from fedops_core.db.models import Resume
                from sqlalchemy import update
                await db.execute(
                    update(Resume)
                    .where(Resume.id == resume_id)
                    .values(status="FAILED", error_message=f"System Error: {str(e)}")
                )
                await db.commit()
        except:
            pass

@router.get("/{resume_id}")
async def get_resume(resume_id: int, db: AsyncSession = Depends(get_db)):
    """
    Get resume details.
    """
    service = ResumeService(db)
    result = await db.execute(select(Resume).where(Resume.id == resume_id))
    resume = result.scalar_one_or_none()
    
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
        
    return resume

@router.post("/{resume_id}/format")
async def format_resume(
    resume_id: int, 
    include_signature: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """
    Generate formatted resume.
    """
    service = ResumeService(db)
    try:
        resume = await service.generate_formatted_resume(resume_id, include_signature)
        return resume
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{resume_id}/download")
async def download_resume(resume_id: int, db: AsyncSession = Depends(get_db)):
    """
    Returns the formatted HTML content.
    """
    result = await db.execute(select(Resume).where(Resume.id == resume_id))
    resume = result.scalar_one_or_none()
    
    if not resume or not resume.formatted_content_html:
         raise HTTPException(status_code=404, detail="Formatted content not found")
         
    return {"html": resume.formatted_content_html}
