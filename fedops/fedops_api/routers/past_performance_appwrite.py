"""
Past Performance Router - Appwrite Version

API endpoints for past performance management using Appwrite database.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
import logging

from fedops_core.services.additional_repositories import PastPerformancesRepository
from fedops_core.services.entities_repository import EntitiesRepository
from appwrite.query import Query as AppwriteQuery

router = APIRouter()
logger = logging.getLogger(__name__)


class PastPerformanceCreate(BaseModel):
    entity_uei: str
    title: str
    award_id: Optional[str] = None
    opportunity_id: Optional[str] = None
    source_document_id: Optional[str] = None
    status: str = "DRAFT"
    questionnaire_data: Optional[Dict[str, Any]] = None


class PastPerformanceUpdate(BaseModel):
    title: Optional[str] = None
    status: Optional[str] = None
    questionnaire_data: Optional[Dict[str, Any]] = None
    citations_data: Optional[Dict[str, Any]] = None


class GenerateSectionRequest(BaseModel):
    section_key: str
    context: Optional[str] = None


class StructuredOutputRequest(BaseModel):
    format: str = "json"  # json, text, markdown


@router.post("/")
async def create_past_performance(data: PastPerformanceCreate):
    """Create a new past performance questionnaire."""
    repo = PastPerformancesRepository()
    entities_repo = EntitiesRepository()
    
    # Verify entity exists
    entity = await entities_repo.get_by_uei(data.entity_uei)
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    
    try:
        # Initialize questionnaire data if not provided
        questionnaire_data = data.questionnaire_data or {
            "project_overview": {"content": "", "generated": False},
            "scope_of_work": {"content": "", "generated": False},
            "technical_approach": {"content": "", "generated": False},
            "challenges_solutions": {"content": "", "generated": False},
            "results_outcomes": {"content": "", "generated": False},
            "relevance": {"content": "", "generated": False},
            "references": {"content": "", "generated": False}
        }
        
        pp_data = data.dict()
        pp_data["questionnaire_data"] = questionnaire_data
        
        new_pp = await repo.create(pp_data)
        return new_pp
    except Exception as e:
        logger.error(f"Error creating past performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{past_perf_id}")
async def get_past_performance(past_perf_id: str):
    """Get a specific past performance by ID."""
    repo = PastPerformancesRepository()
    
    pp = await repo.get(past_perf_id)
    if not pp:
        raise HTTPException(status_code=404, detail="Past performance not found")
    return pp


@router.get("/entity/{entity_uei}")
async def list_entity_past_performances(
    entity_uei: str,
    status: Optional[str] = Query(None, description="Filter by status")
):
    """List all past performances for an entity."""
    repo = PastPerformancesRepository()
    
    result = await repo.get_by_entity(entity_uei)
    documents = result.get("documents", [])
    
    # Filter by status if provided
    if status:
        documents = [d for d in documents if d.get("status") == status]
    
    return documents


@router.get("/")
async def list_all_past_performances(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=100)
):
    """List all past performances with optional filtering."""
    repo = PastPerformancesRepository()
    
    queries = []
    if status:
        queries.append(AppwriteQuery.equal("status", status))
    
    queries.append(AppwriteQuery.order_desc("created_at"))
    
    try:
        result = await repo.list(queries=queries, limit=limit)
        return {
            "items": result.get("documents", []),
            "total": result.get("total", 0)
        }
    except Exception as e:
        logger.error(f"Error listing past performances: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{past_perf_id}")
async def update_past_performance(past_perf_id: str, data: PastPerformanceUpdate):
    """Update a past performance."""
    repo = PastPerformancesRepository()
    
    pp = await repo.get(past_perf_id)
    if not pp:
        raise HTTPException(status_code=404, detail="Past performance not found")
    
    try:
        update_data = {k: v for k, v in data.dict().items() if v is not None}
        updated = await repo.update(past_perf_id, update_data)
        return updated
    except Exception as e:
        logger.error(f"Error updating past performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{past_perf_id}")
async def delete_past_performance(past_perf_id: str):
    """Delete a past performance."""
    repo = PastPerformancesRepository()
    
    pp = await repo.get(past_perf_id)
    if not pp:
        raise HTTPException(status_code=404, detail="Past performance not found")
    
    try:
        await repo.delete(past_perf_id)
        return {"ok": True, "message": "Past performance deleted"}
    except Exception as e:
        logger.error(f"Error deleting past performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{past_perf_id}/section/{section_key}")
async def update_section(past_perf_id: str, section_key: str, content: str):
    """Update a specific questionnaire section."""
    repo = PastPerformancesRepository()
    
    pp = await repo.get(past_perf_id)
    if not pp:
        raise HTTPException(status_code=404, detail="Past performance not found")
    
    questionnaire_data = pp.get("questionnaire_data", {})
    
    if section_key not in questionnaire_data:
        raise HTTPException(status_code=400, detail=f"Invalid section: {section_key}")
    
    questionnaire_data[section_key]["content"] = content
    questionnaire_data[section_key]["generated"] = False
    
    try:
        await repo.update(past_perf_id, {"questionnaire_data": questionnaire_data})
        return {"ok": True, "section": section_key}
    except Exception as e:
        logger.error(f"Error updating section: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{past_perf_id}/approve")
async def approve_past_performance(past_perf_id: str, approved_by: str):
    """Approve a past performance questionnaire."""
    repo = PastPerformancesRepository()
    
    pp = await repo.get(past_perf_id)
    if not pp:
        raise HTTPException(status_code=404, detail="Past performance not found")
    
    from datetime import datetime
    
    try:
        await repo.update(past_perf_id, {
            "status": "APPROVED",
            "approved_by": approved_by,
            "approved_at": datetime.utcnow().isoformat()
        })
        return {"ok": True, "message": "Past performance approved"}
    except Exception as e:
        logger.error(f"Error approving past performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{past_perf_id}/export")
async def export_past_performance(
    past_perf_id: str,
    format: str = Query("json", description="Export format: json, text, markdown")
):
    """Export past performance in various formats."""
    repo = PastPerformancesRepository()
    
    pp = await repo.get(past_perf_id)
    if not pp:
        raise HTTPException(status_code=404, detail="Past performance not found")
    
    questionnaire_data = pp.get("questionnaire_data", {})
    
    if format == "json":
        return {
            "id": pp.get("id"),
            "title": pp.get("title"),
            "entity_uei": pp.get("entity_uei"),
            "status": pp.get("status"),
            "sections": questionnaire_data
        }
    
    elif format == "text":
        text_output = f"PAST PERFORMANCE: {pp.get('title')}\n"
        text_output += "=" * 50 + "\n\n"
        
        section_titles = {
            "project_overview": "Project Overview",
            "scope_of_work": "Scope of Work",
            "technical_approach": "Technical Approach",
            "challenges_solutions": "Challenges & Solutions",
            "results_outcomes": "Results & Outcomes",
            "relevance": "Relevance",
            "references": "References"
        }
        
        for key, title in section_titles.items():
            section = questionnaire_data.get(key, {})
            content = section.get("content", "")
            text_output += f"{title}\n"
            text_output += "-" * len(title) + "\n"
            text_output += f"{content}\n\n"
        
        return {"content": text_output, "format": "text"}
    
    elif format == "markdown":
        md_output = f"# Past Performance: {pp.get('title')}\n\n"
        
        section_titles = {
            "project_overview": "Project Overview",
            "scope_of_work": "Scope of Work",
            "technical_approach": "Technical Approach",
            "challenges_solutions": "Challenges & Solutions",
            "results_outcomes": "Results & Outcomes",
            "relevance": "Relevance",
            "references": "References"
        }
        
        for key, title in section_titles.items():
            section = questionnaire_data.get(key, {})
            content = section.get("content", "")
            md_output += f"## {title}\n\n{content}\n\n"
        
        return {"content": md_output, "format": "markdown"}
    
    else:
        raise HTTPException(status_code=400, detail="Invalid format. Use: json, text, markdown")


@router.get("/template")
async def get_questionnaire_template():
    """Get the questionnaire template structure."""
    return {
        "sections": {
            "project_overview": {
                "title": "Project Overview",
                "description": "Brief overview of the project, client, and objectives"
            },
            "scope_of_work": {
                "title": "Scope of Work",
                "description": "Detailed description of work performed"
            },
            "technical_approach": {
                "title": "Technical Approach",
                "description": "Methods, technologies, and approach used"
            },
            "challenges_solutions": {
                "title": "Challenges & Solutions",
                "description": "Problems encountered and how they were resolved"
            },
            "results_outcomes": {
                "title": "Results & Outcomes",
                "description": "Quantifiable results and outcomes achieved"
            },
            "relevance": {
                "title": "Relevance",
                "description": "How this experience relates to the opportunity"
            },
            "references": {
                "title": "References",
                "description": "Client references and contact information"
            }
        }
    }
