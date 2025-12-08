"""
Pydantic schemas for Perplexity-powered competitive analysis.
Defines structured output for entity research with citations.
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class Citation(BaseModel):
    """A research source citation from Perplexity search results"""
    title: str = Field(..., description="Title of the source")
    url: str = Field(..., description="URL of the source")
    snippet: Optional[str] = Field(None, description="Brief excerpt from the source")
    date: Optional[str] = Field(None, description="Publication or crawl date")


class Strength(BaseModel):
    """A competitive strength with supporting evidence"""
    description: str = Field(..., description="Description of the strength")
    evidence: Optional[str] = Field(None, description="Supporting evidence or details")
    source_index: Optional[int] = Field(None, description="Index into citations array")


class Weakness(BaseModel):
    """A competitive weakness or vulnerability"""
    description: str = Field(..., description="Description of the weakness")
    evidence: Optional[str] = Field(None, description="Supporting evidence or details")
    source_index: Optional[int] = Field(None, description="Index into citations array")


class CompetitiveStrategy(BaseModel):
    """A strategy to compete against this entity"""
    strategy: str = Field(..., description="The competitive strategy")
    rationale: str = Field(..., description="Why this strategy would be effective")
    priority: str = Field("MEDIUM", description="Priority level: HIGH, MEDIUM, LOW")


class CompetitiveAnalysisResult(BaseModel):
    """Complete competitive analysis result from Perplexity research"""
    entity_name: str = Field(..., description="Name of the analyzed entity")
    entity_uei: Optional[str] = Field(None, description="UEI if available")
    
    overview: str = Field(..., description="Executive summary of the entity")
    market_position: str = Field(..., description="Description of market position")
    
    strengths: List[Strength] = Field(default_factory=list, description="List of competitive strengths")
    weaknesses: List[Weakness] = Field(default_factory=list, description="List of weaknesses/vulnerabilities")
    key_differentiators: List[str] = Field(default_factory=list, description="What sets them apart")
    how_to_beat_them: List[CompetitiveStrategy] = Field(default_factory=list, description="Strategies to win against them")
    
    citations: List[Citation] = Field(default_factory=list, description="Research sources")
    analyzed_at: datetime = Field(default_factory=datetime.utcnow, description="When analysis was performed")
    raw_response: Optional[str] = Field(None, description="Raw API response for debugging")

    class Config:
        from_attributes = True


class CompetitiveAnalysisRequest(BaseModel):
    """Request body for competitive analysis research"""
    context: Optional[str] = Field(
        None, 
        description="Additional context about the entity or opportunity (e.g., 'defense contractor, IT modernization')"
    )
    opportunity_id: Optional[int] = Field(None, description="Optional opportunity ID for context")
    force_refresh: bool = Field(False, description="Force new research even if cached results exist")


class CompetitiveAnalysisDB(BaseModel):
    """Schema for database-stored competitive analysis"""
    id: int
    entity_uei: Optional[str]
    entity_name: str
    opportunity_id: Optional[int]
    overview: Optional[str]
    market_position: Optional[str]
    strengths: Optional[List[dict]]
    weaknesses: Optional[List[dict]]
    key_differentiators: Optional[List[str]]
    strategies_to_beat: Optional[List[dict]]
    citations: Optional[List[dict]]
    model_used: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
