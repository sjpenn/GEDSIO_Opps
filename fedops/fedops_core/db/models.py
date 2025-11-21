from sqlalchemy import Column, Integer, String, DateTime, Boolean, ARRAY, Text, ForeignKey, Float, Date
from sqlalchemy.dialects.postgresql import JSONB
from fedops_core.db.engine import Base
from datetime import datetime

class Opportunity(Base):
    __tablename__ = "opportunities"

    id = Column(Integer, primary_key=True, index=True)
    notice_id = Column(String, unique=True, index=True)
    solicitation_number = Column(String, index=True, nullable=True)
    title = Column(String, index=True)
    department = Column(String, index=True, nullable=True)
    sub_tier = Column(String, nullable=True)
    office = Column(String, nullable=True)
    posted_date = Column(DateTime, index=True)
    type = Column(String, index=True)
    base_type = Column(String, nullable=True)
    archive_type = Column(String, nullable=True)
    archive_date = Column(DateTime, nullable=True)
    type_of_set_aside_description = Column(String, nullable=True)
    type_of_set_aside = Column(String, nullable=True)
    response_deadline = Column(DateTime, nullable=True)
    naics_code = Column(String, index=True, nullable=True)
    classification_code = Column(String, nullable=True)
    active = Column(String, default="Yes") # "Yes" or "No" from API
    
    # Nested structures stored as JSONB
    award = Column(JSONB, nullable=True)
    point_of_contact = Column(JSONB, nullable=True)
    description = Column(Text, nullable=True)  # Full description text from SAM.gov
    organization_type = Column(String, nullable=True)
    office_address = Column(JSONB, nullable=True)
    place_of_performance = Column(JSONB, nullable=True)
    additional_info_link = Column(String, nullable=True)
    ui_link = Column(String, nullable=True)
    links = Column(JSONB, nullable=True) # List of links
    resource_links = Column(ARRAY(String), nullable=True) # Keep for compatibility or extra links
    resource_files = Column(JSONB, nullable=True) # Store resolved filenames: [{url, filename}]
    
    full_response = Column(JSONB, nullable=True) # Store the complete raw response

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class CompanyProfile(Base):
    __tablename__ = "company_profiles"

    id = Column(Integer, primary_key=True, index=True)
    uei = Column(String, unique=True, index=True, nullable=False)
    company_name = Column(String, nullable=False)
    target_naics = Column(JSONB, default=[])
    target_keywords = Column(JSONB, default=[])
    target_set_asides = Column(JSONB, default=[])
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Entity(Base):
    __tablename__ = "entities"

    uei = Column(String, primary_key=True, index=True)
    legal_business_name = Column(String, nullable=False)
    cage_code = Column(String, nullable=True)
    entity_type = Column(String, default="OTHER") # PARTNER, COMPETITOR, OTHER
    notes = Column(Text, nullable=True)
    full_response = Column(JSONB, nullable=True)
    last_synced_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class EntityAward(Base):
    __tablename__ = "entity_awards"

    award_id = Column(String, primary_key=True, index=True)
    recipient_uei = Column(String, ForeignKey("entities.uei"), index=True)
    total_obligation = Column(Float, nullable=True)
    description = Column(Text, nullable=True)
    award_date = Column(Date, nullable=True)
    awarding_agency = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
