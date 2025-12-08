"""
API Router for Competitive Intelligence
Handles USAspending data integration, competitor analysis, and Perplexity research
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime, timedelta

from fedops_core.db.engine import get_db
from fedops_core.services.competitive_analytics_service import CompetitiveAnalyticsService
from fedops_core.services.perplexity_service import perplexity_service
from fedops_core.db.shipley_models import CompetitiveIntelligence, PerplexityCompetitorAnalysis
from fedops_core.schemas.competitive_analysis_schemas import (
    CompetitiveAnalysisRequest,
    CompetitiveAnalysisResult,
    CompetitiveAnalysisDB
)
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


@router.get("/competitors/{competitor_uei}/entity_details")
async def get_entity_details(
    competitor_uei: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed SAM.gov entity data for a specific competitor
    Returns comprehensive entity information including NAICS codes and business types
    """
    try:
        entity_data = await CompetitiveAnalyticsService.fetch_entity_data(competitor_uei)
        
        if not entity_data:
            raise HTTPException(status_code=404, detail=f"Entity data not found for UEI {competitor_uei}")
        
        return entity_data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Perplexity-Powered Competitive Analysis Endpoints
# ============================================================================

@router.post("/competitors/{entity_name}/research")
async def research_competitor(
    entity_name: str,
    request: CompetitiveAnalysisRequest = CompetitiveAnalysisRequest(),
    db: AsyncSession = Depends(get_db)
):
    """
    Research a competitor using Perplexity API.
    
    Performs web research on the entity and returns a structured competitive
    analysis with strengths, weaknesses, strategies to beat them, and citations.
    
    Results are cached in the database for 7 days unless force_refresh is True.
    """
    try:
        # Check for cached analysis (unless force refresh)
        if not request.force_refresh:
            cache_cutoff = datetime.utcnow() - timedelta(days=7)
            stmt = select(PerplexityCompetitorAnalysis).where(
                PerplexityCompetitorAnalysis.entity_name == entity_name,
                PerplexityCompetitorAnalysis.created_at > cache_cutoff
            ).order_by(PerplexityCompetitorAnalysis.created_at.desc())
            
            result = await db.execute(stmt)
            cached = result.scalar_one_or_none()
            
            if cached:
                return {
                    "source": "cache",
                    "analysis": {
                        "id": cached.id,
                        "entity_name": cached.entity_name,
                        "entity_uei": cached.entity_uei,
                        "overview": cached.overview,
                        "market_position": cached.market_position,
                        "strengths": cached.strengths or [],
                        "weaknesses": cached.weaknesses or [],
                        "key_differentiators": cached.key_differentiators or [],
                        "how_to_beat_them": cached.strategies_to_beat or [],
                        "citations": cached.citations or [],
                        "analyzed_at": cached.created_at.isoformat() if cached.created_at else None,
                        "model_used": cached.model_used
                    }
                }
        
        # Perform fresh research
        analysis = await perplexity_service.research_entity(
            entity_name=entity_name,
            context=request.context
        )
        
        # Store in database
        db_analysis = PerplexityCompetitorAnalysis(
            entity_name=entity_name,
            opportunity_id=request.opportunity_id,
            overview=analysis.overview,
            market_position=analysis.market_position,
            strengths=[s.model_dump() for s in analysis.strengths],
            weaknesses=[w.model_dump() for w in analysis.weaknesses],
            key_differentiators=analysis.key_differentiators,
            strategies_to_beat=[s.model_dump() for s in analysis.how_to_beat_them],
            citations=[c.model_dump() for c in analysis.citations],
            raw_response=analysis.raw_response,
            model_used=perplexity_service.DEFAULT_MODEL
        )
        db.add(db_analysis)
        await db.commit()
        await db.refresh(db_analysis)
        
        return {
            "source": "fresh",
            "analysis": {
                "id": db_analysis.id,
                "entity_name": analysis.entity_name,
                "entity_uei": analysis.entity_uei,
                "overview": analysis.overview,
                "market_position": analysis.market_position,
                "strengths": [s.model_dump() for s in analysis.strengths],
                "weaknesses": [w.model_dump() for w in analysis.weaknesses],
                "key_differentiators": analysis.key_differentiators,
                "how_to_beat_them": [s.model_dump() for s in analysis.how_to_beat_them],
                "citations": [c.model_dump() for c in analysis.citations],
                "analyzed_at": analysis.analyzed_at.isoformat(),
                "model_used": perplexity_service.DEFAULT_MODEL
            }
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/competitors/{entity_uei}/perplexity-analysis")
async def get_perplexity_analysis(
    entity_uei: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get stored Perplexity analysis for an entity by UEI.
    Returns the most recent analysis if available.
    """
    try:
        stmt = select(PerplexityCompetitorAnalysis).where(
            PerplexityCompetitorAnalysis.entity_uei == entity_uei
        ).order_by(PerplexityCompetitorAnalysis.created_at.desc())
        
        result = await db.execute(stmt)
        analysis = result.scalar_one_or_none()
        
        if not analysis:
            raise HTTPException(
                status_code=404, 
                detail=f"No Perplexity analysis found for UEI {entity_uei}"
            )
        
        return {
            "id": analysis.id,
            "entity_name": analysis.entity_name,
            "entity_uei": analysis.entity_uei,
            "overview": analysis.overview,
            "market_position": analysis.market_position,
            "strengths": analysis.strengths or [],
            "weaknesses": analysis.weaknesses or [],
            "key_differentiators": analysis.key_differentiators or [],
            "how_to_beat_them": analysis.strategies_to_beat or [],
            "citations": analysis.citations or [],
            "analyzed_at": analysis.created_at.isoformat() if analysis.created_at else None,
            "model_used": analysis.model_used
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/competitors/analyses/recent")
async def get_recent_analyses(
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """
    Get recently performed competitive analyses.
    Useful for viewing analysis history.
    """
    try:
        stmt = select(PerplexityCompetitorAnalysis).order_by(
            PerplexityCompetitorAnalysis.created_at.desc()
        ).limit(limit)
        
        result = await db.execute(stmt)
        analyses = result.scalars().all()
        
        return [
            {
                "id": a.id,
                "entity_name": a.entity_name,
                "entity_uei": a.entity_uei,
                "overview": a.overview[:200] + "..." if a.overview and len(a.overview) > 200 else a.overview,
                "citation_count": len(a.citations) if a.citations else 0,
                "analyzed_at": a.created_at.isoformat() if a.created_at else None
            }
            for a in analyses
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
