from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class ComplianceRequirement(BaseModel):
    """Single compliance requirement extracted from contract"""
    requirement_id: str = Field(..., description="Unique requirement ID (REQ_001, etc.)")
    requirement_text: str = Field(..., description="Compliance requirement statement")
    category: str = Field(..., description="Category (security, reporting, audit, personnel, etc.)")
    severity: str = Field(..., description="Severity level: CRITICAL, HIGH, MEDIUM, LOW")
    applicable_to: List[str] = Field(..., description="What this applies to (vendor, contractor, subcontractor, etc.)")
    regulatory_framework: str = Field(..., description="Governing framework (FAR, DFARS, NIST, ISO, etc.)")
    remediation_notes: Optional[str] = Field(None, description="How to meet this requirement")
    estimated_effort: Optional[str] = Field(None, description="Effort to implement (low/medium/high)")
    page_reference: int = Field(..., description="Page number where requirement appears")
    direct_quote: Optional[str] = Field(None, description="Exact text from contract (if available)")
    confidence: float = Field(0.90, ge=0.0, le=1.0, description="Confidence in extraction")

class RegulatoryReference(BaseModel):
    """Single regulatory/standards reference found in document"""
    reference_type: str = Field(..., description="Type: FAR, DFARS, NIST, ISO, STANDARD, EXTERNAL_DOC, etc.")
    citation: str = Field(..., description="Full citation (e.g., '48 CFR 52.204-21')")
    title: Optional[str] = Field(None, description="Reference title/name")
    description: Optional[str] = Field(None, description="What this reference covers")
    context: Optional[str] = Field(None, description="Surrounding text for context")
    page_number: int = Field(..., description="Where reference appears")
    is_requirement: bool = Field(False, description="Does this impose a requirement?")
    impact_level: str = Field(..., description="Impact: CRITICAL, HIGH, MEDIUM, LOW")

class ContractMetadata(BaseModel):
    """High-level contract metadata"""
    contract_number: Optional[str] = Field(None, description="Official contract number")
    contract_type: str = Field(..., description="Type: Fixed-Price, Time-Materials, Cost-Plus, Labor-Hour, etc.")
    parties: List[str] = Field(..., description="Contracting parties (government agency, contractor names)")
    contract_value: Optional[float] = Field(None, description="Total contract value (USD)")
    performance_start_date: Optional[str] = Field(None, description="Period of performance start (YYYY-MM-DD)")
    performance_end_date: Optional[str] = Field(None, description="Period of performance end (YYYY-MM-DD)")
    primary_naics_code: Optional[str] = Field(None, description="Primary NAICS code if present")
    small_business_set_aside: Optional[bool] = Field(None, description="Is this a small business set-aside?")
    vehicle: Optional[str] = Field(None, description="Contract vehicle (GSA MAS, IDIQ, BPA, etc.)")
    payment_terms: Optional[str] = Field(None, description="Payment schedule (Net 30, milestone-based, etc.)")
    key_deliverables: List[str] = Field(default_factory=list, description="Main deliverables")
    termination_conditions: Optional[str] = Field(None, description="Termination for convenience/cause terms")

class RiskAssessment(BaseModel):
    """Risk assessment for contract/document"""
    risk_id: str = Field(..., description="Unique risk identifier (RISK_001, etc.)")
    title: str = Field(..., description="Risk title")
    description: str = Field(..., description="Detailed risk description")
    category: str = Field(..., description="Category: Compliance, Financial, Operational, Legal, Security, Reputational")
    likelihood: str = Field(..., description="Likelihood: Low, Medium, High, Critical")
    impact: str = Field(..., description="Impact if risk occurs: Low, Medium, High, Critical")
    risk_score: float = Field(..., ge=0.0, le=10.0, description="Calculated risk score (0-10)")
    mitigation_strategy: Optional[str] = Field(None, description="How to mitigate this risk")
    responsible_party: Optional[str] = Field(None, description="Who is responsible for managing this risk?")
    related_requirements: List[str] = Field(default_factory=list, description="Related requirement IDs")
    page_reference: Optional[int] = Field(None, description="Where in document this appears")

class DocumentAnalysis(BaseModel):
    """Complete analysis output (from ANALYSIS LAYER)"""
    document_id: str = Field(..., description="Reference to original document")
    analysis_timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Core findings
    contract_metadata: Optional[ContractMetadata] = Field(None, description="Contract-specific metadata")
    compliance_requirements: List[ComplianceRequirement] = Field(..., description="All compliance requirements")
    regulatory_references: List[RegulatoryReference] = Field(..., description="All regulatory/standards references")
    risks: List[RiskAssessment] = Field(..., description="Identified risks")
    
    # Summaries
    executive_summary: str = Field(..., description="300-500 word executive summary")
    key_findings: List[str] = Field(..., description="3-5 most important findings")
    critical_gaps: List[str] = Field(default_factory=list, description="Missing critical compliance areas")
    
    # Scoring
    overall_complexity: str = Field(..., description="Assessment: Simple, Moderate, Complex, Very Complex")
    compliance_readiness: int = Field(..., ge=0, le=100, description="Current compliance readiness (0-100)")
    implementation_effort: str = Field(..., description="Overall effort: Low, Medium, High, Very High")
    
    # Quality
    analysis_confidence: float = Field(0.90, ge=0.0, le=1.0, description="Analyst confidence (0-1)")
    requires_human_review: bool = Field(False, description="Flag for manual review?")
    review_notes: Optional[str] = Field(None, description="Analyst notes for manual review")

class BidDecisionSummary(BaseModel):
    """
    Summary for Bid/No-Bid Decision Matrix
    Mapped to standard RFP Sections (A, B, C, L, M)
    """
    # 1. KNOCK-OUT CRITERIA
    solicitation_number: str = Field(..., description="Solicitation ID")
    proposal_due_date: str = Field(..., description="YYYY-MM-DD HH:MM Timezone")
    questions_due_date: str = Field(..., description="YYYY-MM-DD")
    set_aside: str = Field(..., description="Total Small Business, 8(a), Unrestricted, etc.")
    naics_code: str = Field(..., description="NAICS Code")
    security_clearance: str = Field("None", description="Facility/Personnel Clearance level required")
    mandatory_certs: List[str] = Field(default_factory=list, description="CMMC, ISO, CMMI requirements")

    # 2. FIT CRITERIA
    summary_scope: str = Field(..., description="3-bullet summary of the PWS/SOW")
    tech_stack: List[str] = Field(default_factory=list, description="Required technologies/languages")
    place_of_performance: str = Field(..., description="Remote, On-site, Hybrid, Specific Location")
    key_personnel_roles: List[str] = Field(default_factory=list, description="Required Key Personnel titles")

    # 3. WIN CRITERIA
    evaluation_method: str = Field(..., description="LPTA, Best Value, Highest Rated, etc.")
    incumbent_info: Optional[str] = Field(None, description="Name of incumbent if found")
    contract_type: str = Field(..., description="FFP, T&M, Cost-Plus")
    estimated_value: Optional[str] = Field(None, description="Rough order of magnitude or ceiling")
    
    # 4. EFFORT CRITERIA
    proposal_complexity: str = Field(..., description="Low, Medium, High based on page count/volumes")
    page_limit_tech: int = Field(..., description="Page limit for Technical Volume")
    
    # 5. AI RECOMMENDATION
    ai_bid_recommendation: str = Field(..., description="BID, NO-BID, or MAYBE")
    recommendation_reasoning: str = Field(..., description="Brief rationale based on GEDSIO profile")

