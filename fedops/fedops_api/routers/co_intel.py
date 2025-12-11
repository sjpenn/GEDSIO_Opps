"""
API Router for Contracting Officer (CO) Intelligence
Handles requests for CO research using Perplexity and Award searches via USAspending
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import List, Optional

from fedops_core.db.engine import get_db
from fedops_core.services.perplexity_service import perplexity_service
from fedops_core.schemas.competitive_analysis_schemas import COResearchResult
from fedops_core.services.co_extraction_service import search_cos_local, backfill_cos_from_opportunities
from fedops_sources.usaspending import USASpendingClient

router = APIRouter(
    prefix="/co_intel",
    tags=["co_intel"]
)

class COResearchRequest(BaseModel):
    co_name: str
    agency: Optional[str] = None

@router.post("/research", response_model=COResearchResult)
async def research_co(
    request: COResearchRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Research a Contracting Officer using Perplexity API.
    Returns structured data including Bio, Career History, Awarding Preferences.
    """
    try:
        result = await perplexity_service.research_co(request.co_name, request.agency)
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/awards")
async def get_co_awards(
    q: str = Query(..., description="Name of the Contracting Officer to search for in awards"),
    limit: int = 50,
    usaspending: USASpendingClient = Depends(USASpendingClient)
):
    """
    Search USAspending for awards associated with a Contracting Officer.
    Note: Uses keyword search as USAspending API does not have a direct CO filter.
    Results may need client-side filtering or interpretation.
    """
    try:
        # We search by keyword which searches across description and other text fields.
        # This is the best approximation available without a direct CO field in the API.
        awards = await usaspending.search_awards_by_keyword(q, limit=limit)
        return awards
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search")
async def search_co(
    q: str = Query(..., description="Name or query to find contracting professionals"),
    db: AsyncSession = Depends(get_db)
):
    """
    Search for Contracting Officers/Specialists by name across agencies.
    Returns list of potential matches with verification details.
    """
    try:
        result = await perplexity_service.research_contracting_professionals(q)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/directory")
async def search_co_directory(
    q: str = Query(..., description="Name, email, or agency to search for COs"),
    limit: int = Query(20, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    Search contracting officers in local database (extracted from SAM.gov opportunities).
    Faster than Perplexity search - uses local fuzzy matching.
    """
    try:
        cos = await search_cos_local(db, q, limit)
        return {
            "query": q,
            "count": len(cos),
            "results": [
                {
                    "id": co.id,
                    "name": co.name,
                    "email": co.email,
                    "phone": co.phone,
                    "title": co.title,
                    "agency": co.agency,
                    "sub_agency": co.sub_agency,
                    "office": co.office,
                    "opportunity_count": co.opportunity_count,
                    "first_seen": co.first_seen_at.isoformat() if co.first_seen_at else None,
                    "last_seen": co.last_seen_at.isoformat() if co.last_seen_at else None
                }
                for co in cos
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/backfill")
async def backfill_cos(db: AsyncSession = Depends(get_db)):
    """
    Backfill contracting_officers table from existing opportunities.
    Extracts CO data from point_of_contact fields.
    """
    try:
        count = await backfill_cos_from_opportunities(db)
        return {"message": f"Backfilled {count} contracting officers from existing opportunities"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
