from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
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
    fuzzy: bool = Query(True, description="Enable fuzzy matching with multiple patterns"),
    min_similarity: float = Query(0.5, ge=0.0, le=1.0, description="Minimum similarity score (0.0-1.0)"),
    use_phonetic: bool = Query(True, description="Enable phonetic matching for sound-alike names"),
    use_abbreviations: bool = Query(True, description="Enable abbreviation expansion/contraction"),
    use_typos: bool = Query(True, description="Enable typo tolerance"),
    bypass_cache: bool = Query(False, description="Skip cache and fetch fresh results"),
    db: AsyncSession = Depends(get_db)
):
    """Search for entities on SAM.gov with advanced fuzzy matching and save them to DB"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        client = SamEntityClient()
        data = await client.search_entities(
            q,
            fuzzy=fuzzy,
            min_similarity=min_similarity,
            use_phonetic=use_phonetic,
            use_abbreviations=use_abbreviations,
            use_typos=use_typos,
            bypass_cache=bypass_cache
        )
        
        logger.info(f"SAM Search response type: {type(data)}")
        
        # SAM API V3 structure: {'entityData': [...], 'searchMetadata': {...}}
        entities_data = data.get("entityData", []) if isinstance(data, dict) else data
        search_metadata = data.get("searchMetadata", {}) if isinstance(data, dict) else {}
        
        if not isinstance(entities_data, list):
            entities_data = []
        
        if search_metadata:
            logger.info(f"Fuzzy search metadata: {search_metadata}")

        results = []
        for item in entities_data:
            if not isinstance(item, dict):
                logger.warning(f"Skipping non-dict item: {item}")
                continue
                
            # Extract fields
            # Structure: item['entityRegistration']['ueiSAM'], item['entityRegistration']['legalBusinessName']
            reg = item.get("entityRegistration", {})
            uei = reg.get("ueiSAM")
            name = reg.get("legalBusinessName")
            cage = reg.get("cageCode")
            
            # Extract fuzzy match metadata
            fuzzy_match = item.get("_fuzzy_match", {})
            similarity_score = fuzzy_match.get("similarity_score", 1.0)
            
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
                
                # Add similarity score to the entity object for frontend display
                # Note: This is not persisted to DB, just for the response
                existing.similarity_score = similarity_score
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
                
                # Add similarity score for response
                new_entity.similarity_score = similarity_score
                results.append(new_entity)
        
        await db.commit()
        # Refresh all to get IDs and timestamps
        for e in results:
            await db.refresh(e)
            
        # Sort by similarity score (highest first) if fuzzy search was used
        if fuzzy and hasattr(results[0] if results else None, 'similarity_score'):
            results.sort(key=lambda e: getattr(e, 'similarity_score', 0), reverse=True)
            
        return results
    except Exception as e:
        logger.error(f"Error in search_entities: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/partners", response_model=List[schemas.Entity])
async def get_partner_entities(
    db: AsyncSession = Depends(get_db)
):
    """Get all entities marked as partners for team building"""
    result = await db.execute(
        select(Entity)
        .where(Entity.entity_type == "PARTNER")
        .order_by(Entity.legal_business_name)
    )
    return result.scalars().all()

@router.get("/primary", response_model=schemas.Entity)
async def get_primary_entity(
    db: AsyncSession = Depends(get_db)
):
    """Get the primary entity (company profile entity)"""
    result = await db.execute(
        select(Entity).where(Entity.is_primary == True)
    )
    entity = result.scalars().first()
    if not entity:
        raise HTTPException(status_code=404, detail="No primary entity set. Please configure your company profile.")
    return entity


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
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    usaspending: USASpendingClient = Depends(USASpendingClient)
):
    """Fetch awards for an entity from USASpending.gov"""
    try:
        # 1. Get the entity name from the database
        result = await db.execute(select(Entity).where(Entity.uei == uei))
        entity = result.scalars().first()
        
        if not entity:
            print(f"Entity with UEI {uei} not found")
            return []
        
        # 2. Fetch from USASpending using entity name (not UEI)
        # Fetch Prime Awards
        prime_awards = await usaspending.get_awards_by_name(entity.legal_business_name, limit=limit)
        
        # Fetch Sub-Awards
        sub_awards = await usaspending.get_subawards_by_name(entity.legal_business_name, limit=limit)
        
        all_awards = []
        
        # Process Prime Awards
        for award in prime_awards:
            award_id = award.get("Award ID")
            if not award_id:
                continue
            
            # Normalize for response
            award["award_type"] = "Prime"
            all_awards.append(award)
                
            # Check if exists
            result = await db.execute(select(EntityAward).where(EntityAward.award_id == award_id))
            if not result.scalars().first():
                db_award = EntityAward(
                    award_id=award_id,
                    recipient_uei=uei,
                    total_obligation=award.get("Award Amount"),
                    description=award.get("Description"),
                    award_date=datetime.strptime(award.get("Start Date"), "%Y-%m-%d").date() if award.get("Start Date") else None,
                    awarding_agency=award.get("Awarding Agency"),
                    naics_code=award.get("NAICS Code"),
                    solicitation_id=award.get("Solicitation ID"),
                    award_type="Prime"
                )
                db.add(db_award)

        # Process Sub-Awards
        for award in sub_awards:
            sub_id = award.get("Sub-Award ID")
            if not sub_id:
                continue
                
            # Normalize keys to match Prime Award structure for frontend
            normalized_award = {
                "Award ID": sub_id,
                "Recipient Name": award.get("Sub-Awardee Name"),
                "Award Amount": award.get("Sub-Award Amount"),
                "Description": award.get("Sub-Award Description"),
                "Start Date": award.get("Sub-Award Date"),
                "Awarding Agency": award.get("Awarding Agency"),
                "Prime Award ID": award.get("Prime Award ID"),
                "Prime Recipient Name": award.get("Prime Recipient Name"),
                "award_type": "Sub"
            }
            all_awards.append(normalized_award)
            
            # Check if exists
            # Note: Sub-Award IDs might clash with Prime IDs? Unlikely but possible.
            # Usually Sub-Award IDs are distinct.
            result = await db.execute(select(EntityAward).where(EntityAward.award_id == sub_id))
            if not result.scalars().first():
                db_award = EntityAward(
                    award_id=sub_id,
                    recipient_uei=uei,
                    total_obligation=award.get("Sub-Award Amount"),
                    description=award.get("Sub-Award Description"),
                    award_date=datetime.strptime(award.get("Sub-Award Date"), "%Y-%m-%d").date() if award.get("Sub-Award Date") else None,
                    awarding_agency=award.get("Awarding Agency"),
                    award_type="Sub"
                )
                db.add(db_award)
        
        await db.commit()
        
        # Return the merged data
        return all_awards
    except Exception as e:
        print(f"Error in get_entity_awards: {e}")
        import traceback
        traceback.print_exc()
        return []

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

@router.post("/{uei}/logo")
async def upload_entity_logo(
    uei: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """Upload a logo for the entity"""
    import shutil
    import os
    from pathlib import Path
    
    # Verify entity exists
    result = await db.execute(select(Entity).where(Entity.uei == uei))
    entity = result.scalars().first()
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    
    # Create static/logos directory if not exists
    # Assuming app root is where main.py is, or relative to this file
    # Let's use a fixed path relative to the project root for now
    # We need to find the project root.
    # fedops/fedops_api/routers/entities.py -> fedops/
    
    base_path = Path(__file__).resolve().parent.parent.parent
    static_dir = base_path / "static" / "logos"
    static_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate filename
    file_ext = os.path.splitext(file.filename)[1]
    filename = f"{uei}_logo{file_ext}"
    file_path = static_dir / filename
    
    # Save file
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
        
    # Update entity logo_url
    # We'll store the relative path for serving
    logo_url = f"/static/logos/{filename}"
    entity.logo_url = logo_url
    
    await db.commit()
    await db.refresh(entity)
    
    return {"logo_url": logo_url}


@router.get("/primary", response_model=Optional[schemas.Entity])
async def get_primary_entity(db: AsyncSession = Depends(get_db)):
    """Get the current primary entity"""
    result = await db.execute(select(Entity).where(Entity.is_primary == True))
    return result.scalars().first()

    return matches

@router.get("/{uei}/contract-documents")
async def get_contract_documents(
    uei: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve SOW/PWS documents for an entity's awards.
    1. Get awards with solicitation IDs.
    2. Fetch opportunity details from SAM.gov.
    3. Extract resource links (documents).
    """
    from fedops_sources.sam_opportunities.client import SamOpportunitiesClient
    from sqlalchemy import desc
    import httpx
    import urllib.parse
    import re
    import logging
    
    logger = logging.getLogger(__name__)
    
    # 1. Get awards for this entity that have a solicitation ID
    # We limit to recent or significant awards to avoid too many API calls
    stmt = (
        select(EntityAward)
        .where(EntityAward.recipient_uei == uei)
        .where(EntityAward.solicitation_id.isnot(None))
        .order_by(desc(EntityAward.total_obligation))
        .limit(20) # Limit to top 20 awards
    )
    result = await db.execute(stmt)
    awards = result.scalars().all()
    
    sam_client = SamOpportunitiesClient()
    documents = []
    
    for award in awards:
        if not award.solicitation_id:
            continue
            
        try:
            # Fetch opportunity from SAM.gov
            opp = await sam_client.get_opportunity_by_solicitation_id(award.solicitation_id)
            
            if not opp:
                logger.warning(f"No opportunity found for solicitation ID: {award.solicitation_id}")
                continue
                
            # Extract resource links from the opportunity
            resource_links = opp.get("resourceLinks", [])
            
            if not resource_links:
                logger.info(f"No resource links found for solicitation ID: {award.solicitation_id}")
                continue
            
            # Process each resource link to resolve filename
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=False) as client:
                for link in resource_links:
                    try:
                        # Default filename from URL
                        filename = link.split("/")[-1] if isinstance(link, str) else "document"
                        url = link if isinstance(link, str) else link.get("url", link.get("href", ""))
                        
                        if not url:
                            continue
                        
                        # Try to get real filename from headers (same logic as opportunities endpoint)
                        try:
                            response = await client.head(url)
                            
                            # Check for redirect with filename in query params (common for SAM.gov)
                            if response.status_code in (301, 302, 303, 307, 308):
                                location = response.headers.get("location")
                                if location:
                                    parsed = urllib.parse.urlparse(location)
                                    params = urllib.parse.parse_qs(parsed.query)
                                    content_disposition = params.get('response-content-disposition', [None])[0]
                                    if content_disposition:
                                        # Look for filename="name"
                                        match = re.search(r'filename="?([^"]+)"?', content_disposition)
                                        if match:
                                            filename = match.group(1)
                                        else:
                                            # Try filename*=
                                            match = re.search(r"filename\*=UTF-8''(.+)", content_disposition)
                                            if match:
                                                filename = urllib.parse.unquote(match.group(1))
                            
                            # If not a redirect, check Content-Disposition header directly
                            elif response.status_code == 200:
                                content_disposition = response.headers.get("content-disposition")
                                if content_disposition:
                                    match = re.search(r'filename="?([^"]+)"?', content_disposition)
                                    if match:
                                        filename = match.group(1)
                                    else:
                                        match = re.search(r"filename\*=UTF-8''(.+)", content_disposition)
                                        if match:
                                            filename = urllib.parse.unquote(match.group(1))
                        except Exception as e:
                            logger.warning(f"Error resolving filename for {url}: {e}")
                        
                        # Clean up filename (replace + with space)
                        if filename:
                            filename = filename.replace("+", " ")
                        
                        # Determine document type based on filename
                        doc_type = "Other"
                        filename_lower = filename.lower()
                        if any(keyword in filename_lower for keyword in ["sow", "statement of work", "statement_of_work"]):
                            doc_type = "SOW"
                        elif any(keyword in filename_lower for keyword in ["pws", "performance work statement", "performance_work_statement"]):
                            doc_type = "PWS"
                        elif any(keyword in filename_lower for keyword in ["rfp", "request for proposal"]):
                            doc_type = "RFP"
                        elif any(keyword in filename_lower for keyword in ["amendment", "modification"]):
                            doc_type = "Amendment"
                        
                        documents.append({
                            "award_id": award.award_id,
                            "solicitation_id": award.solicitation_id,
                            "opportunity_title": opp.get("title"),
                            "document_url": url,
                            "document_filename": filename,
                            "document_type": doc_type,
                            "award_description": award.description,
                            "award_amount": award.total_obligation
                        })
                    except Exception as e:
                        logger.error(f"Error processing resource link {link}: {e}")
                        continue
        except Exception as e:
            logger.error(f"Error fetching documents for solicitation {award.solicitation_id}: {e}")
            continue
            
    return documents

@router.get("/{uei}/profile", response_model=schemas.Entity)
async def get_entity_profile(
    uei: str,
    db: AsyncSession = Depends(get_db)
):
    """Get comprehensive entity profile including partner search details"""
    from fedops_core.services.partner_service import PartnerService
    service = PartnerService(db)
    entity = await service.get_entity_profile(uei)
    
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
        
    return entity

@router.post("/{uei}/refresh", response_model=schemas.Entity)
async def refresh_entity_data(
    uei: str,
    db: AsyncSession = Depends(get_db)
):
    """Refresh entity data from SAM.gov and re-extract details"""
    # 1. Fetch fresh data from SAM
    client = SamEntityClient()
    data = await client.get_entity(uei)
    
    if not data:
        raise HTTPException(status_code=404, detail="Entity not found in SAM.gov")
        
    # 2. Update entity in DB
    result = await db.execute(select(Entity).where(Entity.uei == uei))
    entity = result.scalars().first()
    
    if not entity:
        # Should create if not exists? Maybe. For now assume it exists or use save logic.
        # Let's create if not exists to be safe
        reg = data.get("entityRegistration", {}) if "entityRegistration" in data else data.get("entityData", [{}])[0].get("entityRegistration", {})
        entity = Entity(
            uei=uei,
            legal_business_name=reg.get("legalBusinessName", "Unknown"),
            cage_code=reg.get("cageCode"),
            full_response=data,
            last_synced_at=datetime.utcnow()
        )
        db.add(entity)
    else:
        entity.full_response = data
        entity.last_synced_at = datetime.utcnow()
        
    await db.commit()
    
    # 3. Extract details using PartnerService
    from fedops_core.services.partner_service import PartnerService
    service = PartnerService(db)
    await service.update_entity_from_sam(entity)
    
    return entity
