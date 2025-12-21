"""
Entities Router - Appwrite Version

API endpoints for entity management using Appwrite database.
"""

from fastapi import APIRouter, HTTPException, Query
import pydantic
from typing import Optional, List
import logging

from fedops_core.services.entities_repository import EntitiesRepository
from fedops_core.services.additional_repositories import EntityAwardsRepository
from appwrite.query import Query as AppwriteQuery

router = APIRouter()
logger = logging.getLogger(__name__)


class EntityCreate(pydantic.BaseModel):
    uei: str
    legal_business_name: str
    cage_code: Optional[str] = None
    entity_type: str = "OTHER"
    notes: Optional[str] = None
    logo_url: Optional[str] = None
    revenue: Optional[float] = None
    personnel_count: Optional[int] = None


class EntityUpdate(pydantic.BaseModel):
    legal_business_name: Optional[str] = None
    cage_code: Optional[str] = None
    entity_type: Optional[str] = None
    notes: Optional[str] = None
    logo_url: Optional[str] = None
    revenue: Optional[float] = None
    personnel_count: Optional[int] = None


@router.get("/")
async def list_entities(
    skip: int = 0,
    limit: int = 25,
    entity_type: Optional[str] = Query(None, description="Filter by entity type")
):
    """List all entities with optional filtering."""
    repo = EntitiesRepository()
    
    queries = []
    if entity_type:
        queries.append(AppwriteQuery.equal("entity_type", entity_type))
    
    queries.append(AppwriteQuery.order_desc("created_at"))
    
    try:
        result = await repo.list(queries=queries, limit=limit, offset=skip)
        return {
            "items": result.get("documents", []),
            "total": result.get("total", 0)
        }
    except Exception as e:
        logger.error(f"Error listing entities: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/primary")
async def get_primary_entity():
    """Get the currently active primary entity."""
    repo = EntitiesRepository()
    
    entity = await repo.get_primary_entity()
    if not entity:
        raise HTTPException(status_code=404, detail="No primary entity set")
    return entity


@router.post("/primary/{uei}")
async def set_primary_entity(uei: str):
    """Set an entity as the primary entity."""
    repo = EntitiesRepository()
    
    try:
        entity = await repo.set_primary_entity(uei)
        return {
            "message": "Primary entity updated",
            "entity": entity
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error setting primary entity: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search")
async def search_entities(
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = 10
):
    """Search entities by name."""
    repo = EntitiesRepository()
    
    try:
        result = await repo.search_by_name(q, limit)
        return result.get("documents", [])
    except Exception as e:
        logger.error(f"Error searching entities: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/partners")
async def get_partners(limit: int = 25):
    """Get all partner entities."""
    repo = EntitiesRepository()
    result = await repo.get_partners(limit)
    return result.get("documents", [])


@router.get("/competitors")
async def get_competitors(limit: int = 25):
    """Get all competitor entities."""
    repo = EntitiesRepository()
    result = await repo.get_competitors(limit)
    return result.get("documents", [])


@router.get("/uei/{uei}")
async def get_entity_by_uei(uei: str):
    """Get an entity by UEI."""
    repo = EntitiesRepository()
    
    entity = await repo.get_by_uei(uei)
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    return entity


@router.get("/{id}")
async def get_entity(id: str):
    """Get an entity by document ID."""
    repo = EntitiesRepository()
    
    entity = await repo.get(id)
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    return entity


@router.post("/")
async def create_entity(entity: EntityCreate):
    """Create a new entity."""
    repo = EntitiesRepository()
    
    # Check if UEI already exists
    existing = await repo.get_by_uei(entity.uei)
    if existing:
        raise HTTPException(status_code=409, detail="Entity with this UEI already exists")
    
    try:
        new_entity = await repo.create(entity.dict())
        return new_entity
    except Exception as e:
        logger.error(f"Error creating entity: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{id}")
async def update_entity(id: str, entity: EntityUpdate):
    """Update an entity."""
    repo = EntitiesRepository()
    
    existing = await repo.get(id)
    if not existing:
        raise HTTPException(status_code=404, detail="Entity not found")
    
    try:
        # Filter out None values
        update_data = {k: v for k, v in entity.dict().items() if v is not None}
        updated = await repo.update(id, update_data)
        return updated
    except Exception as e:
        logger.error(f"Error updating entity: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{id}")
async def delete_entity(id: str):
    """Delete an entity."""
    repo = EntitiesRepository()
    
    existing = await repo.get(id)
    if not existing:
        raise HTTPException(status_code=404, detail="Entity not found")
    
    # Check if this is the primary entity
    if existing.get("is_primary"):
        raise HTTPException(
            status_code=400, 
            detail="Cannot delete primary entity. Set another entity as primary first."
        )
    
    try:
        await repo.delete(id)
        return {"ok": True, "message": "Entity deleted"}
    except Exception as e:
        logger.error(f"Error deleting entity: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Entity Awards
# =============================================================================

@router.get("/{id}/awards")
async def get_entity_awards(id: str, limit: int = 100):
    """Get awards for an entity."""
    entities_repo = EntitiesRepository()
    awards_repo = EntityAwardsRepository()
    
    entity = await entities_repo.get(id)
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    
    uei = entity.get("uei")
    result = await awards_repo.get_by_uei(uei, limit)
    return result.get("documents", [])


class AwardCreate(pydantic.BaseModel):
    award_id: str
    total_obligation: Optional[float] = None
    description: Optional[str] = None
    award_date: Optional[str] = None
    awarding_agency: Optional[str] = None
    naics_code: Optional[str] = None
    solicitation_id: Optional[str] = None
    award_type: str = "Prime"


@router.post("/{id}/awards")
async def add_entity_award(id: str, award: AwardCreate):
    """Add an award to an entity."""
    entities_repo = EntitiesRepository()
    awards_repo = EntityAwardsRepository()
    
    entity = await entities_repo.get(id)
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    
    uei = entity.get("uei")
    
    # Check if award already exists
    existing = await awards_repo.get_by_award_id(award.award_id)
    if existing:
        raise HTTPException(status_code=409, detail="Award already exists")
    
    try:
        award_data = award.dict()
        award_data["recipient_uei"] = uei
        new_award = await awards_repo.create(award_data)
        return new_award
    except Exception as e:
        logger.error(f"Error adding award: {e}")
        raise HTTPException(status_code=500, detail=str(e))
