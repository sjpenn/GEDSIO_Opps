from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from fedops_core.db.engine import get_db
from fedops_core.db.models import CompanyProfile
from fedops_core.schemas import company as schemas

router = APIRouter()

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
    return db_profile

@router.get("/", response_model=List[schemas.CompanyProfile])
async def get_company_profiles(
    skip: int = 0, 
    limit: int = 10, 
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(CompanyProfile).offset(skip).limit(limit))
    return result.scalars().all()

@router.get("/{uei}", response_model=schemas.CompanyProfile)
async def get_company_profile(uei: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CompanyProfile).where(CompanyProfile.uei == uei))
    profile = result.scalars().first()
    if not profile:
        raise HTTPException(status_code=404, detail="Company Profile not found")
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
    return db_profile
