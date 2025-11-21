from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from fedops_api.deps import get_db
from fedops_sources.sam_opportunities.adapter import SAMOpportunitiesConnector
from fedops_core.db.models import Opportunity
from datetime import datetime

router = APIRouter()

@router.post("/sam/opportunities/run")
async def run_sam_ingest(
    api_key: str = None, 
    limit: int = 10, 
    db: AsyncSession = Depends(get_db)
):
    connector = SAMOpportunitiesConnector()
    count = 0
    async for record in connector.pull({"api_key": api_key, "limit": limit}):
        # Simple mapper to DB model
        opp = Opportunity(
            solicitation_number=record.get("solicitation_number"),
            title=record.get("title"),
            posted_at=datetime.fromisoformat(record.get("posted_at").replace("Z", "+00:00")),
            type=record.get("type"),
            base_type=record.get("base_type"),
            set_aside_code=record.get("set_aside_code"),
            naics=record.get("naics"),
            # ... map other fields ...
        )
        db.add(opp)
        count += 1
    
    await db.commit()
    return {"status": "success", "ingested_count": count}

@router.post("/usaspending/awards/run")
async def run_usaspending_ingest():
    return {"status": "not_implemented_yet"}
