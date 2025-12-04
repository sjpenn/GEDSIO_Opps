from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float, Boolean, JSON, ARRAY, Date, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from fedops_core.db.engine import Base
from datetime import datetime
import enum

class ShipleyPhase(str, enum.Enum):
    """Shipley Business Development Lifecycle Phases"""
    PHASE_0_MARKET_SEGMENTATION = "PHASE_0_MARKET_SEGMENTATION"
    PHASE_1_LONG_TERM_POSITIONING = "PHASE_1_LONG_TERM_POSITIONING"
    PHASE_2_OPPORTUNITY_ASSESSMENT = "PHASE_2_OPPORTUNITY_ASSESSMENT"
    PHASE_3_CAPTURE_PLANNING = "PHASE_3_CAPTURE_PLANNING"
    PHASE_4_PROPOSAL_PLANNING = "PHASE_4_PROPOSAL_PLANNING"
    PHASE_5_PROPOSAL_DEVELOPMENT = "PHASE_5_PROPOSAL_DEVELOPMENT"
    PHASE_6_POST_SUBMITTAL = "PHASE_6_POST_SUBMITTAL"

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

    # Manual Ingest & Incumbent Details
    source = Column(String, default="SAM.gov") # SAM.gov, Ebuy, Efast, Seaport, Manual
    incumbent_vendor = Column(String, nullable=True)
    incumbent_contract_number = Column(String, nullable=True)
    incumbent_value = Column(String, nullable=True)
    incumbent_expiration_date = Column(DateTime, nullable=True)
    previous_sow_document_id = Column(Integer, ForeignKey("stored_files.id"), nullable=True)

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
    logo_url = Column(String, nullable=True)
    
    # Partner Search Fields
    revenue = Column(Float, nullable=True)  # Annual revenue if available
    capabilities = Column(JSONB, nullable=True)  # Array of capability descriptions/NAICS/PSC
    locations = Column(JSONB, nullable=True)  # Array of business locations
    web_addresses = Column(JSONB, nullable=True)  # Array of website URLs
    personnel_count = Column(Integer, nullable=True)  # Employee count
    business_types = Column(JSONB, nullable=True)  # Array of business type codes and descriptions
    
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
    
    # Version Control Fields
    version_number = Column(String, default="1.0", index=True)
    status = Column(String, default="DRAFT")  # DRAFT, REVIEW, FINAL, ARCHIVED
    checked_out_by = Column(String, nullable=True)
    checked_out_at = Column(DateTime, nullable=True)
    s3_uri = Column(String, nullable=True)  # S3 location (future use)
    parent_file_id = Column(Integer, ForeignKey("stored_files.id"), nullable=True)  # Version chain
    
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
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Proposal(Base):
    __tablename__ = "proposals"

    id = Column(Integer, primary_key=True, index=True)
    opportunity_id = Column(Integer, ForeignKey("opportunities.id"), nullable=False, index=True)
    
    version = Column(Integer, default=1)
    
    # Shipley Workflow Fields
    shipley_phase = Column(String, default=ShipleyPhase.PHASE_1_LONG_TERM_POSITIONING.value, index=True)
    capture_manager_id = Column(String, nullable=True)  # User assignment
    pmp_data = Column(JSONB, nullable=True)  # Proposal Management Plan
    
    # Bid Decision Tracking
    bid_decision_score = Column(Float, nullable=True)
    bid_decision_justification = Column(Text, nullable=True)
    bid_decision_date = Column(DateTime, nullable=True)
    bid_decision_by = Column(String, nullable=True)
    
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


class OpportunityPipeline(Base):
    __tablename__ = "opportunity_pipelines"

    id = Column(Integer, primary_key=True, index=True)
    opportunity_id = Column(Integer, ForeignKey("opportunities.id"), nullable=False, unique=True, index=True)
    
    status = Column(String, default="WATCHING") # WATCHING, GO, NO_GO, SUBMITTED, AWARDED
    stage = Column(String, default="QUALIFICATION") # QUALIFICATION, PROPOSAL_DEV, REVIEW, SUBMISSION
    
    questions_due_date = Column(DateTime, nullable=True)
    proposal_due_date = Column(DateTime, nullable=True)
    
    submission_instructions = Column(Text, nullable=True)
    required_artifacts = Column(JSONB, default=[]) # List of required docs
    
    notes = Column(Text, nullable=True)
    
    # Archive fields
    archived = Column(Boolean, default=False, index=True)
    archived_at = Column(DateTime, nullable=True)
    archived_by = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ProposalRequirement(Base):
    __tablename__ = "proposal_requirements"

    id = Column(Integer, primary_key=True, index=True)
    proposal_id = Column(Integer, ForeignKey("proposals.id"), nullable=False, index=True)
    requirement_text = Column(Text, nullable=False)
    requirement_type = Column(String, nullable=False)  # TECHNICAL, MANAGEMENT, PAST_PERFORMANCE, PRICING, CERTIFICATION, OTHER
    source_document_id = Column(Integer, ForeignKey("stored_files.id"), nullable=True)
    source_section = Column(String, nullable=True)
    source_location = Column(JSON, nullable=True)  # {page, paragraph, start_char, end_char}
    priority = Column(String, nullable=False, default="IMPORTANT")  # MANDATORY, IMPORTANT, OPTIONAL
    compliance_status = Column(String, nullable=False, default="NOT_STARTED")  # NOT_STARTED, IN_PROGRESS, COMPLETE, REVIEWED
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Import Shipley workflow models
from fedops_core.db.shipley_models import ReviewGate, ReviewComment, CompetitiveIntelligence, BidNoGidCriteria

# Import Team models
from fedops_core.db.team_models import OpportunityTeam, TeamMember


class RequirementResponse(Base):
    __tablename__ = "requirement_responses"

    id = Column(Integer, primary_key=True, index=True)
    requirement_id = Column(Integer, ForeignKey("proposal_requirements.id"), nullable=False, index=True)
    response_text = Column(Text, nullable=True)
    proposal_section_ref = Column(String, nullable=True)
    assigned_to = Column(String, nullable=True)
    status = Column(String, nullable=False, default="DRAFT")  # DRAFT, REVIEW, APPROVED
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class DocumentArtifact(Base):
    __tablename__ = "document_artifacts"

    id = Column(Integer, primary_key=True, index=True)
    proposal_id = Column(Integer, ForeignKey("proposals.id"), nullable=False, index=True)
    artifact_type = Column(String, nullable=False)  # FORM, CERTIFICATION, PAST_PERFORMANCE, PRICING_SHEET, OTHER
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    source_section = Column(String, nullable=True)
    required = Column(Boolean, nullable=False, default=True)
    status = Column(String, nullable=False, default="NOT_STARTED")  # NOT_STARTED, IN_PROGRESS, COMPLETE
    file_id = Column(Integer, ForeignKey("stored_files.id"), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    stored_file_id = Column(Integer, ForeignKey("stored_files.id"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    metadata_ = Column("metadata", JSONB, nullable=True) # "metadata" is reserved in SQLAlchemy Base, so we map it
    
    page_number = Column(Integer, nullable=True)
    section = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
