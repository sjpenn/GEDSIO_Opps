"""
Extraction Router - Appwrite Version

API endpoints for document extraction and analysis using Appwrite.
Provides endpoints for the Qualify & Extract frontend module to:
- Run AI-powered extraction on uploaded files
- Get extraction history
- Get extraction status
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import logging
import uuid

from fedops_core.services.ai_service import AIService
from fedops_core.services.files_repository import FilesRepository

router = APIRouter()
logger = logging.getLogger(__name__)


# Pydantic models for request/response
class ExtractionRequest(BaseModel):
    """Request to run extraction on files."""
    file_ids: List[str]  # Appwrite uses string IDs
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


# In-memory storage for extraction history (in production, could use Appwrite collection)
extraction_history: List[dict] = []


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
    background_tasks: BackgroundTasks
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
        # Gather content from files using Appwrite
        combined_content = ""
        files_repo = FilesRepository()
        
        if request.file_ids:
            for file_id in request.file_ids:
                try:
                    # Get file metadata from Appwrite
                    file_doc = await files_repo.get(file_id)
                    
                    if not file_doc:
                        logger.warning(f"File {file_id} not found")
                        continue
                    
                    filename = file_doc.get("filename", f"file_{file_id}")
                    file_names.append(filename)
                    
                    # Try to get parsed content if available
                    parsed_content = file_doc.get("parsed_content", "")
                    
                    if parsed_content:
                        combined_content += f"\n\n--- {filename} ---\n\n{parsed_content}"
                    else:
                        # Download and extract content from file
                        file_content = await files_repo.download_file(file_id)
                        if file_content:
                            # For now, decode as text if possible
                            try:
                                text_content = file_content.decode('utf-8', errors='ignore')
                                combined_content += f"\n\n--- {filename} ---\n\n{text_content[:50000]}"
                            except Exception:
                                logger.warning(f"Could not decode file {file_id} as text")
                                
                except Exception as e:
                    logger.error(f"Error processing file {file_id}: {e}")
        
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
        
        # Save to history
        history_item = {
            "id": extraction_id,
            "timestamp": datetime.utcnow().isoformat(),
            "types": request.extraction_types,
            "file_count": len(file_names),
            "files": file_names,
            "results": [r.dict() for r in results],
            "preview": results[0].content[:200] + "..." if results else "No results"
        }
        extraction_history.insert(0, history_item)
        
        # Keep only last 50 history items
        while len(extraction_history) > 50:
            extraction_history.pop()
        
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
async def get_extraction_history(limit: int = 20):
    """
    Get extraction history.
    
    Args:
        limit: Maximum number of history items to return
        
    Returns:
        List of extraction history items
    """
    items = []
    for hist in extraction_history[:limit]:
        items.append(ExtractionHistoryItem(
            id=hist["id"],
            timestamp=hist["timestamp"],
            types=hist["types"],
            file_count=hist["file_count"],
            preview=hist["preview"]
        ))
    return items


@router.get("/{extraction_id}")
async def get_extraction(extraction_id: str):
    """
    Get a specific extraction by ID.
    
    Args:
        extraction_id: The extraction ID
        
    Returns:
        Full extraction details
    """
    for hist in extraction_history:
        if hist["id"] == extraction_id:
            return hist
    
    raise HTTPException(status_code=404, detail="Extraction not found")


@router.delete("/{extraction_id}")
async def delete_extraction(extraction_id: str):
    """
    Delete an extraction from history.
    
    Args:
        extraction_id: The extraction ID to delete
        
    Returns:
        Success message
    """
    global extraction_history
    extraction_history = [h for h in extraction_history if h["id"] != extraction_id]
    return {"message": "Extraction deleted"}
