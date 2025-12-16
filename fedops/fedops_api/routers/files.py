from typing import List
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, BackgroundTasks, Form
from sqlalchemy.ext.asyncio import AsyncSession
from fedops_core.db.engine import get_db
from fedops_core.schemas.file import FileResponse, FileUpdate
from fedops_core.services.file_service import FileService
from fedops_core.services.docling_service import DoclingService
import json
from pathlib import Path
from fastapi.responses import JSONResponse

router = APIRouter()

@router.post("/upload", response_model=FileResponse)
async def upload_file(
    file: UploadFile = File(...),
    opportunity_id: int = Form(None),
    db: AsyncSession = Depends(get_db)
):
    service = FileService(db)
    return await service.upload_file(file, opportunity_id)

@router.get("/", response_model=List[FileResponse])
async def list_files(
    opportunity_id: int = None,
    db: AsyncSession = Depends(get_db)
):
    service = FileService(db)
    return await service.get_files(opportunity_id)

@router.get("/{file_id}", response_model=FileResponse)
async def get_file(file_id: int, db: AsyncSession = Depends(get_db)):
    service = FileService(db)
    file = await service.get_file(file_id)
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    return file

@router.post("/{file_id}/process", response_model=FileResponse)
async def process_file(
    file_id: int, 
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    service = FileService(db)
    # For simplicity, we'll await it here, but ideally this should be a background task
    # if it takes too long. For now, let's await to return the result immediately
    # or we can use background_tasks.add_task(service.process_file, file_id)
    # But the user wants to "view the contents", so maybe immediate is better for MVP
    # unless it's very slow. Let's try immediate first.
    try:
        return await service.process_file(file_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/import-resources/{opportunity_id}")
async def import_resources(
    opportunity_id: int,
    db: AsyncSession = Depends(get_db)
):
    service = FileService(db)
    try:
        files = await service.import_opportunity_resources(opportunity_id)
        return {"message": f"Imported {len(files)} files", "files": [f.filename for f in files]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{file_id}/docling")
async def get_docling_json(
    file_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get the full Docling extraction JSON for a file.
    Processed on-demand if not already cached.
    """
    service = FileService(db)
    file_record = await service.get_file(file_id)
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")
        
    file_path = file_record.file_path
    
    # Check for sidecar file
    json_path = Path(file_path + ".docling.json")
    if json_path.exists():
        try:
            with open(json_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            # If corrupt, we'll regenerating
            pass
            
    # Generate on demand
    docling_service = DoclingService()
    if not docling_service.docling_available:
        raise HTTPException(status_code=503, detail="Docling service not available")
        
    try:
        result = await docling_service.parse_document(file_path, extract_tables=True)
        if not result.success:
             raise HTTPException(status_code=500, detail=f"Docling parsing failed: {result.error}")
             
        # Cache results
        if result.document_dict:
             with open(json_path, 'w') as f:
                 json.dump(result.document_dict, f)
             return result.document_dict
        else:
             raise HTTPException(status_code=500, detail="No JSON output from Docling")
             
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error generating Docling JSON: {str(e)}")

@router.post("/batch-process")
async def batch_process_files(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    service = FileService(db)
    files = await service.get_files()
    count = 0
    for file in files:
        if not file.content_summary: # Only process unprocessed files
            background_tasks.add_task(service.process_file, file.id)
            count += 1
    return {"message": f"Batch processing started for {count} files"}
