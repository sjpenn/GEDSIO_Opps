from pydantic import BaseModel
from typing import List, Optional, Any
from datetime import datetime

class CompanyProfileBase(BaseModel):
    uei: str
    company_name: str
    entity_uei: Optional[str] = None
    target_naics: List[str] = []
    target_keywords: List[str] = []
    target_set_asides: List[str] = []

class CompanyProfileCreate(CompanyProfileBase):
    pass

class CompanyProfileUpdate(BaseModel):
    company_name: Optional[str] = None
    entity_uei: Optional[str] = None
    target_naics: Optional[List[str]] = None
    target_keywords: Optional[List[str]] = None
    target_set_asides: Optional[List[str]] = None

class CompanyProfile(CompanyProfileBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Company Profile Document Schemas
class CompanyProfileDocumentBase(BaseModel):
    company_uei: str
    document_type: str  # SOW, Capability, PastPerformance, Other
    title: str
    description: Optional[str] = None

class CompanyProfileDocumentCreate(CompanyProfileDocumentBase):
    pass

class CompanyProfileDocument(CompanyProfileDocumentBase):
    id: int
    file_path: str
    file_size: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Company Profile Link Schemas
class CompanyProfileLinkBase(BaseModel):
    company_uei: str
    link_type: str  # SOW, PWS, Capability, Other
    title: str
    url: str
    description: Optional[str] = None

class CompanyProfileLinkCreate(CompanyProfileLinkBase):
    pass

class CompanyProfileLink(CompanyProfileLinkBase):
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
    
    # Partner Search Fields
    revenue: Optional[float] = None
    capabilities: Optional[List[dict]] = None
    locations: Optional[List[dict]] = None
    web_addresses: Optional[List[dict]] = None
    personnel_count: Optional[int] = None
    business_types: Optional[List[dict]] = None

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
