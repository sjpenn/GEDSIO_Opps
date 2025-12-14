"""
Pydantic schemas for Past Performance Questionnaire API
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class QuestionnaireSection(BaseModel):
    """Individual section of the questionnaire"""
    content: str = ""
    generated: bool = False
    last_generated_at: Optional[datetime] = None
    model_used: Optional[str] = None


class QuestionnaireData(BaseModel):
    """Complete questionnaire data structure"""
    project_overview: QuestionnaireSection = Field(default_factory=QuestionnaireSection)
    scope_of_work: QuestionnaireSection = Field(default_factory=QuestionnaireSection)
    technical_approach: QuestionnaireSection = Field(default_factory=QuestionnaireSection)
    challenges_solutions: QuestionnaireSection = Field(default_factory=QuestionnaireSection)
    results_outcomes: QuestionnaireSection = Field(default_factory=QuestionnaireSection)
    relevance: QuestionnaireSection = Field(default_factory=QuestionnaireSection)
    references: QuestionnaireSection = Field(default_factory=QuestionnaireSection)


class PastPerformanceCreate(BaseModel):
    """Request to create a new past performance questionnaire"""
    entity_uei: str
    award_id: Optional[str] = None
    opportunity_id: Optional[int] = None
    title: str
    created_by: Optional[str] = None


class PastPerformanceUpdate(BaseModel):
    """Request to update an existing past performance"""
    title: Optional[str] = None
    status: Optional[str] = None
    questionnaire_data: Optional[Dict[str, Any]] = None
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None


class PastPerformanceResponse(BaseModel):
    """Response model for past performance"""
    id: int
    entity_uei: str
    award_id: Optional[str] = None
    opportunity_id: Optional[int] = None
    title: str
    status: str
    questionnaire_data: Dict[str, Any]
    created_by: Optional[str] = None
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PastPerformanceWithCitationsResponse(PastPerformanceResponse):
    """Response model for past performance with citations"""
    citations_data: Optional[Dict[str, Any]] = None
    solicitation_context: Optional[Dict[str, Any]] = None


class GenerateSectionRequest(BaseModel):
    """Request to generate content for a specific section"""
    section_name: str = Field(..., description="Name of the section to generate (e.g., 'project_overview')")
    context: Optional[str] = Field(None, description="Additional context for generation")
    force_regenerate: bool = Field(False, description="Force regeneration even if content exists")


class GenerateSectionResponse(BaseModel):
    """Response from section generation"""
    section_name: str
    content: str
    generated: bool
    model_used: str
    generated_at: datetime


class StructuredOutputRequest(BaseModel):
    """Request to export structured output"""
    format: str = Field("json", description="Output format: json, text, markdown")
    include_metadata: bool = Field(True, description="Include metadata in output")


class StructuredOutputResponse(BaseModel):
    """Structured output response"""
    format: str
    content: str
    metadata: Optional[Dict[str, Any]] = None


class QuestionnaireTemplate(BaseModel):
    """Template structure for questionnaire sections"""
    sections: Dict[str, Dict[str, str]] = {
        "project_overview": {
            "title": "Project Overview",
            "description": "Basic information about the contract including number, period of performance, value, and client",
            "prompt_hint": "Include contract details, dates, value, and client information"
        },
        "scope_of_work": {
            "title": "Scope of Work",
            "description": "Detailed description of the work performed under this contract",
            "prompt_hint": "Describe the services or products delivered"
        },
        "technical_approach": {
            "title": "Technical Approach & Solutions",
            "description": "Technical methodologies, tools, and approaches used",
            "prompt_hint": "Explain the technical solutions and methodologies employed"
        },
        "challenges_solutions": {
            "title": "Challenges & Solutions",
            "description": "Key challenges encountered and how they were resolved",
            "prompt_hint": "Describe obstacles faced and innovative solutions implemented"
        },
        "results_outcomes": {
            "title": "Results & Outcomes",
            "description": "Measurable results, achievements, and outcomes",
            "prompt_hint": "Quantify achievements, cost savings, performance improvements"
        },
        "relevance": {
            "title": "Relevance to Current Opportunity",
            "description": "How this past performance relates to the current opportunity",
            "prompt_hint": "Draw parallels between past work and current requirements"
        },
        "references": {
            "title": "References & Points of Contact",
            "description": "Client references and contact information",
            "prompt_hint": "Provide client POC names, titles, phone, and email"
        }
    }
