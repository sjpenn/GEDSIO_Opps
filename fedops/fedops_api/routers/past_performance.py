"""
API Router for Past Performance Questionnaires
Handles CRUD operations, AI content generation, and export functionality
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from fedops_core.db.engine import get_db
from fedops_core.schemas.past_performance_schemas import (
    PastPerformanceCreate,
    PastPerformanceUpdate,
    PastPerformanceResponse,
    GenerateSectionRequest,
    GenerateSectionResponse,
    StructuredOutputRequest,
    StructuredOutputResponse,
    QuestionnaireTemplate,
    PastPerformanceMatchRequest,
    PastPerformanceMatchResponse
)
from fedops_core.services.past_performance_service import PastPerformanceService
from fedops_core.db.models import OpportunityScore
from sqlalchemy import select


router = APIRouter(
    prefix="/past-performance",
    tags=["past_performance"]
)


@router.post("/", response_model=PastPerformanceResponse)
async def create_past_performance(
    data: PastPerformanceCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new past performance questionnaire"""
    try:
        past_perf = await PastPerformanceService.create_past_performance(db, data)
        return past_perf
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{past_perf_id}", response_model=PastPerformanceResponse)
async def get_past_performance(
    past_perf_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific past performance by ID"""
    past_perf = await PastPerformanceService.get_past_performance(db, past_perf_id)
    if not past_perf:
        raise HTTPException(status_code=404, detail="Past performance not found")
    return past_perf


@router.get("/entity/{entity_uei}", response_model=List[PastPerformanceResponse])
async def list_entity_past_performances(
    entity_uei: str,
    status: Optional[str] = Query(None, description="Filter by status"),
    db: AsyncSession = Depends(get_db)
):
    """List all past performances for a specific entity"""
    try:
        past_perfs = await PastPerformanceService.list_by_entity(db, entity_uei, status)
        return past_perfs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[PastPerformanceResponse])
async def list_all_past_performances(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of results"),
    db: AsyncSession = Depends(get_db)
):
    """List all past performances with optional filtering"""
    try:
        past_perfs = await PastPerformanceService.list_all(db, status, limit)
        return past_perfs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{past_perf_id}", response_model=PastPerformanceResponse)
async def update_past_performance(
    past_perf_id: int,
    data: PastPerformanceUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update an existing past performance"""
    try:
        past_perf = await PastPerformanceService.update_past_performance(db, past_perf_id, data)
        if not past_perf:
            raise HTTPException(status_code=404, detail="Past performance not found")
        return past_perf
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{past_perf_id}")
async def delete_past_performance(
    past_perf_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete a past performance"""
    try:
        success = await PastPerformanceService.delete_past_performance(db, past_perf_id)
        if not success:
            raise HTTPException(status_code=404, detail="Past performance not found")
        return {"message": "Past performance deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{past_perf_id}/generate-section", response_model=GenerateSectionResponse)
async def generate_section_content(
    past_perf_id: int,
    request: GenerateSectionRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Generate AI content for a specific questionnaire section.
    
    Uses Perplexity AI to generate professional content based on:
    - Award data (contract details, value, dates, agency)
    - Opportunity context (if linked)
    - Section-specific guidance
    """
    try:
        result = await PastPerformanceService.generate_section_content(db, past_perf_id, request)
        return GenerateSectionResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{past_perf_id}/export", response_model=StructuredOutputResponse)
async def export_structured_output(
    past_perf_id: int,
    request: StructuredOutputRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Export past performance as structured output.
    
    Supported formats:
    - json: Structured JSON with all sections
    - text: Plain text formatted document
    - markdown: Markdown formatted document
    """
    try:
        result = await PastPerformanceService.export_structured_output(
            db, 
            past_perf_id, 
            request.format, 
            request.include_metadata
        )
        return StructuredOutputResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates/questionnaire", response_model=QuestionnaireTemplate)
async def get_questionnaire_template():
    """Get the questionnaire template structure with section descriptions"""
    return PastPerformanceService.get_template()


@router.post("/{past_perf_id}/generate-citations")
async def generate_citations(
    past_perf_id: int,
    section_l_text: str,
    section_m_text: str,
    sow_pws_text: str,
    agency_name: str,
    solicitation_id: Optional[str] = None,
    solicitation_title: Optional[str] = None,
    required_citations: int = 3,
    db: AsyncSession = Depends(get_db)
):
    """
    Generate comprehensive past performance citations for a solicitation.
    
    Takes Section L, M, and SOW/PWS text and generates structured citations
    tailored to the solicitation requirements.
    
    Returns:
        Dictionary with solicitation_meta and citations array
    """
    try:
        from fedops_core.services.ai_service import AIService
        ai_service = AIService()
        
        result = await PastPerformanceService.generate_citations_for_solicitation(
            db=db,
            past_perf_id=past_perf_id,
            section_l_text=section_l_text,
            section_m_text=section_m_text,
            sow_pws_text=sow_pws_text,
            agency_name=agency_name,
            solicitation_id=solicitation_id,
            solicitation_title=solicitation_title,
            required_citations=required_citations,
            ai_service=ai_service
        )
        
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{past_perf_id}/citations")
async def get_citations(
    past_perf_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get stored citations for a past performance record.
    
    Returns:
        Dictionary with solicitation_meta and citations, or null if not generated
    """
    try:
        citations = await PastPerformanceService.get_citations(db, past_perf_id)
        if citations is None:
            return {"citations": None, "message": "No citations generated yet"}
        return citations
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/match", response_model=PastPerformanceMatchResponse)
async def match_past_performance(
    request: PastPerformanceMatchRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Identify relevant past performance projects for an opportunity based on analysis.
    """
    try:
        # Fetch Opportunity Analysis
        score_result = await db.execute(select(OpportunityScore).where(OpportunityScore.opportunity_id == request.opportunity_id))
        score = score_result.scalar_one_or_none()
        
        if not score or not score.details:
            raise HTTPException(status_code=404, detail="Opportunity analysis not found. Please run analysis first.")
        
        # Extract requirements from score.details
        # We try to extract key sections from the possibly nested JSON structure
        details = score.details
        
        requirements = {
            "section_m": details.get("evaluation_criteria", "N/A"), # Evaluation Factors
            "sow": details.get("scope_of_work", "N/A"), # SOW
            "section_l": details.get("solicitation_instructions", "N/A"), # Instructions
            "naics": details.get("opportunity", {}).get("naics_code", "N/A")
        }
        
        # If specific structured sections aren't found at top level, try looking in 'solicitation' or 'technical' keys
        if "solicitation" in details:
             if "evaluation_criteria" in details["solicitation"]:
                 requirements["section_m"] = details["solicitation"]["evaluation_criteria"]
        
        matches = await PastPerformanceService.match_projects_for_solicitation(
            db, 
            request.entity_uei, 
            requirements
        )
        
        return {"matches": matches}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


