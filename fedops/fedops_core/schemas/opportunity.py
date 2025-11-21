from pydantic import BaseModel
from typing import List, Optional, Any, Dict
from datetime import datetime

class OpportunityBase(BaseModel):
    notice_id: str
    title: str
    solicitation_number: Optional[str] = None
    department: Optional[str] = None
    sub_tier: Optional[str] = None
    office: Optional[str] = None
    posted_date: Optional[datetime] = None
    type: Optional[str] = None
    base_type: Optional[str] = None
    archive_type: Optional[str] = None
    archive_date: Optional[datetime] = None
    type_of_set_aside_description: Optional[str] = None
    type_of_set_aside: Optional[str] = None
    response_deadline: Optional[datetime] = None
    naics_code: Optional[str] = None
    classification_code: Optional[str] = None
    active: Optional[str] = "Yes"
    
    award: Optional[Dict[str, Any]] = None
    point_of_contact: Optional[List[Dict[str, Any]]] = None
    description: Optional[str] = None
    organization_type: Optional[str] = None
    office_address: Optional[Dict[str, Any]] = None
    place_of_performance: Optional[Dict[str, Any]] = None
    additional_info_link: Optional[str] = None
    ui_link: Optional[str] = None
    links: Optional[List[Dict[str, Any]]] = None
    resource_links: Optional[List[str]] = None
    
    full_response: Optional[Dict[str, Any]] = None

class OpportunityCreate(OpportunityBase):
    pass

class OpportunityUpdate(OpportunityBase):
    pass

class Opportunity(OpportunityBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
