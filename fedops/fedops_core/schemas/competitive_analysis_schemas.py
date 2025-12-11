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


class LOBItem(BaseModel):
    """Line of Business with responsibilities"""
    name: str = Field(..., description="Name of the line of business")
    description: str = Field(..., description="What this LOB does")
    responsibilities: List[str] = Field(default_factory=list, description="Key responsibilities")
    key_programs: List[str] = Field(default_factory=list, description="Major programs under this LOB")
    budget_share: Optional[str] = Field(None, description="Percentage of agency budget e.g. '15%'")


class BudgetItem(BaseModel):
    """Budget allocation by division/program"""
    division: str = Field(..., description="Division or program name")
    amount: Optional[str] = Field(None, description="Dollar amount e.g. '$2.5B'")
    percentage: Optional[float] = Field(None, description="Percentage of total budget")
    trend: Optional[str] = Field(None, description="Budget trend: increasing, stable, decreasing")


class OrgNode(BaseModel):
    """Hierarchical org structure node for tree visualization"""
    name: str = Field(..., description="Name of position or unit")
    title: Optional[str] = Field(None, description="Job title or description")
    icon_type: str = Field("default", description="Icon type: aviation, military, health, finance, etc.")
    children: List["OrgNode"] = Field(default_factory=list, description="Child nodes in hierarchy")


# Enable self-referencing in OrgNode
OrgNode.model_rebuild()


class AgencyResearchResult(BaseModel):
    """Competitive intelligence for a Federal Agency"""
    agency_name: str = Field(..., description="Name of the agency")
    acronym: Optional[str] = Field(None, description="Agency acronym")
    
    overview: str = Field(..., description="Agency mission and overview")
    strategic_goals: List[str] = Field(default_factory=list, description="Key strategic goals and priorities")
    budget_outlook: str = Field(..., description="Budget summary and outlook")
    
    org_structure: str = Field(..., description="Description of organizational structure")
    org_tree: Optional[OrgNode] = Field(None, description="Hierarchical tree structure for visualization")
    key_bureaus: List[str] = Field(default_factory=list, description="Key sub-agencies or bureaus")
    
    # NEW: Lines of Business with responsibilities
    lines_of_business: List[LOBItem] = Field(default_factory=list, description="Lines of business and their responsibilities")
    
    # NEW: Budget breakdown by division/program
    budget_by_division: List[BudgetItem] = Field(default_factory=list, description="Budget allocation by division")
    
    pain_points: List[str] = Field(default_factory=list, description="Major challenges or pain points")
    procurement_priorities: List[str] = Field(default_factory=list, description="What they are looking to buy")
    
    citations: List[Citation] = Field(default_factory=list, description="Research sources")
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)
    raw_response: Optional[str] = Field(None, description="Raw API response")


class COResearchResult(BaseModel):
    """Intelligence on a Contracting Officer"""
    co_name: str = Field(..., description="Name of the Contracting Officer")
    agency: Optional[str] = Field(None, description="Agency they work for")
    
    overview: str = Field(..., description="Professional background and overview")
    career_history: List[str] = Field(default_factory=list, description="Past roles and agencies")
    education: Optional[str] = Field(None, description="Education background")
    
    awarding_patterns: Optional[str] = Field(None, description="Observed patterns in their contract awards")
    preferred_vehicles: List[str] = Field(default_factory=list, description="Contract vehicles they frequently use")
    
    citations: List[Citation] = Field(default_factory=list, description="Research sources")
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)
    raw_response: Optional[str] = Field(None, description="Raw API response")


class ContractingProfessionalMatch(BaseModel):
    """Details of a matched contracting professional"""
    name: str = Field(..., description="Full name of the professional")
    agency: str = Field(..., description="Agency they are associated with")
    office: Optional[str] = Field(None, description="Office or Bureau")
    role: Optional[str] = Field(None, description="Job title or role")
    match_reason: Optional[str] = Field(None, description="Why this person was returned")
    location: Optional[str] = Field(None, description="Location if available")
    contact_info: Optional[str] = Field(None, description="Public contact info")
    overview: Optional[str] = Field(None, description="Brief professional summary")
    recent_activity: Optional[str] = Field(None, description="Recent solicitations or awards")


class ContractingProfessionalSearchResult(BaseModel):
    """Result of searching for contracting professionals"""
    query: str = Field(..., description="Original search query")
    matches: List[ContractingProfessionalMatch] = Field(default_factory=list, description="List of potential matches")
    
    citations: List[Citation] = Field(default_factory=list, description="Research sources")
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)
    raw_response: Optional[str] = Field(None, description="Raw API response")
