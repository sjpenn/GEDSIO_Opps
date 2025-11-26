from pydantic import BaseModel
from typing import List, Optional, Any
from datetime import datetime

class CompanyProfileBase(BaseModel):
    uei: str
    company_name: str
    target_naics: List[str] = []
    target_keywords: List[str] = []
    target_set_asides: List[str] = []

class CompanyProfileCreate(CompanyProfileBase):
    pass

class CompanyProfileUpdate(BaseModel):
    company_name: Optional[str] = None
    target_naics: Optional[List[str]] = None
    target_keywords: Optional[List[str]] = None
    target_set_asides: Optional[List[str]] = None

class CompanyProfile(CompanyProfileBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class EntityBase(BaseModel):
    uei: str
    legal_business_name: str
    cage_code: Optional[str] = None
    entity_type: str = "OTHER"
    is_primary: bool = False
    notes: Optional[str] = None

class EntityCreate(EntityBase):
    pass

class Entity(EntityBase):
    full_response: Optional[dict] = None
    last_synced_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    similarity_score: Optional[float] = None

    class Config:
        from_attributes = True

class EntityAwardBase(BaseModel):
    award_id: str
    recipient_uei: str
    total_obligation: Optional[float] = None
    description: Optional[str] = None
    award_date: Optional[Any] = None # Date
    awarding_agency: Optional[str] = None
    award_type: Optional[str] = "Prime"

class EntityAward(EntityAwardBase):
    created_at: datetime

    class Config:
        from_attributes = True
