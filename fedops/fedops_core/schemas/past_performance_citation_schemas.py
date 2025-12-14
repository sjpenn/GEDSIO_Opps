"""
Pydantic schemas for Past Performance Citation Generation
Implements comprehensive citation structure for federal proposal submissions
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime, date


class ContractIdentifiers(BaseModel):
    """Contract identification and customer information"""
    contract_number: str
    task_order_number: Optional[str] = None
    vehicle_name: Optional[str] = None
    prime_or_sub: Literal["PRIME", "SUB"]
    customer_name: str
    customer_type: Literal["CIVILIAN", "DOD", "INTEL", "STATE_LOCAL", "COMMERCIAL", "OTHER"]
    naics: Optional[str] = None
    psc: Optional[str] = None


class PeriodAndValue(BaseModel):
    """Contract period of performance and financial details"""
    period_of_performance_start: str  # YYYY-MM-DD
    period_of_performance_end: str  # YYYY-MM-DD or "ONGOING"
    is_within_recency_window: bool
    base_years: int
    option_years: int
    total_contract_value: float
    total_value_units: Literal["USD", "OTHER"] = "USD"
    total_obligated_value: Optional[float] = None


class CustomerPOC(BaseModel):
    """Customer point of contact information"""
    name: str
    role: str = Field(..., description="e.g., COR, CO, Technical POC")
    organization: str
    email: str
    phone: str


class SizeAndComplexityIndicators(BaseModel):
    """Indicators of project size and complexity"""
    fte_count: Optional[int] = None
    locations_count: Optional[int] = None
    users_supported: Optional[int] = None
    data_or_transaction_volume: Optional[str] = None


class SolicitationTaskMapping(BaseModel):
    """Mapping to specific solicitation tasks"""
    solicitation_task_label: str = Field(..., description="e.g., Task 2 – Cloud Migration")
    description_of_alignment: str


class ScopeAndRelevance(BaseModel):
    """Project scope and relevance to solicitation"""
    summary_mission_context: str
    core_services_and_tasks: List[str]
    key_technologies_and_tools: List[str]
    size_and_complexity_indicators: SizeAndComplexityIndicators
    mapped_to_solicitation_tasks: List[SolicitationTaskMapping]


class PerformanceMetric(BaseModel):
    """Individual performance metric"""
    name: str
    value: str
    better_direction: Literal["HIGHER_IS_BETTER", "LOWER_IS_BETTER"]


class PerformanceCategory(BaseModel):
    """Performance category with narrative and metrics"""
    narrative: str
    metrics: List[PerformanceMetric]


class CPARSSummary(BaseModel):
    """CPARS or PPQ ratings summary"""
    cpars_rating_quality: Optional[str] = None
    cpars_rating_schedule: Optional[str] = None
    cpars_rating_cost_control: Optional[str] = None
    cpars_rating_management: Optional[str] = None
    overall_assessment_excerpt: Optional[str] = None


class ManagementAndBusinessRelations(BaseModel):
    """Management and business relations performance"""
    narrative: str
    highlights: List[str]


class PerformanceResults(BaseModel):
    """Comprehensive performance results"""
    quality: PerformanceCategory
    schedule: PerformanceCategory
    cost_control: PerformanceCategory
    management_and_business_relations: ManagementAndBusinessRelations
    cpars_or_ppq_summary: CPARSSummary


class ChallengesAndRiskMitigation(BaseModel):
    """Challenges faced and risk mitigation strategies"""
    key_challenges: List[str]
    mitigation_actions: List[str]
    outcomes: List[str]


class EvaluationFactorLink(BaseModel):
    """Link to specific evaluation factor"""
    factor_name: str = Field(..., description="e.g., Past Performance – Relevance")
    how_this_citation_supports_factor: str


class TailoredNarrative(BaseModel):
    """Tailored narrative for the solicitation"""
    executive_summary: str = Field(..., description="2–4 sentence summary tailored to this solicitation")
    detailed_writeup: str = Field(..., description="multi-paragraph narrative, max ~400 words, written as proposal-ready text")
    explicit_links_to_evaluation_factors: List[EvaluationFactorLink]


class PastPerformanceCitation(BaseModel):
    """Complete past performance citation"""
    citation_id: str
    overall_relevance_level: Literal["VERY_RELEVANT", "RELEVANT", "SOMEWHAT_RELEVANT", "NOT_RELEVANT"]
    source_project_id: str
    
    contract_identifiers: ContractIdentifiers
    period_and_value: PeriodAndValue
    customer_points_of_contact: List[CustomerPOC]
    scope_and_relevance: ScopeAndRelevance
    performance_results: PerformanceResults
    challenges_and_risk_mitigation: ChallengesAndRiskMitigation
    tailored_narrative: TailoredNarrative


class SolicitationMeta(BaseModel):
    """Solicitation metadata"""
    agency_name: str
    solicitation_id: str
    title: str
    section_l_focus: str
    section_m_factors: List[str]


class CitationGenerationRequest(BaseModel):
    """Request to generate past performance citations"""
    solicitation_section_l: str = Field(..., description="Section L instructions text")
    solicitation_section_m: str = Field(..., description="Section M evaluation factors text")
    solicitation_sow_pws: str = Field(..., description="SOW/PWS text")
    agency_name: str
    solicitation_id: Optional[str] = None
    solicitation_title: Optional[str] = None
    required_number_of_citations: int = Field(3, description="Number of citations to generate")
    internal_project_summaries: Optional[str] = Field(None, description="JSON string of internal project data")


class CitationGenerationResponse(BaseModel):
    """Response with generated citations"""
    solicitation_meta: SolicitationMeta
    citations: List[PastPerformanceCitation]
    generated_at: datetime
    model_used: str


class CitationUpdateRequest(BaseModel):
    """Request to update a specific citation"""
    citation_data: Dict[str, Any]


class CitationExportRequest(BaseModel):
    """Request to export citations"""
    format: Literal["json", "word", "markdown"] = "json"
    include_metadata: bool = True
    citation_ids: Optional[List[str]] = Field(None, description="Specific citations to export, or all if None")
