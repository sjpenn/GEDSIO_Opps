from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, BackgroundTasks, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fedops_core.db.engine import get_db
from fedops_core.db.models import DocumentChunk, StoredFile
from fedops_core.schemas.file import FileResponse as FileResponseSchema, FileUpdate
from fedops_core.services.file_service import FileService
from fedops_core.services.docling_service import DoclingService
import json
import logging
from pathlib import Path
from fastapi.responses import JSONResponse, FileResponse

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/upload", response_model=FileResponseSchema)
async def upload_file(
    file: UploadFile = File(...),
    opportunity_id: int = Form(None),
    db: AsyncSession = Depends(get_db)
):
    service = FileService(db)
    return await service.upload_file(file, opportunity_id)

@router.get("/", response_model=List[FileResponseSchema])
async def list_files(
    opportunity_id: int = None,
    db: AsyncSession = Depends(get_db)
):
    service = FileService(db)
    return await service.get_files(opportunity_id)

@router.get("/{file_id}", response_model=FileResponseSchema)
async def get_file(file_id: int, db: AsyncSession = Depends(get_db)):
    service = FileService(db)
    file = await service.get_file(file_id)
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Fallback: If parsed_content is missing, try to reassemble from chunks
    # This handles files processed via DoclingChunker which stores data in the document_chunks table
    if not file.parsed_content:
        try:
            chunks_result = await db.execute(
                select(DocumentChunk)
                .where(DocumentChunk.stored_file_id == file_id)
                .order_by(DocumentChunk.chunk_index)
            )
            chunks = chunks_result.scalars().all()
            if chunks:
                logger.info(f"Populating parsed_content from {len(chunks)} chunks for file {file_id}")
                file.parsed_content = "\n\n".join(chunk.content for chunk in chunks)
                
        except Exception as e:
            logger.error(f"Error reassembling content from chunks for file {file_id}: {e}")
            
    # Second fallback: If still no content, try to process the file on-demand
    # This handles files that were imported but processing failed or was skipped
    if not file.parsed_content:
        logger.info(f"File {file_id} has no content and no chunks. Attempting on-demand processing.")
        try:
             # Trigger processing
             updated_file = await service.process_file(file_id)
             if updated_file.parsed_content:
                 file.parsed_content = updated_file.parsed_content
                 file.content_summary = updated_file.content_summary
        except Exception as e:
            logger.error(f"On-demand processing failed for file {file_id}: {e}")
            
    return file

@router.post("/{file_id}/process", response_model=FileResponseSchema)
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


@router.get("/{file_id}/chunks")
async def get_file_chunks(
    file_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all chunks for a file, ordered by chunk_index.
    
    This allows the frontend to reassemble file content from stored chunks.
    Chunks are stored during document analysis via the DoclingChunker.
    
    Returns:
        - file_id: The file ID
        - filename: The original filename
        - total_chunks: Total number of chunks
        - chunks: List of chunks with content, page_number, section, etc.
    """
    try:
        # First, verify the file exists
        file_result = await db.execute(
            select(StoredFile).where(StoredFile.id == file_id)
        )
        stored_file = file_result.scalar_one_or_none()
        
        if not stored_file:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Get all chunks for this file, ordered by chunk_index
        chunks_result = await db.execute(
            select(DocumentChunk)
            .where(DocumentChunk.stored_file_id == file_id)
            .order_by(DocumentChunk.chunk_index)
        )
        chunks = chunks_result.scalars().all()
        
        if not chunks:
            logger.info(f"No chunks found for file {file_id} ({stored_file.filename})")
            return {
                "file_id": file_id,
                "filename": stored_file.filename,
                "total_chunks": 0,
                "chunks": [],
                "message": "No chunks available. File may not have been processed yet."
            }
        
        return {
            "file_id": file_id,
            "filename": stored_file.filename,
            "total_chunks": len(chunks),
            "chunks": [
                {
                    "index": chunk.chunk_index,
                    "content": chunk.content,
                    "page_number": chunk.page_number,
                    "section": chunk.section,
                    "chunk_type": getattr(chunk, 'chunk_type', None),
                    "heading_context": getattr(chunk, 'heading_context', None),
                    "metadata": getattr(chunk, 'metadata_', None)
                }
                for chunk in chunks
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching chunks for file {file_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching chunks: {str(e)}")


@router.get("/{file_id}/content")
async def get_file_content_reassembled(
    file_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get the full reassembled content of a file from its chunks.
    
    Returns the content as a single string by joining all chunks in order.
    """
    # First, verify the file exists
    file_result = await db.execute(
        select(StoredFile).where(StoredFile.id == file_id)
    )
    stored_file = file_result.scalar_one_or_none()
    
    if not stored_file:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Get all chunks ordered by index
    chunks_result = await db.execute(
        select(DocumentChunk)
        .where(DocumentChunk.stored_file_id == file_id)
        .order_by(DocumentChunk.chunk_index)
    )
    chunks = chunks_result.scalars().all()
    
    if not chunks:
        # Fallback to parsed_content if available
        if stored_file.parsed_content:
            return {
                "file_id": file_id,
                "filename": stored_file.filename,
                "content": stored_file.parsed_content,
                "source": "parsed_content"
            }
        return {
            "file_id": file_id,
            "filename": stored_file.filename,
            "content": "",
            "source": "none",
            "message": "No content available. File may not have been processed yet."
        }
    
    # Reassemble content from chunks
    full_content = "\n\n".join(chunk.content for chunk in chunks)
    
    return {
        "file_id": file_id,
        "filename": stored_file.filename,
        "content": full_content,
        "source": "chunks",
        "total_chunks": len(chunks)
    }

@router.get("/{file_id}/download", response_class=FileResponse)
async def download_file(
    file_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Download a file by ID."""
    service = FileService(db)
    file_record = await service.get_file(file_id)
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")
        
    file_path = Path(file_record.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File content not found on server")
        
    return FileResponse(
        path=file_path, 
        filename=file_record.filename,
        media_type='application/octet-stream'
    )

@router.get("/{file_id}/view", response_class=FileResponse)
async def view_file(
    file_id: str,
    db: AsyncSession = Depends(get_db)
):
    try:
        """View a file inline by ID (for PDFs etc)."""
        # Validate ID
        if not file_id.isdigit():
             logger.error(f"Invalid file_id format: {file_id}. Expected integer.")
             raise HTTPException(status_code=400, detail=f"Invalid file ID: {file_id}. Please refresh the page.")
             
        file_id_int = int(file_id)
        
        service = FileService(db)
        logger.info(f"Viewing file ID: {file_id_int}")
        
        file_record = await service.get_file(file_id_int)
        if not file_record:
            logger.error(f"File ID {file_id} not found in DB")
            raise HTTPException(status_code=404, detail="File not found")
            
        file_path = Path(file_record.file_path)
        logger.info(f"File path: {file_path}")
        
        if not file_path.exists():
            logger.error(f"File path {file_path} does not exist on disk (CWD: {Path.cwd()})")
            raise HTTPException(status_code=404, detail=f"File content not found on server at {file_path}")
            
        # Determine media type
        media_type = 'application/octet-stream'
        if file_record.filename.lower().endswith('.pdf'):
            media_type = 'application/pdf'
        elif file_record.filename.lower().endswith(('.txt', '.md', '.json', '.log')):
            media_type = 'text/plain'
            
        path_str = str(file_path.absolute())
        return FileResponse(
            path=path_str, 
            filename=file_record.filename,
            media_type=media_type,
            content_disposition_type='inline'
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in view_file for ID {file_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
