from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional
import os
import shutil
from pathlib import Path

from fedops_core.db.engine import get_db
from fedops_core.db.models import CompanyProfile, CompanyProfileDocument, CompanyProfileLink, Entity
from fedops_core.schemas import company as schemas
from fedops_sources.sam_entity import SamEntityClient
from fedops_core.services.entity_enrichment_service import entity_enrichment_service

router = APIRouter()

# Directory for storing company profile documents
UPLOAD_DIR = Path("uploads/company_profile")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

def extract_entity_metadata(entity_data: dict) -> dict:
    """
    Extract NAICS codes and keywords (from PSC codes) from SAM.gov entity data.
    """
    metadata = {
        "naics": [],
        "keywords": []
    }
    
    if not entity_data:
        return metadata
        
    try:
        assertions = entity_data.get("assertions", {})
        goods_and_services = assertions.get("goodsAndServices", {})
        
        # Extract NAICS
        naics_list = goods_and_services.get("naicsList", [])
        if naics_list:
            metadata["naics"] = [item.get("naicsCode") for item in naics_list if item.get("naicsCode")]
            
        # Extract Keywords (PSC Codes removed as per request)
        # psc_list = goods_and_services.get("pscList", [])
        keywords = set()
        # if psc_list:
        #     for item in psc_list:
        #         if item.get("pscCode"):
        #             keywords.add(item.get("pscCode"))
        #         if item.get("pscName"):
        #             keywords.add(item.get("pscName"))
        
        # Also consider business types as keywords
        # Check assertions (original location)
        business_types = assertions.get("businessTypes", {}).get("businessTypeList", [])
        
        # Check coreData (new location found in real data)
        core_data = entity_data.get("coreData", {})
        if not business_types:
            business_types = core_data.get("businessTypes", {}).get("businessTypeList", [])
            
        if business_types:
            for item in business_types:
                # Check both possible field names
                name = item.get("businessTypeName") or item.get("businessTypeDesc")
                if name:
                    keywords.add(name)
                    
        metadata["keywords"] = list(keywords)
        
    except Exception as e:
        print(f"Error extracting metadata: {e}")
        
    return metadata

@router.post("/", response_model=schemas.CompanyProfile)
async def create_company_profile(
    profile: schemas.CompanyProfileCreate, 
    db: AsyncSession = Depends(get_db)
):
    # Check if UEI already exists
    result = await db.execute(select(CompanyProfile).where(CompanyProfile.uei == profile.uei))
    existing = result.scalars().first()
    if existing:
        raise HTTPException(status_code=400, detail="Company Profile with this UEI already exists")

    db_profile = CompanyProfile(**profile.model_dump())
    db.add(db_profile)
    await db.commit()
    await db.refresh(db_profile)
    db_profile.awards = []  # Initialize awards for response schema
    return db_profile

@router.get("/", response_model=List[schemas.CompanyProfile])
async def get_company_profiles(
    skip: int = 0, 
    limit: int = 10, 
    db: AsyncSession = Depends(get_db)
):
    # Get all profiles
    result = await db.execute(select(CompanyProfile).offset(skip).limit(limit))
    profiles = result.scalars().all()
    
    # Sort so that the profile corresponding to the primary entity is first
    # We need to fetch the primary entity UEI first
    primary_res = await db.execute(select(Entity.uei).where(Entity.is_primary == True))
    primary_uei = primary_res.scalar_one_or_none()
    
    if primary_uei:
        # Sort profiles: primary first
        profiles = sorted(profiles, key=lambda p: p.uei != primary_uei)
        
    # Initialize awards for all profiles to satisfy schema
    # Initialize awards for all profiles
    from fedops_core.db.models import EntityAward
    for p in profiles:
        awards_res = await db.execute(
            select(EntityAward)
            .where(EntityAward.recipient_uei == p.uei)
            .order_by(EntityAward.award_date.desc().nulls_last())
            .limit(50) # Limit to avoid massive payloads for list view
        )
        p.awards = awards_res.scalars().all()
        
    return profiles

@router.get("/{uei}", response_model=schemas.CompanyProfile)
async def get_company_profile(uei: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CompanyProfile).where(CompanyProfile.uei == uei))
    profile = result.scalars().first()
    if not profile:
        raise HTTPException(status_code=404, detail="Company Profile not found")
        
    # Fetch awards manually since we don't have a relationship yet (or just query them)
    # Using explicit query for now 
    from fedops_core.db.models import EntityAward
    awards_res = await db.execute(select(EntityAward).where(EntityAward.recipient_uei == uei).order_by(EntityAward.award_date.desc().nulls_last()))
    profile.awards = awards_res.scalars().all()
    
    # Fetch Past Performances
    from fedops_core.services.past_performance_service import PastPerformanceService
    # Use entity_uei if available, otherwise company uei
    target_uei = profile.entity_uei if profile.entity_uei else uei
    profile.past_performances = await PastPerformanceService.list_by_entity(db, target_uei)
    
    return profile

@router.put("/{uei}", response_model=schemas.CompanyProfile)
async def update_company_profile(
    uei: str, 
    profile_update: schemas.CompanyProfileUpdate, 
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(CompanyProfile).where(CompanyProfile.uei == uei))
    db_profile = result.scalars().first()
    if not db_profile:
        raise HTTPException(status_code=404, detail="Company Profile not found")

    update_data = profile_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_profile, key, value)

    await db.commit()
    await db.refresh(db_profile)
    
    # Fetch awards to maintain consistency in response
    from fedops_core.db.models import EntityAward
    awards_res = await db.execute(select(EntityAward).where(EntityAward.recipient_uei == uei).order_by(EntityAward.award_date.desc().nulls_last()))
    db_profile.awards = awards_res.scalars().all()
    
    return db_profile

# ============ Entity Selection Endpoints ============

async def _set_primary_entity(db: AsyncSession, entity_uei: str):
    """Helper to set the primary entity flag"""
    # Unset primary for all
    # We fetch all primary and unset them
    result = await db.execute(select(Entity).where(Entity.is_primary == True))
    current_primaries = result.scalars().all()
    for p in current_primaries:
        p.is_primary = False
        db.add(p)
    
    # Set new primary
    result = await db.execute(select(Entity).where(Entity.uei == entity_uei))
    entity = result.scalars().first()
    if entity:
        entity.is_primary = True
        db.add(entity)
    
    return entity

@router.post("/set-entity/{entity_uei}", response_model=schemas.CompanyProfile)
async def set_entity_as_profile(
    entity_uei: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Set an entity from SAM.gov as the ACTIVE company profile. Creates profile if needed."""
    # 1. Verify entity exists
    result = await db.execute(select(Entity).where(Entity.uei == entity_uei))
    entity = result.scalars().first()
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found. Please search for the entity first.")
    
    # 1.5 Check if entity has full data (assertions), if not fetch it
    if not entity.full_response or "assertions" not in entity.full_response:
        sam_client = SamEntityClient()
        full_data = await sam_client.get_entity(entity_uei)
        if full_data:
            entity.full_response = full_data
            # Update other fields if needed
            if "entityRegistration" in full_data:
                reg = full_data["entityRegistration"]
                entity.legal_business_name = reg.get("legalBusinessName", entity.legal_business_name)
                entity.cage_code = reg.get("cageCode", entity.cage_code)
            db.add(entity) # Mark for update
            await db.commit() # Commit to save full data
    
    # 2. Set as primary entity
    await _set_primary_entity(db, entity_uei)
    
    # 2.5 Trigger enrichment (Awards, Opportunities)
    background_tasks.add_task(entity_enrichment_service.enrich_entity, entity_uei)
    
    # 3. Check if a company profile already exists for THIS entity
    result = await db.execute(select(CompanyProfile).where(CompanyProfile.uei == entity_uei))
    existing_profile = result.scalars().first()
    
    if existing_profile:
        # Profile exists, just return it (it's now the active one because we set is_primary)
        await db.commit()
        await db.refresh(existing_profile)
        
        # Attach awards
        from fedops_core.db.models import EntityAward
        awards_res = await db.execute(select(EntityAward).where(EntityAward.recipient_uei == entity_uei).order_by(EntityAward.award_date.desc().nulls_last()))
        existing_profile.awards = awards_res.scalars().all()
        
        return existing_profile
    else:
        # 4. Extract metadata from entity
        metadata = extract_entity_metadata(entity.full_response)
        
        # Create new profile for this entity
        new_profile = CompanyProfile(
            uei=entity_uei,
            company_name=entity.legal_business_name,
            entity_uei=entity_uei,
            target_naics=metadata["naics"],
            target_keywords=metadata["keywords"],
            target_set_asides=[]
        )
        db.add(new_profile)
        await db.commit()
        await db.refresh(new_profile)
        new_profile.awards = [] # New profile, no awards yet
        return new_profile

@router.put("/{company_uei}/switch-entity/{new_entity_uei}", response_model=schemas.CompanyProfile)
async def switch_company_entity(
    company_uei: str,
    new_entity_uei: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Switch the ACTIVE company profile to a different entity. Creates profile if needed."""
    # This is effectively the same as set_entity_as_profile, but we might want to validate company_uei was the previous one
    # For now, just delegate to the same logic
    return await set_entity_as_profile(new_entity_uei, background_tasks, db)

# ============ Document Management Endpoints ============

@router.post("/{company_uei}/documents", response_model=schemas.CompanyProfileDocument)
async def upload_company_document(
    company_uei: str,
    file: UploadFile = File(...),
    document_type: str = Form(...),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db)
):
    """Upload a document for the company profile"""
    # 1. Verify company profile exists
    result = await db.execute(select(CompanyProfile).where(CompanyProfile.uei == company_uei))
    profile = result.scalars().first()
    if not profile:
        raise HTTPException(status_code=404, detail="Company Profile not found")
    
    # 2. Create directory for this company
    company_dir = UPLOAD_DIR / company_uei
    company_dir.mkdir(parents=True, exist_ok=True)
    
    # 3. Save file
    file_path = company_dir / file.filename
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # 4. Get file size
    file_size = os.path.getsize(file_path)
    
    # 5. Create database record
    db_document = CompanyProfileDocument(
        company_uei=company_uei,
        document_type=document_type,
        title=title,
        description=description,
        file_path=str(file_path),
        file_size=file_size
    )
    db.add(db_document)
    await db.commit()
    await db.refresh(db_document)
    
    return db_document

@router.get("/{company_uei}/documents", response_model=List[schemas.CompanyProfileDocument])
async def get_company_documents(
    company_uei: str,
    document_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get all documents for a company profile, optionally filtered by type"""
    query = select(CompanyProfileDocument).where(CompanyProfileDocument.company_uei == company_uei)
    
    if document_type:
        query = query.where(CompanyProfileDocument.document_type == document_type)
    
    result = await db.execute(query)
    return result.scalars().all()

@router.post("/{company_uei}/documents/bulk", response_model=List[schemas.CompanyProfileDocument])
async def upload_company_documents_bulk(
    company_uei: str,
    files: List[UploadFile] = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: AsyncSession = Depends(get_db)
):
    """
    Bulk upload documents for a company profile.
    Automatically classifies documents and extracts content in the background.
    """
    from fedops_core.services.company_document_service import CompanyDocumentService
    service = CompanyDocumentService(db)
    
    # Verify company exists
    result = await db.execute(select(CompanyProfile).where(CompanyProfile.uei == company_uei))
    if not result.scalars().first():
        raise HTTPException(status_code=404, detail="Company Profile not found")

    return await service.process_bulk_upload(company_uei, files, background_tasks)

@router.delete("/{company_uei}/documents/{doc_id}")
async def delete_company_document(
    company_uei: str,
    doc_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete a document from the company profile"""
    # 1. Get document
    result = await db.execute(
        select(CompanyProfileDocument).where(
            CompanyProfileDocument.id == doc_id,
            CompanyProfileDocument.company_uei == company_uei
        )
    )
    document = result.scalars().first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # 2. Delete file from filesystem
    try:
        if os.path.exists(document.file_path):
            os.remove(document.file_path)
    except Exception as e:
        print(f"Error deleting file: {e}")
    
    # 3. Delete database record
    await db.delete(document)
    await db.commit()
    
    return {"message": "Document deleted successfully"}
    
@router.post("/{company_uei}/documents/{doc_id}/reanalyze")
async def reanalyze_document(
    company_uei: str,
    doc_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Trigger re-analysis of a document"""
    from fedops_core.services.company_document_service import CompanyDocumentService
    service = CompanyDocumentService(db)
    
    success = await service.reanalyze_document(doc_id, background_tasks)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")
        
    return {"message": "Re-analysis triggered"}

@router.post("/{company_uei}/documents/{doc_id}/generate-pp")
async def generate_past_performance(
    company_uei: str,
    doc_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Generate Past Performance record from a document"""
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"Starting PP generation for company_uei={company_uei}, doc_id={doc_id}")
    
    from fedops_core.services.past_performance_service import PastPerformanceService
    from fedops_core.services.ai_service import AIService
    
    # Initialize services
    ai_service = AIService()
    
    try:
        logger.info(f"Calling PastPerformanceService.generate_from_document...")
        pp = await PastPerformanceService.generate_from_document(db, doc_id, ai_service)
        logger.info(f"Successfully generated PP with id={pp.id}, title={pp.title}")
        return {"message": "Past Performance generation started", "id": pp.id, "title": pp.title}
    except ValueError as e:
        logger.error(f"ValueError in PP generation: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in PP generation: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error generating Past Performance: {str(e)}")

@router.get("/past-performance/{pp_id}")
async def get_past_performance(
    pp_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific Past Performance record"""
    from fedops_core.services.past_performance_service import PastPerformanceService
    
    pp = await PastPerformanceService.get_past_performance(db, pp_id)
    if not pp:
        raise HTTPException(status_code=404, detail="Past Performance record not found")
        
    return pp

# ============ Link Management Endpoints ============

@router.post("/{company_uei}/links", response_model=schemas.CompanyProfileLink)
async def add_company_link(
    company_uei: str,
    link: schemas.CompanyProfileLinkCreate,
    db: AsyncSession = Depends(get_db)
):
    """Add a link to the company profile"""
    # 1. Verify company profile exists
    result = await db.execute(select(CompanyProfile).where(CompanyProfile.uei == company_uei))
    profile = result.scalars().first()
    if not profile:
        raise HTTPException(status_code=404, detail="Company Profile not found")
    
    # 2. Create link
    db_link = CompanyProfileLink(**link.model_dump())
    db.add(db_link)
    await db.commit()
    await db.refresh(db_link)
    
    return db_link

@router.get("/{company_uei}/links", response_model=List[schemas.CompanyProfileLink])
async def get_company_links(
    company_uei: str,
    link_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get all links for a company profile, optionally filtered by type"""
    query = select(CompanyProfileLink).where(CompanyProfileLink.company_uei == company_uei)
    
    if link_type:
        query = query.where(CompanyProfileLink.link_type == link_type)
    
    result = await db.execute(query)
    return result.scalars().all()

@router.delete("/{company_uei}/links/{link_id}")
async def delete_company_link(
    company_uei: str,
    link_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete a link from the company profile"""
    result = await db.execute(
        select(CompanyProfileLink).where(
            CompanyProfileLink.id == link_id,
            CompanyProfileLink.company_uei == company_uei
        )
    )
    link = result.scalars().first()
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    
    await db.delete(link)
    await db.commit()
    
    return {"message": "Link deleted successfully"}
