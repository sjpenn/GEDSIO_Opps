"""
API Router for Agency Intelligence
Handles requests for Agency research using Perplexity
"""
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from fedops_core.db.engine import get_db
from fedops_core.db.models import SavedAgencySearch
from fedops_core.services.perplexity_service import perplexity_service
from fedops_core.schemas.competitive_analysis_schemas import AgencyResearchResult

router = APIRouter(
    prefix="/agency_intel",
    tags=["agency_intel"]
)


# --- Request/Response Schemas ---

class AgencyResearchRequest(BaseModel):
    agency_name: str


class SavedAgencySearchSummary(BaseModel):
    id: int
    agency_name: str
    acronym: Optional[str] = None
    icon_type: str = "default"
    last_refreshed_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class SavedAgencySearchDetail(BaseModel):
    id: int
    agency_name: str
    acronym: Optional[str] = None
    icon_type: str = "default"
    overview: Optional[str] = None
    strategic_goals: Optional[List[str]] = None
    budget_outlook: Optional[str] = None
    org_structure: Optional[str] = None
    org_tree: Optional[dict] = None
    key_bureaus: Optional[List[str]] = None
    lines_of_business: Optional[List[dict]] = None
    budget_by_division: Optional[List[dict]] = None
    pain_points: Optional[List[str]] = None
    procurement_priorities: Optional[List[str]] = None
    citations: Optional[List[dict]] = None
    last_refreshed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# --- Helper Functions ---

def detect_icon_type(agency_name: str) -> str:
    """Detect icon type based on agency name keywords"""
    name_lower = agency_name.lower()
    
    if any(kw in name_lower for kw in ["aviation", "faa", "transportation", "fmcsa", "nhtsa"]):
        return "aviation"
    elif any(kw in name_lower for kw in ["defense", "dod", "army", "navy", "air force", "marine", "pentagon", "darpa"]):
        return "military"
    elif any(kw in name_lower for kw in ["health", "hhs", "nih", "cdc", "fda", "cms", "samhsa"]):
        return "health"
    elif any(kw in name_lower for kw in ["treasury", "irs", "finance", "federal reserve", "sec", "fdic"]):
        return "finance"
    elif any(kw in name_lower for kw in ["congress", "senate", "house of representatives", "gao", "cbo"]):
        return "legislative"
    elif any(kw in name_lower for kw in ["justice", "doj", "fbi", "atf", "dea", "marshals"]):
        return "justice"
    elif any(kw in name_lower for kw in ["homeland", "dhs", "tsa", "ice", "cbp", "fema", "secret service"]):
        return "shield"
    elif any(kw in name_lower for kw in ["energy", "doe", "nuclear", "nrc"]):
        return "energy"
    elif any(kw in name_lower for kw in ["nasa", "space"]):
        return "rocket"
    elif any(kw in name_lower for kw in ["agriculture", "usda", "farm"]):
        return "agriculture"
    elif any(kw in name_lower for kw in ["veteran", "va"]):
        return "veteran"
    elif any(kw in name_lower for kw in ["education", "ed"]):
        return "education"
    else:
        return "default"


# --- Endpoints ---

@router.post("/research", response_model=AgencyResearchResult)
async def research_agency(
    request: AgencyResearchRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Research a Federal Agency using Perplexity API.
    Returns structured data including Goals, Budget, Org Chart, LOB, etc.
    """
    try:
        result = await perplexity_service.research_agency(request.agency_name)
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/saved", response_model=List[SavedAgencySearchSummary])
async def list_saved_searches(db: AsyncSession = Depends(get_db)):
    """List all saved agency searches"""
    result = await db.execute(
        select(SavedAgencySearch).order_by(SavedAgencySearch.updated_at.desc())
    )
    return result.scalars().all()


@router.get("/saved/{search_id}", response_model=SavedAgencySearchDetail)
async def get_saved_search(search_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific saved search by ID"""
    result = await db.execute(
        select(SavedAgencySearch).where(SavedAgencySearch.id == search_id)
    )
    saved = result.scalar_one_or_none()
    if not saved:
        raise HTTPException(status_code=404, detail="Saved search not found")
    return saved


@router.post("/save/{agency_name}", response_model=SavedAgencySearchDetail)
async def save_agency_search(
    agency_name: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Save an agency research result for quick access.
    Performs fresh research and caches the result.
    """
    try:
        # Check if already saved
        result = await db.execute(
            select(SavedAgencySearch).where(SavedAgencySearch.agency_name == agency_name)
        )
        existing = result.scalar_one_or_none()
        
        # Perform fresh research
        research = await perplexity_service.research_agency(agency_name)
        
        icon_type = detect_icon_type(agency_name)
        
        if existing:
            # Update existing
            existing.acronym = research.acronym
            existing.icon_type = icon_type
            existing.overview = research.overview
            existing.strategic_goals = research.strategic_goals
            existing.budget_outlook = research.budget_outlook
            existing.org_structure = research.org_structure
            existing.org_tree = research.org_tree.model_dump() if research.org_tree else None
            existing.key_bureaus = research.key_bureaus
            existing.lines_of_business = [lob.model_dump() for lob in research.lines_of_business]
            existing.budget_by_division = [b.model_dump() for b in research.budget_by_division]
            existing.pain_points = research.pain_points
            existing.procurement_priorities = research.procurement_priorities
            existing.citations = [c.model_dump() for c in research.citations]
            existing.raw_response = research.raw_response
            existing.last_refreshed_at = datetime.utcnow()
            await db.commit()
            await db.refresh(existing)
            return existing
        else:
            # Create new
            saved = SavedAgencySearch(
                agency_name=research.agency_name,
                acronym=research.acronym,
                icon_type=icon_type,
                overview=research.overview,
                strategic_goals=research.strategic_goals,
                budget_outlook=research.budget_outlook,
                org_structure=research.org_structure,
                org_tree=research.org_tree.model_dump() if research.org_tree else None,
                key_bureaus=research.key_bureaus,
                lines_of_business=[lob.model_dump() for lob in research.lines_of_business],
                budget_by_division=[b.model_dump() for b in research.budget_by_division],
                pain_points=research.pain_points,
                procurement_priorities=research.procurement_priorities,
                citations=[c.model_dump() for c in research.citations],
                raw_response=research.raw_response,
                last_refreshed_at=datetime.utcnow()
            )
            db.add(saved)
            await db.commit()
            await db.refresh(saved)
            return saved
            
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/saved/{search_id}")
async def delete_saved_search(search_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a saved search"""
    result = await db.execute(
        select(SavedAgencySearch).where(SavedAgencySearch.id == search_id)
    )
    saved = result.scalar_one_or_none()
    if not saved:
        raise HTTPException(status_code=404, detail="Saved search not found")
    
    await db.delete(saved)
    await db.commit()
    return {"status": "deleted", "id": search_id}


@router.post("/saved/{search_id}/refresh", response_model=SavedAgencySearchDetail)
async def refresh_saved_search(search_id: int, db: AsyncSession = Depends(get_db)):
    """Refresh cached data for a saved agency"""
    result = await db.execute(
        select(SavedAgencySearch).where(SavedAgencySearch.id == search_id)
    )
    saved = result.scalar_one_or_none()
    if not saved:
        raise HTTPException(status_code=404, detail="Saved search not found")
    
    try:
        # Perform fresh research
        research = await perplexity_service.research_agency(saved.agency_name)
        
        # Update cached data
        saved.acronym = research.acronym
        saved.icon_type = detect_icon_type(saved.agency_name)
        saved.overview = research.overview
        saved.strategic_goals = research.strategic_goals
        saved.budget_outlook = research.budget_outlook
        saved.org_structure = research.org_structure
        saved.org_tree = research.org_tree.model_dump() if research.org_tree else None
        saved.key_bureaus = research.key_bureaus
        saved.lines_of_business = [lob.model_dump() for lob in research.lines_of_business]
        saved.budget_by_division = [b.model_dump() for b in research.budget_by_division]
        saved.pain_points = research.pain_points
        saved.procurement_priorities = research.procurement_priorities
        saved.citations = [c.model_dump() for c in research.citations]
        saved.raw_response = research.raw_response
        saved.last_refreshed_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(saved)
        return saved
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
