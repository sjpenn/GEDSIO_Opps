from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Any

from fedops_core.db.engine import get_db
from fedops_core.db.models import Entity, EntityAward
from fedops_core.schemas import company as schemas
from fedops_sources.sam_entity import SamEntityClient
from fedops_sources.usaspending import USASpendingClient

router = APIRouter()

from datetime import datetime

def get_sam_client():
    return SamEntityClient()

@router.get("/search", response_model=List[schemas.Entity])
async def search_entities(
    q: str = Query(..., min_length=3, description="Legal Business Name to search"),
    db: AsyncSession = Depends(get_db)
):
    """Search for entities on SAM.gov and save them to DB"""
    client = SamEntityClient()
    data = await client.search_entities(q)
    
    # SAM API V3 structure: {'entityData': [...]}
    entities_data = data.get("entityData", []) if isinstance(data, dict) else data
    if not isinstance(entities_data, list):
        entities_data = []

    results = []
    for item in entities_data:
        # Extract fields
        # Structure: item['entityRegistration']['ueiSAM'], item['entityRegistration']['legalBusinessName']
        reg = item.get("entityRegistration", {})
        uei = reg.get("ueiSAM")
        name = reg.get("legalBusinessName")
        cage = reg.get("cageCode")
        
        if not uei or not name:
            continue
            
        # Upsert
        result = await db.execute(select(Entity).where(Entity.uei == uei))
        existing = result.scalars().first()
        
        if existing:
            existing.legal_business_name = name
            existing.cage_code = cage
            existing.full_response = item
            existing.last_synced_at = datetime.utcnow()
            # Don't overwrite entity_type or notes if they exist
            results.append(existing)
        else:
            new_entity = Entity(
                uei=uei,
                legal_business_name=name,
                cage_code=cage,
                full_response=item,
                entity_type="OTHER",
                last_synced_at=datetime.utcnow()
            )
            db.add(new_entity)
            results.append(new_entity)
    
    await db.commit()
    # Refresh all to get IDs and timestamps
    for e in results:
        await db.refresh(e)
        
    return results

@router.post("/", response_model=schemas.Entity)
async def save_entity(
    entity: schemas.EntityCreate, 
    db: AsyncSession = Depends(get_db)
):
    """Save an entity to the local database (e.g. as Partner or Competitor)"""
    result = await db.execute(select(Entity).where(Entity.uei == entity.uei))
    existing = result.scalars().first()
    if existing:
        # Update existing
        for key, value in entity.model_dump().items():
            setattr(existing, key, value)
        await db.commit()
        await db.refresh(existing)
        return existing

    db_entity = Entity(**entity.model_dump())
    db.add(db_entity)
    await db.commit()
    await db.refresh(db_entity)
    return db_entity

@router.get("/{uei}/awards")
async def get_entity_awards(
    uei: str, 
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
    usaspending: USASpendingClient = Depends(USASpendingClient)
):
    """Fetch awards for an entity from USASpending.gov"""
    # 1. Try to fetch from USASpending
    awards_data = await usaspending.get_awards_by_uei(uei, limit=limit)
    
    # 2. Cache/Update in DB (Simplified logic: just insert new ones)
    # In a real app, we'd handle updates and duplicates more carefully
    for award in awards_data:
        # Map USASpending fields to our model
        # Note: USASpending field names might need adjustment based on actual API response
        award_id = award.get("Award ID")
        if not award_id:
            continue
            
        # Check if exists
        result = await db.execute(select(EntityAward).where(EntityAward.award_id == award_id))
        if not result.scalars().first():
            db_award = EntityAward(
                award_id=award_id,
                recipient_uei=uei,
                total_obligation=award.get("Award Amount"),
                description=award.get("Description"),
                award_date=None, # Parse date if needed
                awarding_agency=award.get("Awarding Agency")
            )
            db.add(db_award)
    
    await db.commit()
    
    # Return the data directly from API for freshness, or query DB
    return awards_data
