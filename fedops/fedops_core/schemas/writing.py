from pydantic import BaseModel, Field
from typing import List, Optional
from fedops_core.schemas.analysis import RegulatoryReference

class ProposalSection(BaseModel):
    """Single section of government proposal response"""
    section_title: str = Field(..., description="Section heading")
    requirement_reference: Optional[str] = Field(None, description="RFP requirement number/reference")
    body: str = Field(..., description="Proposal section body (2000-3000 words typical)")
    key_differentiators: List[str] = Field(default_factory=list, description="Competitive advantages highlighted")
    past_performance_examples: List[str] = Field(default_factory=list, description="Relevant past performance")
    compliance_statements: List[str] = Field(default_factory=list, description="Specific compliance claims")
    success_metrics: List[str] = Field(default_factory=list, description="How success will be measured")
    tone: str = Field("professional", description="Tone: professional, confident, innovative, technical")
    readability_score: float = Field(0.85, ge=0.0, le=1.0, description="Readability assessment")

class ContractSummary(BaseModel):
    """Concise summary of contract for proposal context"""
    summary_type: str = Field(..., description="Type: executive, technical, compliance, risk")
    word_count: int = Field(..., ge=50, le=5000, description="Summary length in words")
    
    # Content sections
    scope_of_work: str = Field(..., description="What work is required")
    key_compliance_obligations: List[str] = Field(..., description="Top 5-7 compliance requirements")
    pricing_and_payment: Optional[str] = Field(None, description="Pricing structure and payment terms")
    performance_schedule: Optional[str] = Field(None, description="Key milestones and timeline")
    risk_summary: Optional[str] = Field(None, description="Key risks and considerations")
    
    # For proposal response
    capability_gaps: List[str] = Field(default_factory=list, description="Where does GEDSIO need to grow?")
    recommended_approach: str = Field(..., description="Recommended technical approach")
    resource_requirements: Optional[str] = Field(None, description="Staffing/resource needs")
    
    # Quality
    summary_confidence: float = Field(0.90, ge=0.0, le=1.0, description="Confidence in summary accuracy")

class ReferenceExtraction(BaseModel):
    """Complete verbose reference extraction"""
    reference_type: str = Field(..., description="Category of reference")
    
    # FAR References
    far_citations: List[RegulatoryReference] = Field(default_factory=list, description="FAR 48 CFR citations")
    
    # DFARS References
    dfars_citations: List[RegulatoryReference] = Field(default_factory=list, description="DFARS 252.XXX citations")
    
    # Standards
    iso_standards: List[RegulatoryReference] = Field(default_factory=list, description="ISO standards referenced")
    nist_standards: List[RegulatoryReference] = Field(default_factory=list, description="NIST standards referenced")
    industry_standards: List[RegulatoryReference] = Field(default_factory=list, description="Other industry standards")
    
    # External documents
    external_documents: List[RegulatoryReference] = Field(default_factory=list, description="External docs referenced")
    appendix_references: List[RegulatoryReference] = Field(default_factory=list, description="Appendices/exhibits referenced")
    
    # Internal cross-refs
    internal_cross_references: List[RegulatoryReference] = Field(default_factory=list, description="Internal document refs")
    
    # Summary
    total_references_found: int = Field(..., description="Total unique references")
    critical_references: List[str] = Field(default_factory=list, description="Must-follow references")
    optional_references: List[str] = Field(default_factory=list, description="Nice-to-have references")
    
    # For compliance
    regulatory_framework: str = Field(..., description="Overall framework: FAR/DFARS/Commercial/Hybrid")
    compliance_complexity: str = Field(..., description="Complexity assessment: Low/Medium/High/Very High")
