"""
API Router for Competitive Intelligence
Handles USAspending data integration and competitor analysis
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from fedops_core.db.engine import get_db
from fedops_core.services.competitive_analytics_service import CompetitiveAnalyticsService
from fedops_core.db.shipley_models import CompetitiveIntelligence
from sqlalchemy import select


router = APIRouter(
    prefix="/competitive_intel",
    tags=["competitive_intel"]
)


@router.get("/opportunities/{opportunity_id}/competitors")
async def get_competitors(
    opportunity_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get competitive intelligence for an opportunity
    Returns stored competitor data from database
    """
    try:
        result = await db.execute(
            select(CompetitiveIntelligence).where(
                CompetitiveIntelligence.opportunity_id == opportunity_id
            ).order_by(CompetitiveIntelligence.total_obligation.desc())
        )
        competitors = result.scalars().all()
        
        return [
            {
                "id": c.id,
                "competitor_name": c.competitor_name,
                "competitor_uei": c.competitor_uei,
                "historical_wins": c.historical_wins,
                "total_obligation": c.total_obligation,
                "win_probability_impact": c.win_probability_impact,
                "is_incumbent": c.is_incumbent,
                "data_source": c.data_source,
                "naics_match": c.naics_match,
                "agency_match": c.agency_match,
                "created_at": c.created_at.isoformat() if c.created_at else None
            }
            for c in competitors
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/opportunities/{opportunity_id}/refresh")
async def refresh_competitive_intel(
    opportunity_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Refresh competitive intelligence from USAspending
    Fetches latest data and updates database
    """
    try:
        result = await CompetitiveAnalyticsService.update_competitive_intelligence(
            db=db,
            opportunity_id=opportunity_id
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/opportunities/{opportunity_id}/win_probability")
async def get_win_probability(
    opportunity_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Calculate win probability based on competitive intelligence
    """
    try:
        win_prob = await CompetitiveAnalyticsService.calculate_win_probability(
            db=db,
            opportunity_id=opportunity_id
        )
        return {
            "opportunity_id": opportunity_id,
            "win_probability": win_prob
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/competitors/{competitor_uei}/profile")
async def get_competitor_profile(
    competitor_uei: str,
    naics_code: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed profile for a specific competitor
    """
    try:
        profile = await CompetitiveAnalyticsService.profile_competitor(
            db=db,
            competitor_uei=competitor_uei,
            naics_code=naics_code
        )
        return profile
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/opportunities/{opportunity_id}/identify_competitors")
async def identify_competitors(
    opportunity_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Identify competitors from USAspending without storing
    Useful for preview before committing to database
    """
    try:
        competitors = await CompetitiveAnalyticsService.identify_competitors(
            db=db,
            opportunity_id=opportunity_id
        )
        return {
            "opportunity_id": opportunity_id,
            "competitors_found": len(competitors),
            "competitors": competitors[:10]  # Return top 10
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
