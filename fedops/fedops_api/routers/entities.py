from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Any, Optional

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
                awarding_agency=award.get("Awarding Agency"),
                naics_code=award.get("NAICS Code")
            )
            db.add(db_award)
    
    await db.commit()
    
    # Return the data directly from API for freshness, or query DB
    return awards_data

@router.put("/{uei}/primary", response_model=schemas.Entity)
async def set_primary_entity(
    uei: str,
    is_primary: bool = True,
    db: AsyncSession = Depends(get_db)
):
    """Set an entity as the primary entity. If is_primary is True, unsets others."""
    # 1. Find the entity
    result = await db.execute(select(Entity).where(Entity.uei == uei))
    entity = result.scalars().first()
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    
    # 2. If setting to True, unset others
    if is_primary:
        # Unset all others. Note: This requires 'update' import or raw SQL, or iterating.
        # Using iteration for simplicity with AsyncSession if update() is tricky with async
        # But update() is better. Let's try to use update()
        from sqlalchemy import update
        await db.execute(
            update(Entity).where(Entity.uei != uei).values(is_primary=False)
        )
    
    # 3. Update this entity
    entity.is_primary = is_primary
    await db.commit()
    await db.refresh(entity)
    return entity

@router.get("/primary", response_model=Optional[schemas.Entity])
async def get_primary_entity(db: AsyncSession = Depends(get_db)):
    """Get the current primary entity"""
    result = await db.execute(select(Entity).where(Entity.is_primary == True))
    return result.scalars().first()

@router.post("/match-opportunity", response_model=List[dict])
async def match_partners_to_opportunity(
    opportunity_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Find partners that match an opportunity based on NAICS code and past performance.
    """
    from fedops_core.db.models import Opportunity
    from sqlalchemy import func, desc
    
    # 1. Get Opportunity
    result = await db.execute(select(Opportunity).where(Opportunity.id == opportunity_id))
    opp = result.scalars().first()
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    
    # 2. Get NAICS
    naics = opp.naics_code
    if not naics:
        # Fallback: Try to match by keywords? For now just return empty.
        return [] 
    
    # 3. Find Entities that have awards with this NAICS
    # We prioritize entities marked as PARTNER, but search all.
    
    stmt = (
        select(Entity, func.sum(EntityAward.total_obligation).label("total_obligation"), func.count(EntityAward.award_id).label("award_count"))
        .join(EntityAward, Entity.uei == EntityAward.recipient_uei)
        .where(EntityAward.naics_code == naics)
        .group_by(Entity.uei)
        .order_by(desc("total_obligation"))
    )
    
    results = await db.execute(stmt)
    matches = []
    for row in results:
        entity = row[0]
        total_ob = row[1] or 0
        count = row[2] or 0
        
        # Serialize entity using Pydantic model
        entity_data = schemas.Entity.model_validate(entity).model_dump()
        
        matches.append({
            "entity": entity_data,
            "match_score": total_ob, 
            "match_details": {
                "total_obligation": total_ob,
                "award_count": count,
                "reason": f"Has {count} awards in NAICS {naics}"
            }
        })
        
    return matches
