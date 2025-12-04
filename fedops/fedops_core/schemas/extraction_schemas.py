"""
Pydantic schemas for document extraction validation.

These schemas ensure structured output from AI extraction and track source quotes
to prevent hallucination and enable requirement traceability.
"""

from typing import List, Dict, Optional, Any, Literal
from pydantic import BaseModel, Field, field_validator
from datetime import datetime


# ============================================================================
# Base Models
# ============================================================================

class BaseExtractedItem(BaseModel):
    """Base model for all extracted items with source tracking"""
    source_quote: str = Field(
        description="Exact text from the source document supporting this extraction"
    )
    section_reference: Optional[str] = Field(
        None,
        description="Section/page reference (e.g., 'Section L.3.2.1', 'Page 15')"
    )
    confidence: Optional[Literal["high", "medium", "low"]] = Field(
        None,
        description="Confidence level of extraction"
    )


class SourceDocument(BaseModel):
    """Reference to source document"""
    filename: str
    document_type: str
    section: str


# ============================================================================
# Section L - Instructions to Offerors
# ============================================================================

class FormattingRequirements(BaseModel):
    """Formatting requirements for proposal submission"""
    font: Optional[str] = Field(None, description="Font family and size (e.g., 'Arial 12pt')")
    margins: Optional[str] = Field(None, description="Margin specifications")
    page_limits: Dict[str, int] = Field(default_factory=dict, description="Page limits by volume")
    file_types: List[str] = Field(default_factory=list, description="Accepted file formats")
    file_size_limit: Optional[str] = None
    naming_convention: Optional[str] = None
    color_printing: Optional[str] = None
    source_quote: str = Field(description="Exact text defining formatting requirements")


class SubmissionRequirements(BaseModel):
    """Submission method and deadline requirements"""
    method: str = Field(description="Submission method (PIEE, SAM.gov, Email, etc.)")
    portal: Optional[str] = None
    email: Optional[str] = None
    copies: Dict[str, int] = Field(
        default_factory=lambda: {"electronic": 0, "hard": 0},
        description="Number of copies required"
    )
    due_date: Optional[str] = Field(None, description="Proposal due date/time")
    time_zone: Optional[str] = None
    questions_due: Optional[str] = None
    modifications_allowed: Optional[bool] = None
    late_proposals: Optional[str] = None
    source_quote: str = Field(description="Exact text defining submission requirements")


class VolumeStructure(BaseModel):
    """Structure for proposal volumes"""
    volume_name: str
    page_limit: Optional[int] = None
    content_required: List[str] = Field(default_factory=list)
    file_name: Optional[str] = None
    source_quote: str


class ContentRequirement(BaseExtractedItem):
    """Individual content requirement from Section L"""
    requirement: str = Field(description="The requirement text")
    requirement_type: Literal["mandatory", "optional", "conditional"] = "mandatory"
    volume: Optional[str] = Field(None, description="Which volume this applies to")


class SectionLSchema(BaseModel):
    """Complete Section L extraction schema"""
    formatting: Optional[FormattingRequirements] = None
    submission: Optional[SubmissionRequirements] = None
    volume_structure: List[VolumeStructure] = Field(default_factory=list)
    content_requirements: List[ContentRequirement] = Field(default_factory=list)
    disqualification_risks: List[str] = Field(
        default_factory=list,
        description="Items that could lead to disqualification"
    )
    compliance_checklist: List[str] = Field(default_factory=list)


# ============================================================================
# Section M - Evaluation Criteria
# ============================================================================

class EvaluationFactor(BaseExtractedItem):
    """Individual evaluation factor"""
    factor: str = Field(description="Factor name (e.g., 'Technical Approach')")
    weight: Optional[str] = Field(None, description="Weight or relative importance")
    subfactors: List[str] = Field(default_factory=list)
    discriminators: Optional[str] = Field(
        None,
        description="Key discriminators where points are won/lost"
    )
    win_strategy: Optional[str] = Field(
        None,
        description="Recommended strategy for this factor"
    )


class PriceEvaluation(BaseModel):
    """Price evaluation approach"""
    structure: Optional[str] = Field(None, description="Contract type (FFP, T&M, CPFF, etc.)")
    ceiling: Optional[str] = None
    evaluation_method: Optional[str] = Field(
        None,
        description="How price is evaluated (realism, reasonableness, etc.)"
    )
    most_probable_cost: Optional[bool] = None
    source_quote: str


class SectionMSchema(BaseModel):
    """Complete Section M extraction schema"""
    evaluation_approach: str = Field(
        description="Overall approach (LPTA, Best Value Tradeoff, etc.)"
    )
    rating_system: Optional[Dict[str, Any]] = Field(
        None,
        description="Rating system (adjectival, color, numerical)"
    )
    relative_importance: Optional[str] = Field(
        None,
        description="Relative importance of factors (e.g., 'Technical > Past Perf > Price')"
    )
    factors: List[EvaluationFactor] = Field(default_factory=list)
    price: Optional[PriceEvaluation] = None
    strength_definitions: Optional[Dict[str, str]] = Field(
        None,
        description="Definitions of strengths, weaknesses, deficiencies"
    )


# ============================================================================
# Section H - Special Contract Requirements
# ============================================================================

class KeyPersonnel(BaseExtractedItem):
    """Key personnel requirement"""
    role: str
    qualifications: Optional[str] = None
    experience: Optional[str] = None
    resume_required: bool = True
    substitutability: Optional[str] = None
    clearance: Optional[str] = None


class SecurityRequirements(BaseModel):
    """Security and clearance requirements"""
    facility_clearance: Optional[str] = Field(
        None,
        description="Required facility clearance level"
    )
    personnel_clearances: Dict[str, Any] = Field(default_factory=dict)
    cmmc_level: Optional[str] = None
    cyber_requirements: List[str] = Field(default_factory=list)
    export_control: Optional[bool] = None
    source_quote: str


class TransitionRequirement(BaseModel):
    """Transition/phase-in requirements"""
    phase: str
    duration: Optional[str] = None
    responsibilities: List[str] = Field(default_factory=list)
    milestones: List[str] = Field(default_factory=list)
    source_quote: str


class SectionHSchema(BaseModel):
    """Complete Section H extraction schema"""
    key_personnel: List[KeyPersonnel] = Field(default_factory=list)
    security_requirements: Optional[SecurityRequirements] = None
    transition_requirements: List[TransitionRequirement] = Field(default_factory=list)
    workforce_requirements: Dict[str, Any] = Field(
        default_factory=dict,
        description="SCA, incumbent, compensation requirements"
    )
    special_clauses: List[Dict[str, str]] = Field(
        default_factory=list,
        description="Special contract clauses with impact"
    )


# ============================================================================
# SOW/PWS - Statement of Work
# ============================================================================

class Deliverable(BaseExtractedItem):
    """Individual deliverable"""
    deliverable_id: Optional[str] = None
    description: str
    due_date: Optional[str] = None
    acceptance_criteria: Optional[str] = None
    format: Optional[str] = None


class PerformanceStandard(BaseExtractedItem):
    """Performance standard or SLA"""
    metric: str
    target: Optional[str] = None
    measurement_method: Optional[str] = None
    surveillance: Optional[str] = None


class SOWSchema(BaseModel):
    """Complete SOW/PWS extraction schema"""
    scope_summary: Dict[str, List[str]] = Field(
        default_factory=lambda: {"in_scope": [], "out_of_scope": [], "assumptions": []},
        description="Scope boundaries"
    )
    work_breakdown: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Work breakdown structure"
    )
    deliverables: List[Deliverable] = Field(default_factory=list)
    performance_standards: List[PerformanceStandard] = Field(default_factory=list)
    execution_requirements: Dict[str, Any] = Field(
        default_factory=dict,
        description="Place of performance, period, personnel, equipment"
    )
    compliance_risks: List[str] = Field(default_factory=list)


# ============================================================================
# Section B - Pricing
# ============================================================================

class CLINItem(BaseExtractedItem):
    """Contract Line Item Number"""
    clin: str
    description: str
    quantity: Optional[str] = None
    unit: Optional[str] = None
    unit_price_required: bool = False
    total_price_required: bool = False
    contract_type: Optional[str] = Field(
        None,
        description="FFP, T&M, CPFF, LH, etc."
    )
    period_of_performance: Optional[str] = None


class PeriodOfPerformance(BaseModel):
    """Period of performance breakdown"""
    base_period: Optional[str] = None
    option_periods: List[str] = Field(default_factory=list)
    total_potential: Optional[str] = None
    source_quote: str


class SectionBSchema(BaseModel):
    """Complete Section B extraction schema"""
    clin_structure: List[CLINItem] = Field(default_factory=list)
    period_of_performance: Optional[PeriodOfPerformance] = None
    pricing_instructions: Dict[str, Any] = Field(
        default_factory=dict,
        description="BOE requirements, labor categories, escalation"
    )
    contract_value: Optional[Dict[str, str]] = Field(
        None,
        description="Estimated or ceiling value"
    )


# ============================================================================
# Section I - Contract Clauses
# ============================================================================

class ContractClause(BaseExtractedItem):
    """Individual contract clause"""
    clause_number: str
    title: str
    clause_type: Literal["mandatory", "optional", "flow-down"] = "mandatory"
    compliance_requirement: Optional[str] = None
    far_reference: Optional[str] = None


class SectionISchema(BaseModel):
    """Complete Section I extraction schema"""
    clauses: List[ContractClause] = Field(default_factory=list)
    compliance_summary: Optional[str] = None
    high_risk_clauses: List[str] = Field(
        default_factory=list,
        description="Clauses requiring special attention"
    )


# ============================================================================
# Section K - Representations and Certifications
# ============================================================================

class Representation(BaseExtractedItem):
    """Individual representation or certification"""
    representation_id: Optional[str] = None
    title: str
    requirement: str
    certification_required: bool = False
    annual_representation: bool = False


class SectionKSchema(BaseModel):
    """Complete Section K extraction schema"""
    representations: List[Representation] = Field(default_factory=list)
    sam_registration_required: bool = True
    small_business_certifications: List[str] = Field(default_factory=list)
    compliance_notes: List[str] = Field(default_factory=list)


# ============================================================================
# CDRL - Contract Data Requirements List
# ============================================================================

class CDRLItem(BaseExtractedItem):
    """Individual CDRL deliverable (DD Form 1423)"""
    cdrl_number: str
    did_number: Optional[str] = None
    title: str
    frequency: Optional[str] = Field(
        None,
        description="ONE TIME, MONTHLY, WEEKLY, QUARTERLY, etc."
    )
    first_submission: Optional[str] = None
    submission_frequency: Optional[str] = None
    copies: Dict[str, int] = Field(
        default_factory=lambda: {"hard": 0, "electronic": 1}
    )
    distribution: List[str] = Field(default_factory=list)
    format: Optional[str] = None
    sow_reference: Optional[str] = None


class CDRLSchema(BaseModel):
    """Complete CDRL extraction schema"""
    deliverables: List[CDRLItem] = Field(default_factory=list)
    submission_instructions: Optional[str] = None
    approval_process: Optional[str] = None


# ============================================================================
# Complete Extraction Result
# ============================================================================

class DocumentExtractionResult(BaseModel):
    """Complete extraction result from all documents"""
    section_l: Optional[SectionLSchema] = None
    section_m: Optional[SectionMSchema] = None
    section_h: Optional[SectionHSchema] = None
    sow: Optional[SOWSchema] = None
    section_b: Optional[SectionBSchema] = None
    section_i: Optional[SectionISchema] = None
    section_k: Optional[SectionKSchema] = None
    cdrl: Optional[CDRLSchema] = None
    source_documents: List[SourceDocument] = Field(default_factory=list)
    extraction_timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "section_l": {
                    "formatting": {
                        "font": "Arial 12pt",
                        "margins": "1 inch all sides",
                        "source_quote": "All proposals shall use Arial 12pt font..."
                    }
                },
                "source_documents": [
                    {
                        "filename": "Section_L.pdf",
                        "document_type": "section_l",
                        "section": "section_l"
                    }
                ]
            }
        }
