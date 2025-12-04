from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from fedops_core.db.engine import Base
from datetime import datetime


class OpportunityTeam(Base):
    """Teams formed to pursue specific opportunities"""
    __tablename__ = "opportunity_teams"

    id = Column(Integer, primary_key=True, index=True)
    opportunity_id = Column(Integer, ForeignKey("opportunities.id"), nullable=False, index=True)
    name = Column(String, nullable=False)  # e.g., "IBM-Acme Joint Venture"
    description = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship to members
    members = relationship("TeamMember", back_populates="team", cascade="all, delete-orphan")


class TeamMember(Base):
    """Individual members (entities) within a team"""
    __tablename__ = "team_members"

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("opportunity_teams.id"), nullable=False, index=True)
    entity_uei = Column(String, ForeignKey("entities.uei"), nullable=False, index=True)
    role = Column(String, nullable=False, default="SUB")  # PRIME or SUB
    capabilities_contribution = Column(JSONB, nullable=True)  # Specific capabilities this member brings
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    team = relationship("OpportunityTeam", back_populates="members")
