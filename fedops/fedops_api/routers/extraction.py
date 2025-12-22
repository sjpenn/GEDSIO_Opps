"""
Extraction Router - API endpoints for document extraction and analysis.

Provides endpoints for the Qualify & Extract frontend module to:
- Run AI-powered extraction on uploaded files
- Get extraction history
- Get extraction status
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, delete
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import logging
import uuid
import json

from fedops_api.deps import get_db
from fedops_core.db.models import StoredFile, DocumentChunk, ExtractionHistory
from fedops_core.services.ai_service import AIService
from fedops_core.services.docling_chunker import DoclingChunker

router = APIRouter()
logger = logging.getLogger(__name__)

# Pydantic models for request/response
class ExtractionRequest(BaseModel):
    """Request to run extraction on files."""
    file_ids: List[int]
    extraction_types: List[str]
    paste_text: Optional[str] = None

class ExtractionResult(BaseModel):
    """Single extraction result."""
    id: str
    type: str
    content: str
    timestamp: str
    files: List[str]
    source: str

class ExtractionResponse(BaseModel):
    """Response from extraction."""
    success: bool
    extraction_id: str
    results: List[ExtractionResult]
    error: Optional[str] = None

class ExtractionHistoryItem(BaseModel):
    """History item for past extractions."""
    id: str
    timestamp: str
    types: List[str]
    file_count: int
    preview: str

# Extraction type prompts
EXTRACTION_PROMPTS = {
    "critical-bid": """Analyze the document(s) and extract critical bid decision information:
1. Contract value and ceiling
2. Period of performance
3. Place of performance
4. Set-aside type (if any)
5. Competition type (full & open, sole source, etc.)
6. Key deadlines
7. Any disqualifying requirements

Return as structured JSON with these fields.""",

    "priorities": """Extract the Commissioner's Priorities and core requirements:
1. Primary objectives
2. Key performance indicators
3. Success criteria
4. Priority deliverables
5. Strategic alignment requirements

Return as structured JSON with priorities ranked by importance.""",

    "compliance": """Extract all compliance requirements and non-negotiables:
1. Security clearances required
2. Certifications needed
3. Insurance requirements
4. Facility requirements
5. Small business requirements
6. Mandatory experience thresholds
7. Past performance requirements

Return as structured JSON categorized by requirement type.""",

    "statistics": """Extract all statistics and metrics from the documents:
1. Contract values and ceilings
2. FTE counts
3. Performance metrics
4. Timeline durations
5. Budget allocations
6. Volume requirements

Return as structured JSON with all numeric data.""",

    "dates": """Extract all dates and timelines:
1. Proposal due date
2. Questions deadline
3. Expected award date
4. Period of performance dates
5. Option periods
6. Key milestones

Return as structured JSON with dates in ISO format.""",

    "questions": """Extract potential bid questions to ask the contracting officer:
1. Ambiguous requirements
2. Missing information
3. Clarification needs
4. Technical questions
5. Contract terms questions

Return as structured JSON with questions and context.""",

    "two-pages": """Provide a comprehensive 2-page executive summary:
1. Opportunity overview
2. Key requirements
3. Evaluation criteria
4. Timeline
5. Budget/pricing structure
6. Risks and considerations

Format as professional executive summary.""",

    "one-page": """Provide a 1-page summary covering:
1. Opportunity overview
2. Key requirements
3. Critical dates
4. Main evaluation factors

Format as concise executive summary.""",

    "half-page": """Provide a half-page quick summary:
1. What: Brief description
2. Who: Agency and contact
3. When: Key dates
4. Why: Strategic value

Format as brief synopsis.""",

    "paragraph": """Provide a single paragraph summary of the opportunity highlighting the most critical information for a quick bid/no-bid decision.""",
}


@router.post("/run", response_model=ExtractionResponse)
async def run_extraction(
    request: ExtractionRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Run AI-powered extraction on uploaded files.
    
    Args:
        request: ExtractionRequest with file_ids and extraction_types
        
    Returns:
        ExtractionResponse with results
    """
    extraction_id = str(uuid.uuid4())
    results: List[ExtractionResult] = []
    file_names: List[str] = []
    
    try:
        # Gather content from files
        combined_content = ""
        
        if request.file_ids:
            for file_id in request.file_ids:
                # Get file info
                result = await db.execute(
                    select(StoredFile).where(StoredFile.id == file_id)
                )
                stored_file = result.scalar_one_or_none()
                
                if not stored_file:
                    logger.warning(f"File {file_id} not found")
                    continue
                    
                file_names.append(stored_file.filename)
                
                # Get chunks for this file
                chunks_result = await db.execute(
                    select(DocumentChunk)
                    .where(DocumentChunk.stored_file_id == file_id)
                    .order_by(DocumentChunk.chunk_index)
                )
                chunks = chunks_result.scalars().all()
                
                if chunks:
                    file_content = "\n\n".join([c.content for c in chunks])
                    combined_content += f"\n\n--- {stored_file.filename} ---\n\n{file_content}"
                else:
                    # No chunks, try to read file directly
                    try:
                        chunker = DoclingChunker()
                        parsed = await chunker.parse_file(stored_file.file_path)
                        if parsed:
                            file_content = "\n".join([el.text for el in parsed])
                            combined_content += f"\n\n--- {stored_file.filename} ---\n\n{file_content}"
                    except Exception as e:
                        logger.error(f"Error reading file {file_id}: {e}")
        
        # Add paste text if provided
        if request.paste_text:
            combined_content += f"\n\n--- Pasted Text ---\n\n{request.paste_text}"
            file_names.append("Pasted Text")
        
        if not combined_content.strip():
            raise HTTPException(
                status_code=400,
                detail="No content found in specified files or paste text"
            )
        
        # Truncate content if too long (roughly 100k chars ~ 25k tokens)
        max_content_length = 100000
        if len(combined_content) > max_content_length:
            combined_content = combined_content[:max_content_length] + "\n\n[Content truncated...]"
        
        # Initialize AI service
        ai_service = AIService()
        
        # Run each extraction type
        for extraction_type in request.extraction_types:
            prompt_template = EXTRACTION_PROMPTS.get(extraction_type)
            
            if not prompt_template:
                # Handle custom extraction types
                if extraction_type.startswith("custom"):
                    prompt_template = """Analyze the document(s) and provide a custom extraction 
                    based on the document content. Return structured information."""
                else:
                    logger.warning(f"Unknown extraction type: {extraction_type}")
                    continue
            
            # Build full prompt
            full_prompt = f"""{prompt_template}

Document Content:
{combined_content}

Provide your analysis:"""
            
            try:
                # Call AI service
                response = await ai_service.generate_content(full_prompt, timeout=120)
                
                # Create result
                result = ExtractionResult(
                    id=f"{extraction_id}-{extraction_type}",
                    type=extraction_type,
                    content=response,
                    timestamp=datetime.utcnow().isoformat(),
                    files=file_names,
                    source="AI Analysis"
                )
                results.append(result)
                
            except Exception as e:
                logger.error(f"Error in extraction type {extraction_type}: {e}")
                # Add error result
                results.append(ExtractionResult(
                    id=f"{extraction_id}-{extraction_type}",
                    type=extraction_type,
                    content=f"Error during extraction: {str(e)}",
                    timestamp=datetime.utcnow().isoformat(),
                    files=file_names,
                    source="Error"
                ))
        
        # Save to history (DB)
        history_entry = ExtractionHistory(
            id=extraction_id,
            timestamp=datetime.utcnow(),
            extraction_types=request.extraction_types,
            file_count=len(file_names),
            files=file_names,
            results=[r.dict() for r in results],
            preview=results[0].content[:200] + "..." if results else "No results"
        )
        db.add(history_entry)
        await db.commit()
        
        return ExtractionResponse(
            success=True,
            extraction_id=extraction_id,
            results=results
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        return ExtractionResponse(
            success=False,
            extraction_id=extraction_id,
            results=[],
            error=str(e)
        )


@router.get("/history", response_model=List[ExtractionHistoryItem])
async def get_extraction_history(
    limit: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """
    Get extraction history.
    
    Args:
        limit: Maximum number of history items to return
        
    Returns:
        List of extraction history items
    """
    result = await db.execute(
        select(ExtractionHistory)
        .order_by(desc(ExtractionHistory.timestamp))
        .limit(limit)
    )
    history = result.scalars().all()
    
    items = []
    for h in history:
        items.append(ExtractionHistoryItem(
            id=h.id,
            timestamp=h.timestamp.isoformat(),
            types=h.extraction_types,
            file_count=h.file_count,
            preview=h.preview or ""
        ))
    return items


@router.get("/{extraction_id}")
async def get_extraction(
    extraction_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific extraction by ID.
    
    Args:
        extraction_id: The extraction ID
        
    Returns:
        Full extraction details
    """
    result = await db.execute(
        select(ExtractionHistory).where(ExtractionHistory.id == extraction_id)
    )
    hist = result.scalar_one_or_none()
    
    if not hist:
        raise HTTPException(status_code=404, detail="Extraction not found")
        
    return {
        "id": hist.id,
        "timestamp": hist.timestamp.isoformat(),
        "types": hist.extraction_types,
        "file_count": hist.file_count,
        "files": hist.files,
        "results": hist.results,
        "preview": hist.preview
    }


@router.delete("/{extraction_id}")
async def delete_extraction(
    extraction_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete an extraction from history.
    
    Args:
        extraction_id: The extraction ID to delete
        
    Returns:
        Success message
    """
    result = await db.execute(
        select(ExtractionHistory).where(ExtractionHistory.id == extraction_id)
    )
    hist = result.scalar_one_or_none()
    
    if hist:
        await db.delete(hist)
        await db.commit()
        return {"message": "Extraction deleted"}
    
    raise HTTPException(status_code=404, detail="Extraction not found")
