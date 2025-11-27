from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float, Boolean, JSON, ARRAY, Date
from sqlalchemy.orm import relationship
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
    
    # Agentic Pipeline Fields
    compliance_status = Column(String, default="PENDING") # PENDING, COMPLIANT, NON_COMPLIANT
    risk_score = Column(Float, nullable=True) # Overall risk score

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class CompanyProfile(Base):
    __tablename__ = "company_profiles"

    id = Column(Integer, primary_key=True, index=True)
    uei = Column(String, unique=True, index=True, nullable=False)
    company_name = Column(String, nullable=False)
    entity_uei = Column(String, ForeignKey("entities.uei"), nullable=True, index=True)  # Link to SAM.gov entity
    target_naics = Column(JSONB, default=[])
    target_keywords = Column(JSONB, default=[])
    target_set_asides = Column(JSONB, default=[])
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class CompanyProfileDocument(Base):
    __tablename__ = "company_profile_documents"

    id = Column(Integer, primary_key=True, index=True)
    company_uei = Column(String, ForeignKey("company_profiles.uei"), nullable=False, index=True)
    document_type = Column(String, nullable=False, index=True)  # SOW, Capability, PastPerformance, Other
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    file_path = Column(String, nullable=False)
    file_size = Column(Integer, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class CompanyProfileLink(Base):
    __tablename__ = "company_profile_links"

    id = Column(Integer, primary_key=True, index=True)
    company_uei = Column(String, ForeignKey("company_profiles.uei"), nullable=False, index=True)
    link_type = Column(String, nullable=False, index=True)  # SOW, PWS, Capability, Other
    title = Column(String, nullable=False)
    url = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    
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
    is_primary = Column(Boolean, default=False)
    
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
    naics_code = Column(String, index=True, nullable=True)
    solicitation_id = Column(String, index=True, nullable=True)
    award_type = Column(String, default="Prime") # Prime or Sub
    
    created_at = Column(DateTime, default=datetime.utcnow)

class StoredFile(Base):
    __tablename__ = "stored_files"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True, nullable=False)
    file_path = Column(String, nullable=False)
    file_type = Column(String, nullable=True)
    file_size = Column(Integer, nullable=True)
    content_summary = Column(Text, nullable=True)
    analysis_json = Column(JSONB, nullable=True)
    parsed_content = Column(Text, nullable=True)
    
    opportunity_id = Column(Integer, ForeignKey("opportunities.id"), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class OpportunityComment(Base):
    __tablename__ = "opportunity_comments"

    id = Column(Integer, primary_key=True, index=True)
    opportunity_id = Column(Integer, ForeignKey("opportunities.id"), nullable=False)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class AgentActivityLog(Base):
    __tablename__ = "agent_activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    opportunity_id = Column(Integer, ForeignKey("opportunities.id"), nullable=False, index=True)
    agent_name = Column(String, nullable=False)
    action = Column(String, nullable=False)
    details = Column(JSONB, nullable=True)
    status = Column(String, nullable=False) # SUCCESS, FAILURE, IN_PROGRESS
    timestamp = Column(DateTime, default=datetime.utcnow)

class OpportunityScore(Base):
    __tablename__ = "opportunity_scores"

    id = Column(Integer, primary_key=True, index=True)
    opportunity_id = Column(Integer, ForeignKey("opportunities.id"), nullable=False, unique=True)
    
    # Scores
    strategic_alignment_score = Column(Float, default=0.0)
    financial_viability_score = Column(Float, default=0.0)
    contract_risk_score = Column(Float, default=0.0)
    internal_capacity_score = Column(Float, default=0.0)
    data_integrity_score = Column(Float, default=0.0)
    
    weighted_score = Column(Float, default=0.0)
    go_no_go_decision = Column(String, nullable=True) # GO, NO_GO, REVIEW
    
    details = Column(JSONB, nullable=True) # Breakdown of scoring factors
    
    created_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Proposal(Base):
    __tablename__ = "proposals"

    id = Column(Integer, primary_key=True, index=True)
    opportunity_id = Column(Integer, ForeignKey("opportunities.id"), nullable=False, index=True)
    
    version = Column(Integer, default=1)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    volumes = relationship("ProposalVolume", back_populates="proposal", cascade="all, delete-orphan")

class ProposalVolume(Base):
    __tablename__ = "proposal_volumes"

    id = Column(Integer, primary_key=True, index=True)
    proposal_id = Column(Integer, ForeignKey("proposals.id"), nullable=False, index=True)
    
    title = Column(String, nullable=False) # e.g., "Volume I: Technical"
    order = Column(Integer, default=0)
    
    # Blocks stored as JSONB: [{id: "uuid", title: "Section", content: "Text", order: 1}]
    blocks = Column(JSONB, default=[])
    
    proposal = relationship("Proposal", back_populates="volumes")

