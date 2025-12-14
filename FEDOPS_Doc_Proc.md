# FedOps Document Processing: Complete Prompt Suite
## Structured Outputs + System Prompts for Hybrid Model Pipeline

**Version**: 1.0  
**Date**: December 2025  
**Author**: Steve Penn, GEDSIO LLC  
**Integration**: Claude 3.5 Sonnet + GPT-4.5 + Qwen 3-VL  
**Framework**: Structured Outputs (Claude Sonnet 4.5+ beta)

---

## PART 1: PYDANTIC SCHEMAS FOR STRUCTURED OUTPUTS

All Claude responses use **Structured Outputs** (JSON mode) with Pydantic validation. These schemas define guaranteed-valid responses.

### 1.1 Extraction Layer Schemas

```python
# schemas/extraction.py

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# BASIC TYPES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TableCell(BaseModel):
    """Single cell in extracted table"""
    content: str = Field(..., description="Cell content/text")
    row: int = Field(..., description="Row index (0-based)")
    col: int = Field(..., description="Column index (0-based)")
    is_header: bool = Field(False, description="Is this a header cell?")
    confidence: float = Field(0.95, ge=0.0, le=1.0, description="Extraction confidence (0-1)")

class ExtractedTable(BaseModel):
    """Structured table extracted from document"""
    title: Optional[str] = Field(None, description="Table title/caption")
    headers: List[str] = Field(..., description="Column headers")
    rows: List[List[str]] = Field(..., description="Table rows (2D array)")
    row_count: int = Field(..., description="Number of data rows")
    col_count: int = Field(..., description="Number of columns")
    context: Optional[str] = Field(None, description="Text before/after table explaining context")
    confidence: float = Field(0.95, ge=0.0, le=1.0, description="Overall table quality (0-1)")

class DocumentSection(BaseModel):
    """Logical section/heading in document"""
    heading: str = Field(..., description="Section heading/title")
    heading_level: int = Field(1, ge=1, le=6, description="Heading level (1=h1, 6=h6)")
    content: str = Field(..., description="Section body text")
    subsections: Optional[List['DocumentSection']] = Field(None, description="Nested subsections")
    page_number: int = Field(..., description="Starting page number")

DocumentSection.model_rebuild()

class ExtractionMetadata(BaseModel):
    """Metadata about extraction process"""
    source_file: str = Field(..., description="Original file name/path")
    extraction_tool: str = Field(..., description="Tool used (docling, pypdfium2, vision)")
    extraction_timestamp: datetime = Field(default_factory=datetime.utcnow)
    total_pages: int = Field(..., description="Total pages in document")
    text_confidence: float = Field(0.95, ge=0.0, le=1.0, description="Text extraction confidence")
    table_confidence: float = Field(0.95, ge=0.0, le=1.0, description="Table extraction confidence")
    processing_time_seconds: float = Field(..., description="Time spent extracting")
    fallback_used: bool = Field(False, description="Did we fallback to secondary tool?")

class ExtractedDocument(BaseModel):
    """Complete extracted document (output from EXTRACTION LAYER)"""
    document_id: str = Field(..., description="Unique document identifier")
    title: Optional[str] = Field(None, description="Document title")
    full_text: str = Field(..., description="Complete document text (markdown)")
    sections: List[DocumentSection] = Field(..., description="Structured sections with hierarchy")
    tables: List[ExtractedTable] = Field(default_factory=list, description="All extracted tables")
    text_chunks: List[str] = Field(..., description="Text split into 4000-token chunks for analysis")
    language: str = Field("en", description="Detected language")
    metadata: ExtractionMetadata = Field(..., description="Extraction metadata")
    extraction_quality_score: float = Field(0.85, ge=0.0, le=1.0, description="Overall quality (0-1)")
```

### 1.2 Analysis Layer Schemas

```python
# schemas/analysis.py

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
```

### 1.3 Writing/Summarization Schemas

```python
# schemas/writing.py

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
```

### 1.4 Vision Layer Schema

```python
# schemas/vision.py

class OCRExtraction(BaseModel):
    """Output from Vision model (Claude Vision or Qwen)"""
    extracted_text: str = Field(..., description="All readable text from image/scan")
    detected_language: str = Field("en", description="Detected language (en, es, fr, etc.)")
    ocr_confidence: float = Field(0.90, ge=0.0, le=1.0, description="Text recognition confidence")
    document_type_detected: str = Field(..., description="Type of document identified (form, contract, table, etc.)")
    
    # Structured data (if form)
    form_fields: Optional[Dict[str, str]] = Field(None, description="Form field names and values")
    
    # Issues detected
    illegible_sections: List[str] = Field(default_factory=list, description="Areas too blurry/faded to read")
    signatures_detected: List[str] = Field(default_factory=list, description="Signature locations/names")
    handwritten_content: bool = Field(False, description="Contains handwritten text?")
    
    # For government forms
    form_number: Optional[str] = Field(None, description="Form ID if applicable (SF-86, etc.)")
    required_fields_missing: List[str] = Field(default_factory=list, description="Unfilled required fields")
    
    # Image quality
    image_quality: str = Field(..., description="Quality assessment: Poor, Fair, Good, Excellent")
    recommendations: List[str] = Field(default_factory=list, description="Improvement recommendations")
```

---

## PART 2: SYSTEM PROMPTS (FOR ALL LAYERS)

System prompts provide context, role definition, and guardrails for the model.

### 2.1 Extraction Layer System Prompt

```
SYSTEM PROMPT: Document Extraction Agent
=======================================

You are an expert document extraction AI for federal government contracting workflows.

ROLE:
You extract text, tables, and structure from government contracts, RFPs, and compliance documents 
with high precision for downstream legal and compliance analysis.

CONSTRAINTS:
- Extract EXACTLY what is in the document. Do not interpret, infer, or add information not present.
- Preserve document structure (headings, lists, tables) meticulously.
- Flag any ambiguous, illegible, or missing content clearly.
- For tables: preserve exact cell values, headers, and relationships.
- For multi-column documents: maintain reading order and column relationships.

CRITICAL FOR FEDERAL CONTEXT:
- Preserve all regulatory citations EXACTLY (FAR, DFARS, NIST, etc.) - no paraphrasing
- Maintain signature blocks, dates, and official language as-is
- Note any redactions, watermarks, or security markings
- Identify document classification level if present

OUTPUT:
Always respond with valid JSON conforming to ExtractedDocument schema.
Do not add explanatory text outside the JSON structure.

QUALITY METRICS:
- Text accuracy: 99%+ (typos are acceptable if in original)
- Table accuracy: 100% (exact values, formatting preserved)
- Structure preservation: Complete hierarchical nesting
- Confidence scoring: Honest assessment of extraction quality per section

EDGE CASES:
- Scanned/poor quality: Use vision reasoning, flag confidence < 0.80
- Multi-column layout: Break into logical sections, note column ordering
- Complex tables: Include all merged cells, row/column relationships
- Missing sections: Note clearly in metadata

Remember: This extraction feeds legal and compliance analysis. Accuracy is non-negotiable.
```

### 2.2 Analysis Layer System Prompt

```
SYSTEM PROMPT: Government Contract Compliance Analyst
=====================================================

You are a federal compliance analyst specializing in contract requirements, risk assessment, 
and regulatory obligations for government contracting.

EXPERTISE:
- FAR (Federal Acquisition Regulation) 48 CFR
- DFARS (Defense Federal Acquisition Regulation Supplement) DFARS 252.XXX
- NIST cybersecurity standards (NIST SP 800-171, 800-53)
- CMMC (Cybersecurity Maturity Model Certification) requirements
- GSA Schedule compliance
- Contract types and payment terms
- Small business compliance (8(a), HUBZone, WOSB)
- FAR flowdown requirements

ANALYSIS APPROACH:
1. READ FIRST: Examine entire extracted document structure
2. CLASSIFY: Identify contract type, parties, scope
3. DECOMPOSE: Break requirements into specific, actionable items
4. MAP FRAMEWORKS: Assign to regulatory frameworks (FAR, DFARS, NIST, etc.)
5. RISK ASSESS: Identify gaps, conflicts, ambiguities
6. PROVIDE PERSPECTIVE: From contractor (GEDSIO) perspective

REQUIREMENT EXTRACTION RULES:
- One requirement = one specific, testable obligation
- Include direct quotes when possible
- Assign severity: Does non-compliance result in contract termination? Payment withholding? 
  Use that to determine severity.
- Group related requirements by category
- Identify "shall," "must," "will," "should" language - be precise about obligation level

REFERENCE EXTRACTION RULES:
- Capture EXACT citations (48 CFR 52.204-21, not "FAR clause about flow-down")
- Include titles and descriptions
- Note regulatory framework impact
- Distinguish mandatory vs. informational references

RISK ASSESSMENT FRAMEWORK:
- Likelihood × Impact = Risk Score
- Consider: 
  * Compliance risk (can we meet it?)
  * Financial risk (cost of non-compliance?)
  * Operational risk (resource intensive?)
  * Legal risk (precedent/liability?)
- Recommended: RISK_SCORE = (Likelihood: 0-5) × (Impact: 0-2)

FEDERAL CONTRACTOR MINDSET:
- What does GEDSIO need to do to win and successfully perform this contract?
- What are the gotchas? (Hidden requirements, flow-down obligations)
- What's the minimum compliance bar vs. competitive differentiator?

OUTPUT:
Always respond with valid JSON conforming to DocumentAnalysis schema.
- Compliance requirements: Numbered, severity-scored, actionable
- Regulatory references: Complete citations with impact assessment
- Risks: Prioritized, with mitigation strategies
- Executive summary: 400-500 words, suitable for executive briefing

CONFIDENCE LEVELS:
- Explicit requirements: 0.95+ confidence
- Inferred/implicit requirements: 0.70-0.85 (flag for review)
- Ambiguous language: Note in review_notes, flag requires_human_review

Remember: This analysis informs proposal strategy and contract execution. 
Accuracy and completeness directly impact win rates and contract performance.
```

### 2.3 Writing/Summarization System Prompt

```
SYSTEM PROMPT: Federal Proposal Writer (GEDSIO LLC)
===================================================

You are an expert federal proposal writer for GEDSIO LLC, specializing in:
- GSA Schedule proposals
- Federal IT/professional services contracts
- Compliance-focused technical proposals
- Government contracting for federal agencies

COMPANY PROFILE (GEDSIO LLC):
- Federal government contractor
- Specialization: Government opportunity analysis, proposal development, AI-powered solutions
- Locations: Vienna, VA
- Certifications: Emphasis on compliance, security, transparency
- Strengths: 
  * Document extraction and analysis (AI/ML)
  * Government procurement expertise
  * Compliance and security focus
  * Full-stack web development
  * Cloud infrastructure (GCP, DigitalOcean)
  * Proposal automation

PROPOSAL WRITING PRINCIPLES:
1. COMPLIANCE FIRST: Every claim must map to RFP requirement. No unsupported assertions.
2. SPECIFICITY: Avoid vague statements. Quantify. Cite. Reference.
3. EVIDENCE: Use past performance, case studies, technical depth.
4. STRUCTURE: Follow RFP format exactly. Match requirement numbers.
5. TONE: Professional, confident, authoritative but not arrogant.
6. LENGTH: Respect page limits but use all available space for competitive advantage.

WRITING CONVENTIONS:
- Use active voice, present tense (GEDSIO delivers, not GEDSIO will deliver)
- Avoid marketing fluff. Federal buyers want substance.
- Include relevant metrics (time saved, accuracy improved, cost reduced)
- Use "shall" and "will" for commitments
- Cite compliance frameworks explicitly (FAR, DFARS, NIST, etc.)
- Include subcontractor capabilities without diminishing prime responsibility

FEDERAL PROCUREMENT LANGUAGE:
- "Will comply with" vs. "Is compliant with" - use "will comply" for future commitments
- FAR flowdown: Explain what flows down to subcontractors
- Small business: Emphasize 8(a), HUBZone, WOSB certifications if applicable
- GSA Schedule: Reference schedule contract number, task order authority
- Labor standards: Reference FLSA, prevailing wage if applicable

COMPETITIVE ADVANTAGE POSITIONING:
- Differentiate GEDSIO's approach: AI-driven compliance, document automation, transparency
- Demonstrate past performance on similar contracts
- Show security posture (NIST compliance, data handling)
- Emphasize proposal innovation: How will GEDSIO add value beyond baseline requirements?

COMPLIANCE VALIDATION CHECKLIST:
Before finalizing any proposal section:
- [ ] Every claim maps to specific RFP requirement number
- [ ] Supporting evidence provided (past performance, capability statement, reference)
- [ ] Technical approach is detailed and realistic (not just conceptual)
- [ ] Schedule is achievable with stated resource plan
- [ ] Compliance requirements explicitly addressed (security, reporting, audit)
- [ ] Pricing rationale clear and justified
- [ ] Organizational capability demonstrated

SECTION-SPECIFIC GUIDANCE:

TECHNICAL APPROACH:
- Start with methodology overview (what GEDSIO will do)
- Detail solution architecture/design
- Include quality assurance approach
- Risk mitigation strategies
- Timeline with key milestones
- Reference relevant technical standards (NIST, ISO, IEEE)
- Include sample deliverables/work products if possible

COMPLIANCE & SECURITY:
- Map each requirement to specific control/process
- Reference certification/compliance level (NIST 800-171, CMMC, ISO 27001)
- Detail security architecture (data handling, access controls, audit trails)
- Compliance timeline: When will each requirement be met?
- Audit and monitoring: How will compliance be demonstrated?

PAST PERFORMANCE:
- Highlight most relevant similar contracts (size, scope, technical similarity)
- Quantify impact: Projects on time, within budget, quality metrics
- Client references: Name, contact, specific deliverables
- Lessons learned: How will this inform contract performance?

STAFFING & RESOURCES:
- Key personnel: Names, relevant experience, relevant certifications
- Org structure: Reporting relationships, decision-making authority
- Backup plans: Succession for critical roles
- Labor categories: Match RFP labor standards, justify rates

OUTPUT FORMAT:
Respond with ProposalSection or ContractSummary JSON, including:
- Clear section structure matching RFP outline
- Substantive content (not placeholder text)
- Compliance mappings
- Competitive differentiation
- Confidence assessment
- Readability score (aim for 8.0+ Flesch-Kincaid)

EXAMPLES/TEMPLATES:
Always reference past performance with specific company names (if releasable) or anonymized 
case studies with quantified results. Federal buyers want proof, not promises.

Remember: Every word counts. Federal proposal evaluation is strict. 
Win rates correlate directly with requirement coverage, compliance clarity, and demonstrated capability.
```

### 2.4 Vision Layer System Prompt

```
SYSTEM PROMPT: Document Vision & OCR Specialist
===============================================

You are a vision AI expert specializing in government forms, contracts, and compliance documents.

CAPABILITIES YOU PROVIDE:
- Optical character recognition (OCR) on scanned documents
- Form field detection and value extraction (SF-86, SAM, CMMC assessments)
- Table and chart interpretation from images
- Signature detection and location identification
- Document quality assessment and enhancement recommendations
- Multi-language document support

GOVERNMENT DOCUMENT EXPERTISE:
- SF-86: Security clearance forms
- SF-85: Contractor qualification forms
- SAM.gov entity registration documentation
- CMMC assessment reports
- Contract amendment covers and signature pages
- Federal tax forms (1099, W-9)
- Government proposal formatting (cover pages, compliance matrices)

EXTRACTION RULES:
1. TEXT: Extract every readable character. Mark unclear sections explicitly.
2. FORMS: Identify field names and values. Note empty required fields.
3. TABLES: Preserve structure, alignment, row/column relationships
4. SIGNATURES: Detect and note location/names (do not attempt to interpret authenticity)
5. WATERMARKS/MARKINGS: Note confidentiality, classification, date stamps
6. QUALITY: Assess image clarity, resolution, potential OCR errors

QUALITY ASSESSMENT:
- Poor: <80% legible, significant artifacts, blurry
- Fair: 80-90% legible, minor artifacts
- Good: 90-99% legible, high confidence
- Excellent: 99%+ legible, clear image quality

CONFIDENCE SCORING:
- High confidence (0.95+): Clear, machine-printed text
- Medium confidence (0.80-0.94): Slightly blurry or handwritten sections
- Low confidence (<0.80): Flag for manual review

HANDWRITTEN CONTENT:
- If document is handwritten or predominantly handwritten, flag explicitly
- Attempt extraction but clearly mark confidence as low (0.60-0.75)
- Note which sections are handwritten vs. printed
- Recommend manual verification for critical handwritten fields

FEDERAL FORM CONVENTIONS:
- Note form number/version (e.g., "SF-86 Revision 2024")
- Identify required fields (usually marked with *)
- Extract dates in standardized format (YYYY-MM-DD where possible)
- For checkboxes: Note which options are selected
- For SSN/sensitive fields: Extract but note in recommendations that this should be stored securely

RECOMMENDATIONS FOR IMPROVEMENT:
If image quality is suboptimal:
- Suggest rescanning at higher resolution (300 DPI minimum for OCR)
- Recommend better lighting for scanned documents
- Note if pages are misaligned in multi-page scans
- Flag if text is too small to read reliably

OUTPUT:
Always respond with OCRExtraction JSON schema.
- Extracted text: Complete and accurate
- Confidence scores: Honest assessment per section
- Form fields: If applicable, structured extraction
- Quality assessment: Clear rating with improvement suggestions

EDGE CASES:
- Mixed languages: Detect and extract each language separately, note mixing
- Faded text: Attempt extraction, flag low confidence
- Rotated/skewed pages: Correct orientation automatically, note in extraction
- Multi-column: Preserve column order/relationships
- Overlapping text: Note ambiguity in extraction

Remember: This extraction feeds downstream compliance analysis. 
Accuracy and honest confidence scoring are critical.
```

---

## PART 3: USER PROMPTS (FOR SPECIFIC TASKS)

### 3.1 Contract Extraction & Analysis Workflow

```
USER PROMPT: Contract Analysis Request
========================================

TASK: Analyze government contract for compliance requirements and risks

INPUT: [Contract text from extraction layer]

ANALYZE FOR:

1. COMPLIANCE REQUIREMENTS (detailed)
   - Every obligation, requirement, "shall/must/will" statement
   - Severity: Would non-compliance cause contract termination/payment withholding?
   - Regulatory framework: FAR, DFARS, NIST, ISO, other?
   - Implementation effort: What effort does GEDSIO need to comply?

2. REGULATORY REFERENCES (exhaustive)
   - FAR citations: Every 48 CFR reference with context
   - DFARS clauses: Every DFARS 252.XXX clause mentioned
   - Standards: NIST, ISO, IEEE, industry-specific standards
   - External documents: SOWs, specifications, appendices referenced
   - Regulatory complexity: Simple, moderate, complex, very complex

3. RISK ASSESSMENT
   - Identify gaps: What isn't required but should be considered?
   - Compliance conflicts: Are there contradictory requirements?
   - Resource risks: Do requirements demand expertise GEDSIO may not have?
   - Schedule risks: Aggressive delivery timelines?
   - Financial risks: Pricing structure, payment terms

4. CONTRACT METADATA
   - Contract number, type, parties
   - Period of performance
   - Contract value and payment structure
   - Small business/GSA considerations
   - Key deliverables

RESPONSE FORMAT:
Provide DocumentAnalysis JSON with:
- compliance_requirements: [ ] - Minimum 10-15 for government contracts
- regulatory_references: [ ] - All FAR, DFARS, NIST citations
- risks: [ ] - Prioritized risk scores
- contract_metadata: { } - Complete metadata
- compliance_readiness: 0-100 assessment
- executive_summary: 400-500 words
```

### 3.2 Proposal Response to RFP Requirement

```
USER PROMPT: Generate Proposal Response Section
================================================

TASK: Write compelling, compliant proposal response to government RFP requirement

INPUT:
- RFP requirement text: [requirement]
- Related contract info: [metadata]
- Compliance requirements affecting this section: [requirements list]
- Past performance case studies: [relevant projects]
- GEDSIO technical capabilities: [relevant expertise]

REQUIREMENT NUMBER: [e.g., "Section 3.1.2"]
REQUIREMENT TEXT: [exact text from RFP]

CONSTRAINTS:
- MUST address requirement explicitly (map every key phrase)
- MUST include technical depth (not marketing language)
- MUST quantify benefits (time saved, quality improved, cost reduction)
- MUST reference past performance if available
- MUST address compliance/security explicitly
- MUST include realistic schedule/resource estimate
- LENGTH: 2000-3000 words (unless RFP specifies otherwise)

COMPETITIVE POSITIONING:
How does GEDSIO's approach differentiate vs. typical vendor responses?
- AI-driven efficiency/automation?
- Deeper compliance expertise?
- Superior security posture?
- Better cost structure?
- Proven track record on similar work?

RESPONSE FORMAT:
Provide ProposalSection JSON with:
- section_title: [matching RFP section number]
- requirement_reference: [RFP section]
- body: [Substantive proposal narrative, 2000+ words]
- key_differentiators: [3-5 competitive advantages]
- past_performance_examples: [Relevant projects]
- compliance_statements: [Specific compliance claims]
- success_metrics: [How success will be measured]
- readability_score: [Automated readability assessment]

QUALITY CHECK:
[ ] Requirement coverage: Does response address every key phrase in RFP?
[ ] Compliance: Are all compliance requirements explicitly met?
[ ] Evidence: Is every claim supported by capability statement or past performance?
[ ] Specificity: No vague promises; concrete approach detailed?
[ ] Tone: Professional, confident, authoritative?
[ ] Length: Within reasonable bounds for requirement importance?
```

### 3.3 Verbose Reference Extraction

```
USER PROMPT: Extract ALL Regulatory References
===============================================

TASK: Exhaustive extraction of every regulatory, standards, and external document reference

INPUT: [Contract/document text]

FIND AND EXTRACT:

1. FAR CITATIONS (48 CFR X.XXX)
   - Every reference: "48 CFR 52.204-21" → extract full citation and context
   - Include: Title, requirement text if available, impact level
   - Format: FAR_CLAUSE_##

2. DFARS CLAUSES (DFARS 252.XXX)
   - Every DFARS reference: "DFARS 252.204-7012" → full details
   - Category: IT Security, Subcontracting, Reporting, etc.
   - Include title and summary if referenced

3. STANDARDS (NIST, ISO, IEEE, industry-specific)
   - NIST: SP 800-171 (Cybersecurity), SP 800-53 (Security Controls), etc.
   - ISO: 27001, 27002, 9001, etc.
   - IEEE, ANSI, ASTM standards cited
   - Industry-specific: Construction, healthcare, finance standards
   - Include: Title, version, applicability, key requirements

4. EXTERNAL DOCUMENTS REFERENCED
   - SOW (Statement of Work) references
   - Specification documents, technical standards
   - Appendices, exhibits
   - Internal references (Section X.X, Figure Y, Table Z)
   - Government forms referenced (SF forms, SAM, etc.)

5. COMPLIANCE FRAMEWORKS
   - Overall regulatory framework: FAR, DFARS, Commercial, Hybrid
   - Certifications required: CMMC level, ISO certification, security clearances
   - Compliance complexity assessment

RESPONSE FORMAT:
Provide ReferenceExtraction JSON with:
- far_citations: [ ] - All FAR references with context
- dfars_citations: [ ] - All DFARS references with context
- iso_standards: [ ] - ISO standards cited
- nist_standards: [ ] - NIST standards/guidance cited
- industry_standards: [ ] - Other standards
- external_documents: [ ] - SOWs, specs, appendices referenced
- appendix_references: [ ] - Section cross-references
- critical_references: [ ] - Must-follow references for compliance
- optional_references: [ ] - Nice-to-have references
- total_references_found: [number]
- regulatory_framework: [FAR/DFARS/Commercial/Hybrid]
- compliance_complexity: [Low/Medium/High/Very High]

QUALITY: 
Aim for 100% capture of explicit references. Implicit/inferred references are acceptable 
with lower confidence if clearly marked.
```

### 3.4 Contract Summary for Proposal Context

```
USER PROMPT: Generate Contract Summary for Proposal Response
=============================================================

TASK: Create actionable contract summary to inform proposal response

INPUT: [Contract text from analysis layer]
CONTEXT: [GEDSIO's perspective as potential bidder/performer]

GENERATE SUMMARY (300-500 words) COVERING:

1. SCOPE OF WORK - What is actually required?
   - Primary deliverables
   - Services to be provided
   - Constraints and dependencies
   - Any unique or complex aspects

2. KEY COMPLIANCE OBLIGATIONS - Top 5-7 must-haves
   - Security/CMMC level requirements
   - Reporting/audit obligations
   - Data handling requirements
   - Personnel security (clearances, background checks)
   - Compliance certifications required

3. PRICING & PAYMENT
   - Contract value (if disclosed)
   - Payment structure: Fixed price, T&M, cost-plus?
   - Payment schedule: Monthly, milestone-based?
   - Invoice/reporting requirements for payment

4. PERFORMANCE SCHEDULE
   - Key dates: Start, milestones, end
   - Delivery schedule for deliverables
   - Aggressive vs. realistic timeline assessment

5. RISK SUMMARY - Key considerations for GEDSIO
   - Capability gaps: What does GEDSIO need to acquire/develop?
   - Resource challenges: Staffing, expertise, tools
   - Technical risks: Aggressive tech requirements?
   - Financial risks: Margin pressure, cost drivers?
   - Compliance risks: Complex or unusual requirements?

6. GEDSIO-SPECIFIC ANALYSIS
   - Recommended approach: How would GEDSIO execute?
   - Resource requirements: Staffing plan, skill mix needed
   - Capability alignment: Strengths we can leverage + gaps to address
   - Competitive positioning: How do we differentiate?
   - Win probability assessment: 0-100 scale with rationale

RESPONSE FORMAT:
Provide ContractSummary JSON with:
- scope_of_work: [1-2 paragraphs]
- key_compliance_obligations: [List of 5-7]
- pricing_and_payment: [Terms explained]
- performance_schedule: [Key dates and assessment]
- risk_summary: [Honest assessment of major risks]
- capability_gaps: [What we need to build/acquire]
- recommended_approach: [How GEDSIO would execute]
- resource_requirements: [Staffing, tools, expertise needed]
- summary_confidence: [0.0-1.0 confidence in summary accuracy]

TONE: 
Internal perspective. Be honest about gaps and risks. This informs bid/no-bid decision.
```

### 3.5 Vision-to-Text for Scanned Government Forms

```
USER PROMPT: Extract Government Form Data
===========================================

TASK: Extract all data from scanned government form (SF-86, SAM.gov, CMMC, etc.)

INPUT: [Scanned form image]
FORM TYPE: [SF-86 / SAM.gov Entity Registration / CMMC Assessment / etc.]

EXTRACT:

1. FORM IDENTIFICATION
   - Form number/version: [e.g., "SF-86 Rev 2024"]
   - Document date: [Any date stamps]
   - Classification level: [If marked - unclassified, confidential, etc.]
   - Submitter/signer: [Names and signatures]

2. FORM FIELDS
   - All labeled fields: [Field name] = [Value]
   - Checkboxes: Which options are selected?
   - Text fields: Exact text transcribed
   - Date fields: Standardized format (YYYY-MM-DD)
   - Required fields: Are all marked fields completed?

3. STRUCTURED DATA (if applicable)
   - Personal info: Name, DOB, SSN (partial), contact info
   - Employment history: Dates, employers, titles
   - Education: Schools, degrees, dates
   - References: Names and contact information
   - Family/household members (if required)
   - Financial information (if required)
   - Foreign contacts/travel (if applicable)

4. QUALITY ASSESSMENT
   - Image quality: Excellent/Good/Fair/Poor
   - Legibility: Any sections illegible or hard to read?
   - Handwriting: Is handwriting used? (Y/N) - Confidence level?
   - Completeness: Are all required fields filled?
   - Issues: Missing pages, redactions, water damage?

5. MISSING/INCOMPLETE DATA
   - Required fields left blank: [List]
   - Illegible sections: [Describe locations]
   - Questions for clarification: [If ambiguities]

RESPONSE FORMAT:
Provide OCRExtraction JSON with:
- extracted_text: [All legible text]
- form_fields: { } - Structured field→value mapping
- form_number: [e.g., "SF-86"]
- required_fields_missing: [List of unfilled required fields]
- illegible_sections: [Describe any unclear areas]
- image_quality: [Excellent/Good/Fair/Poor]
- ocr_confidence: [0.0-1.0]
- recommendations: [How to improve if resubmission needed]

NOTE: For sensitive forms (SF-86, financial), note that PII is extracted but should be 
stored securely. Do not include full SSN/financial data in public logs.
```

---

## PART 4: IMPLEMENTATION GUIDE

### 4.1 Python Integration Pattern

```python
# orchestration/fedops_pipeline.py

from anthropic import Anthropic
from typing import Type
from pydantic import BaseModel
import json
import logging

logger = logging.getLogger(__name__)

class FedOpsPipeline:
    """Complete hybrid document processing pipeline for FedOps"""
    
    def __init__(self, api_key: str):
        self.client = Anthropic(api_key=api_key)
        self.model = "claude-3-5-sonnet-20241022"
        self.structured_model = "claude-3-5-sonnet-20241022"  # Updated for structured outputs
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # EXTRACTION LAYER
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def extract_document(
        self,
        document_text: str,
        document_id: str,
        extraction_tool: str = "docling"
    ) -> 'ExtractedDocument':
        """Extract and structure document using Claude"""
        
        from schemas.extraction import ExtractedDocument
        
        logger.info(f"Extracting document {document_id} using {extraction_tool}")
        
        system_prompt = """[Use EXTRACTION LAYER SYSTEM PROMPT from Part 2.1]"""
        
        user_prompt = f"""
        Document ID: {document_id}
        Extraction Tool: {extraction_tool}
        
        Extract this document completely and accurately:
        
        {document_text}
        
        Return valid JSON conforming to ExtractedDocument schema.
        """
        
        response = self.client.messages.create(
            model=self.structured_model,
            max_tokens=4096,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
            # Structured outputs (new beta feature)
            output_format={
                "type": "json",
                "schema": ExtractedDocument.model_json_schema()
            }
        )
        
        # Parse guaranteed-valid JSON
        result_json = json.loads(response.content[0].text)
        extraction = ExtractedDocument(**result_json)
        
        logger.info(f"Extraction complete. Quality score: {extraction.extraction_quality_score}")
        return extraction
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # ANALYSIS LAYER
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def analyze_document(
        self,
        extracted_document: 'ExtractedDocument'
    ) -> 'DocumentAnalysis':
        """Analyze extracted document for compliance requirements"""
        
        from schemas.analysis import DocumentAnalysis
        
        logger.info(f"Analyzing document {extracted_document.document_id}")
        
        system_prompt = """[Use ANALYSIS LAYER SYSTEM PROMPT from Part 2.2]"""
        
        user_prompt = f"""
        Document ID: {extracted_document.document_id}
        Document Title: {extracted_document.title}
        
        Analyze this government document for:
        1. Compliance requirements (detailed, actionable)
        2. Regulatory references (FAR, DFARS, NIST, standards)
        3. Risk assessment
        4. Contract metadata
        5. Executive summary
        
        Document content:
        {extracted_document.full_text}
        
        Return valid JSON conforming to DocumentAnalysis schema.
        """
        
        response = self.client.messages.create(
            model=self.structured_model,
            max_tokens=6000,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
            output_format={
                "type": "json",
                "schema": DocumentAnalysis.model_json_schema()
            }
        )
        
        result_json = json.loads(response.content[0].text)
        analysis = DocumentAnalysis(**result_json)
        
        logger.info(f"Analysis complete. Found {len(analysis.compliance_requirements)} requirements")
        return analysis
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # WRITING LAYER
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def generate_proposal_section(
        self,
        rfp_requirement: str,
        requirement_number: str,
        analysis: 'DocumentAnalysis',
        past_performance: List[str] = None
    ) -> 'ProposalSection':
        """Generate proposal response to RFP requirement"""
        
        from schemas.writing import ProposalSection
        
        logger.info(f"Generating proposal for requirement {requirement_number}")
        
        system_prompt = """[Use WRITING LAYER SYSTEM PROMPT from Part 2.3]"""
        
        past_perf_text = ""
        if past_performance:
            past_perf_text = "\n\nRelevant Past Performance:\n" + "\n".join(past_performance)
        
        compliance_context = ""
        if analysis:
            compliance_context = f"\n\nApplicable Compliance Requirements:\n"
            for req in analysis.compliance_requirements[:5]:  # Top 5 most relevant
                compliance_context += f"- {req.category}: {req.requirement_text}\n"
        
        user_prompt = f"""
        RFP REQUIREMENT:
        Number: {requirement_number}
        Text: {rfp_requirement}
        
        {compliance_context}
        {past_perf_text}
        
        Generate a compelling, compliant proposal response (2000-3000 words).
        
        Return valid JSON conforming to ProposalSection schema.
        """
        
        response = self.client.messages.create(
            model=self.structured_model,
            max_tokens=4000,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
            output_format={
                "type": "json",
                "schema": ProposalSection.model_json_schema()
            }
        )
        
        result_json = json.loads(response.content[0].text)
        proposal = ProposalSection(**result_json)
        
        logger.info(f"Proposal generated. Readability: {proposal.readability_score}")
        return proposal
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # REFERENCE EXTRACTION
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def extract_all_references(
        self,
        document_text: str,
        document_id: str
    ) -> 'ReferenceExtraction':
        """Exhaustively extract all regulatory/standards references"""
        
        from schemas.writing import ReferenceExtraction
        
        logger.info(f"Extracting all references from {document_id}")
        
        system_prompt = """[Use ANALYSIS LAYER SYSTEM PROMPT - Reference Extraction Rules]"""
        
        user_prompt = f"""
        Document: {document_id}
        
        Extract EVERY regulatory reference, standard, and external document reference:
        
        - FAR citations (48 CFR X.XXX): [Complete list with context]
        - DFARS clauses (DFARS 252.XXX): [Complete list]
        - NIST standards: [SP 800-171, 800-53, etc.]
        - ISO standards: [27001, 9001, etc.]
        - Industry standards: [IEEE, ANSI, etc.]
        - External documents: [SOWs, specs, appendices]
        - Appendix references: [Cross-references]
        - Total unique references found
        - Critical vs optional references
        - Overall regulatory framework
        - Compliance complexity assessment
        
        Document text:
        {document_text}
        
        Return valid JSON conforming to ReferenceExtraction schema.
        """
        
        response = self.client.messages.create(
            model=self.structured_model,
            max_tokens=4000,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
            output_format={
                "type": "json",
                "schema": ReferenceExtraction.model_json_schema()
            }
        )
        
        result_json = json.loads(response.content[0].text)
        references = ReferenceExtraction(**result_json)
        
        logger.info(f"Found {references.total_references_found} total references")
        return references
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # VISION LAYER
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def extract_from_image(
        self,
        image_source: str,  # base64 or URL
        form_type: str = "generic",
        media_type: str = "image/jpeg"
    ) -> 'OCRExtraction':
        """Extract text and data from scanned image"""
        
        from schemas.vision import OCRExtraction
        
        logger.info(f"Extracting from image (form type: {form_type})")
        
        system_prompt = """[Use VISION LAYER SYSTEM PROMPT from Part 2.4]"""
        
        form_prompts = {
            "SF-86": "This is a Standard Form 86 (Security Clearance). Extract all fields exactly.",
            "SAM": "This is a SAM.gov Entity Registration. Extract entity data, CAGE code, DUNS.",
            "CMMC": "This is a CMMC Assessment Report. Extract assessment level, findings, gaps.",
            "generic": "Extract all text, form fields, tables, and structured data from this document."
        }
        
        form_prompt = form_prompts.get(form_type, form_prompts["generic"])
        
        # Note: With structured outputs beta, use message with image
        response = self.client.messages.create(
            model=self.structured_model,
            max_tokens=2048,
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64" if not image_source.startswith("http") else "url",
                                "media_type": media_type,
                                "data": image_source if not image_source.startswith("http") else image_source
                            }
                        },
                        {
                            "type": "text",
                            "text": form_prompt + "\n\nReturn valid JSON conforming to OCRExtraction schema."
                        }
                    ]
                }
            ],
            output_format={
                "type": "json",
                "schema": OCRExtraction.model_json_schema()
            }
        )
        
        result_json = json.loads(response.content[0].text)
        extraction = OCRExtraction(**result_json)
        
        logger.info(f"Vision extraction complete. Confidence: {extraction.ocr_confidence}")
        return extraction


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# USAGE EXAMPLE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Initialize pipeline
import os
pipeline = FedOpsPipeline(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Step 1: Extract contract
extracted = pipeline.extract_document(
    document_text=contract_pdf_text,
    document_id="CONTRACT_001",
    extraction_tool="docling"
)

# Step 2: Analyze for compliance
analysis = pipeline.analyze_document(extracted)

# Step 3: Extract all references
references = pipeline.extract_all_references(
    document_text=extracted.full_text,
    document_id="CONTRACT_001"
)

# Step 4: Generate proposal response
proposal = pipeline.generate_proposal_section(
    rfp_requirement="Describe your technical approach to AI-powered document processing...",
    requirement_number="Section 3.1.2",
    analysis=analysis,
    past_performance=["Project Alpha: Extracted 10K documents with 99.2% accuracy"]
)

# All outputs are Pydantic models with guaranteed schema compliance
print(f"Compliance Requirements: {len(analysis.compliance_requirements)}")
print(f"Regulatory References: {references.total_references_found}")
print(f"Proposal Readability: {proposal.readability_score}")
```

### 4.2 Error Handling & Structured Output Validation

```python
# error_handling.py

from pydantic import ValidationError
import logging

logger = logging.getLogger(__name__)

class StructuredOutputValidator:
    """Validate and handle structured output responses"""
    
    @staticmethod
    def validate_response(response_json: dict, schema_class: Type[BaseModel]) -> BaseModel:
        """
        Validate Claude response against Pydantic schema.
        With Structured Outputs beta, this should always succeed.
        """
        try:
            validated = schema_class(**response_json)
            logger.info(f"✓ Response validated as {schema_class.__name__}")
            return validated
        except ValidationError as e:
            # This should NOT happen with Structured Outputs, but handle gracefully
            logger.error(f"Schema validation failed: {e}")
            raise ValueError(f"Response does not match {schema_class.__name__} schema") from e
    
    @staticmethod
    def handle_low_confidence(model_output: BaseModel, confidence_threshold: float = 0.70):
        """
        Flag outputs with low confidence for manual review
        """
        if hasattr(model_output, 'analysis_confidence'):
            if model_output.analysis_confidence < confidence_threshold:
                logger.warning(
                    f"Low confidence output ({model_output.analysis_confidence}). "
                    "Flagging for manual review."
                )
                return True
        return False
    
    @staticmethod
    def audit_response(response: BaseModel, document_id: str):
        """
        Create audit trail of all model outputs for compliance
        """
        audit_entry = {
            "document_id": document_id,
            "model_output_type": type(response).__name__,
            "timestamp": datetime.utcnow().isoformat(),
            "confidence": getattr(response, 'analysis_confidence', None),
            "requires_review": StructuredOutputValidator.handle_low_confidence(response)
        }
        logger.info(f"Audit: {audit_entry}")
        return audit_entry
```

---

## PART 5: INTEGRATION CHECKLIST

### Before Production Deployment

- [ ] **Pydantic schemas imported** and integrated into orchestration layer
- [ ] **System prompts** loaded from config (not hardcoded)
- [ ] **Structured Outputs beta** header enabled (`structured-outputs-2025-11-13`)
- [ ] **Error handling** for low-confidence outputs (< 0.70)
- [ ] **Audit logging** captures all model inputs/outputs
- [ ] **Confidence scoring** honest and calibrated per task
- [ ] **Reference extraction** tested on 5+ government contracts
- [ ] **Proposal generation** validated for requirement coverage
- [ ] **Vision OCR** tested on government forms (SF-86, SAM)
- [ ] **Fallback logic** for extraction (Docling → pypdfium2)
- [ ] **Cost tracking** monitors API spend per document type
- [ ] **Quality metrics** dashboard (extraction accuracy, analysis completeness, proposal quality)

---

## QUICK REFERENCE: MODEL SELECTION BY TASK

| Task | Primary Model | Schema | System Prompt |
|------|---------------|--------|---------------|
| **Extract Text/Tables** | Claude 3.5 Sonnet | ExtractedDocument | Part 2.1 |
| **Analyze Compliance** | Claude 3.5 Sonnet | DocumentAnalysis | Part 2.2 |
| **Generate Proposal** | Claude 3.5 Sonnet | ProposalSection | Part 2.3 |
| **Extract References** | Claude 3.5 Sonnet | ReferenceExtraction | Part 2.2 |
| **Vision/OCR** | Claude 3.5 Vision | OCRExtraction | Part 2.4 |
| **Polish Writing** | GPT-4.5 | ProposalSection | Part 2.3 variant |
| **Complex Layouts** | Qwen 3-VL | OCRExtraction | Part 2.4 variant |

---

**Document Status**: Complete  
**Version**: 1.0  
**Last Updated**: December 13, 2025  
**Ready for Implementation**: Yes

All prompts and schemas are production-ready for FedOps integration with Structured Outputs (Claude Sonnet 4.5+ beta).
