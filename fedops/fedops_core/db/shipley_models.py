from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from fedops_core.db.engine import Base
from datetime import datetime

class ReviewGate(Base):
    """Decision gates and color team reviews in the Shipley workflow"""
    __tablename__ = "review_gates"
    
    id = Column(Integer, primary_key=True, index=True)
    proposal_id = Column(Integer, ForeignKey("proposals.id"), nullable=False, index=True)
    gate_type = Column(String, nullable=False)  # PURSUIT, BID, BID_VALIDATION
    review_type = Column(String, nullable=True)  # BLUE, PINK, RED, GOLD (for Phase 5)
    outcome = Column(String, nullable=False)  # PASS, FAIL, CONDITIONAL
    score = Column(Float, nullable=True)
    artifact_version_reviewed = Column(String, nullable=True)  # Link to specific version
    decision_by = Column(String, nullable=False)  # User who made decision
    decision_date = Column(DateTime, default=datetime.utcnow)
    justification = Column(Text, nullable=True)  # Required for overrides
    details = Column(JSONB, nullable=True)  # Structured decision data
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ReviewComment(Base):
    """Structured feedback from color team reviews"""
    __tablename__ = "review_comments"
    
    id = Column(Integer, primary_key=True, index=True)
    review_gate_id = Column(Integer, ForeignKey("review_gates.id"), nullable=False, index=True)
    artifact_id = Column(Integer, ForeignKey("stored_files.id"), nullable=True)
    section_reference = Column(String, nullable=True)  # Section/page reference
    comment_text = Column(Text, nullable=False)
    comment_type = Column(String, nullable=False)  # COMPLIANCE, CLARITY, STRATEGY, TECHNICAL
    severity = Column(String, default="MEDIUM")  # CRITICAL, HIGH, MEDIUM, LOW
    status = Column(String, default="OPEN")  # OPEN, ADDRESSED, RESOLVED
    reviewer_name = Column(String, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CompetitiveIntelligence(Base):
    """Competitive intelligence from USAspending and other sources"""
    __tablename__ = "competitive_intelligence"
    
    id = Column(Integer, primary_key=True, index=True)
    opportunity_id = Column(Integer, ForeignKey("opportunities.id"), nullable=False, index=True)
    competitor_uei = Column(String, ForeignKey("entities.uei"), nullable=True)
    competitor_name = Column(String, nullable=False)
    historical_wins = Column(Integer, default=0)  # Count of similar awards
    total_obligation = Column(Float, default=0.0)  # Total $ won in similar contracts
    win_probability_impact = Column(Float, nullable=True)  # Impact on WP score
    is_incumbent = Column(Boolean, default=False)
    data_source = Column(String, default="USAspending")  # USAspending, manual, other
    naics_match = Column(String, nullable=True)
    agency_match = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class BidNoGidCriteria(Base):
    """Weighted Bid/No-Bid scoring matrix"""
    __tablename__ = "bid_no_bid_criteria"
    
    id = Column(Integer, primary_key=True, index=True)
    opportunity_id = Column(Integer, ForeignKey("opportunities.id"), nullable=False, unique=True)
    
    # Position to Win (35%)
    win_probability_score = Column(Float, default=0.0)
    competitive_landscape_score = Column(Float, default=0.0)
    incumbent_advantage_score = Column(Float, default=0.0)
    
    # Capability/Capacity (35%)
    technical_capability_score = Column(Float, default=0.0)
    past_performance_relevance_score = Column(Float, default=0.0)
    resource_availability_score = Column(Float, default=0.0)
    compliance_score = Column(Float, default=0.0)
    
    # Attractiveness (30%)
    contract_value_score = Column(Float, default=0.0)
    strategic_alignment_score = Column(Float, default=0.0)
    agency_relationship_score = Column(Float, default=0.0)
    
    # Weighted composite
    weighted_score = Column(Float, default=0.0)
    recommendation = Column(String, nullable=True)  # BID, NO_BID, REVIEW
    
    # Weighting factors (customizable)
    position_weight = Column(Float, default=0.35)
    capability_weight = Column(Float, default=0.35)
    attractiveness_weight = Column(Float, default=0.30)
    
    details = Column(JSONB, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CapturePlan(Base):
    """Phase 3 Capture Plan details"""
    __tablename__ = "capture_plans"

    id = Column(Integer, primary_key=True, index=True)
    proposal_id = Column(Integer, ForeignKey("proposals.id"), nullable=False, unique=True, index=True)
    
    # Strategy
    win_strategy = Column(Text, nullable=True)
    executive_summary_theme = Column(Text, nullable=True)
    
    # Structured Data (JSON)
    customer_hot_buttons = Column(JSONB, default=list)  # [{issue: "", impact: "", solution: ""}]
    discriminators = Column(JSONB, default=list)  # [{discriminator: "", proof: ""}]
    key_themes = Column(JSONB, default=list)  # ["Theme 1", "Theme 2"]
    
    # Competitor Analysis (beyond auto-generated)
    competitor_analysis_summary = Column(Text, nullable=True)
    
    # Teaming
    teaming_strategy = Column(Text, nullable=True)
    partners = Column(JSONB, default=list)  # [{name: "", role: "", status: ""}]
    
    # Action Items
    action_items = Column(JSONB, default=list)  # [{task: "", owner: "", due: "", status: ""}]
    
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Submission(Base):
    """Phase 6 Proposal Submission details"""
    __tablename__ = "submissions"
    
    id = Column(Integer, primary_key=True, index=True)
    proposal_id = Column(Integer, ForeignKey("proposals.id"), nullable=False, unique=True, index=True)
    
    submission_date = Column(DateTime, nullable=False)
    submission_method = Column(String, nullable=False)  # EMAIL, PORTAL, PHYSICAL
    tracking_number = Column(String, nullable=True)
    submitted_by = Column(String, nullable=False)
    submission_notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Award(Base):
    """Phase 6 Award outcome tracking"""
    __tablename__ = "awards"
    
    id = Column(Integer, primary_key=True, index=True)
    proposal_id = Column(Integer, ForeignKey("proposals.id"), nullable=False, unique=True, index=True)
    
    status = Column(String, nullable=False)  # WON, LOST, CANCELLED, PENDING
    award_date = Column(DateTime, nullable=True)
    contract_number = Column(String, nullable=True)
    contract_value = Column(Float, nullable=True)
    award_notes = Column(Text, nullable=True)
    debrief_date = Column(DateTime, nullable=True)
    debrief_notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class LessonsLearned(Base):
    """Phase 6 Lessons Learned from proposal process"""
    __tablename__ = "lessons_learned"
    
    id = Column(Integer, primary_key=True, index=True)
    proposal_id = Column(Integer, ForeignKey("proposals.id"), nullable=False, index=True)
    
    category = Column(String, nullable=False)  # PROCESS, TECHNICAL, STRATEGY, PRICING
    observation = Column(Text, nullable=False)
    impact = Column(String, nullable=True)  # POSITIVE, NEGATIVE, NEUTRAL
    recommendation = Column(Text, nullable=True)
    recorded_by = Column(String, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
