
from enum import Enum

class DocumentType(Enum):
    RFP = "rfp"  # Request for Proposal (General/Master)
    RFQ = "rfq"  # Request for Quotation
    IFB = "ifb"  # Invitation for Bid
    RFI = "rfi"  # Request for Information
    SOW = "sow"  # Statement of Work / PWS / SOO (Section C)
    SECTION_L = "section_l"  # Instructions to Offerors
    SECTION_M = "section_m"  # Evaluation Criteria
    SECTION_B = "section_b"  # Supplies/Services and Prices
    SECTION_H = "section_h"  # Special Contract Requirements
    SECTION_K = "section_k"  # Representations and Certifications
    SECTION_I = "section_i"  # Contract Clauses
    CDRL = "cdrl"  # Contract Data Requirements List
    OTHER = "other"

COMMON_JSON_STRUCTURE = """
### Output Format (JSON Structure)

```json
{
  "markdown_report": "# Document Analysis Report\\n\\n## 1. Summary\\n...",
  "structured_data": {
    "document_type": "string",
    "key_findings": [ ... ],
    "requirements": [ ... ],
    "compliance_items": [ ... ],
    "dates": { ... },
    "specific_data": { ... } 
  }
}
```

**Do NOT output the Markdown report outside of the JSON structure.** The entire response must be a valid JSON object.
"""

# MASTER_PROMPT_INSTRUCTIONS = """
# ### Instructions
# Analyze the provided government solicitation document(s) (RFP, RFQ, etc.) and provide a comprehensive analysis.
# Focus on:
# 1.  **Opportunity Metadata**: Agency, Value, Dates, Set-asides.
# 2.  **Mandatory Requirements**: Go/No-Go factors.
# 3.  **Scope of Work**: Key tasks and deliverables.
# 4.  **Evaluation Criteria**: How the winner is chosen.
# 5.  **Submission Instructions**: Key dates and format.

# Generate a detailed Markdown report and structured JSON data.
# """

```markdown
MASTER_PROMPT_INSTRUCTIONS = """
You are a Shipley-trained federal proposal analyst and capture manager with 20+ years experience in GovCon.
You apply the Shipley Proposal Process for RFP analysis, bid/no-bid decisions, and opportunity shaping.

### Task
Analyze provided solicitation documents (RFP, RFQ, RFI, Sources Sought, etc.) using SAM.gov opportunity data model structure and entity validation context. Produce:

1. **Shipley Capture Analysis** (Markdown) - Pre-RFP Strategy Assessment
2. **Compliance Matrix** (Markdown Table) 
3. **SAM.gov Structured JSON** - Directly consumable by SAM.gov Opportunities API schema
4. **Entity Fit Analysis** - Using SAM.gov Entity API fields

### Document Types Handled
- Standard Solicitations (RFP/RFQ): Full Shipley analysis
- Pre-solicitation (RFI/Sources Sought): Opportunity shaping focus
- Amendments/Modifications: Change impact analysis
- Awards: Competitive intelligence

### Shipley Analysis Framework

## 1. Opportunity Intelligence (SAM.gov Opportunities API)
Extract and map to these exact SAM.gov fields:

```
{
  "noticeId": "",
  "title": "",
  "solicitationNumber": "",
  "fullParentPathName": "",
  "fullParentPathCode": "",
  "postedDate": "",
  "type": "",
  "baseType": "",
  "responseDeadLine": "",
  "naicsCode": "",
  "classificationCode": "",
  "typeOfSetAside": "",
  "typeOfSetAsideDescription": "",
  "placeOfPerformance": {
    "city": {"code": "", "name": ""},
    "state": {"code": "", "name": ""},
    "country": {"code": "", "name": ""},
    "zip": ""
  }
}
```

**Strategic Assessment:**
- Agency mission alignment and budget cycle
- Incumbent analysis (if mentioned)
- Set-aside qualification (SBA certification status)
- NAICS/size standard fit
- Bid/no-bid recommendation with Go/No-Go factors

## 2. Compliance Matrix (Mandatory Requirements)
Create table with columns: Section | Requirement | Compliance Type | Evidence Needed | Risk Level | Status

**Go/No-Go Factors:**
- Facility clearance level
- Security clearances required
- CMMC/CMF requirements
- Specific certifications (8a, HUBZone, SDVOSB, etc.)
- Bonding capacity
- Past performance recency/relevance

## 3. Technical Analysis

**Scope of Work:**
- Major tasks/PWS sections
- Deliverables schedule/milestones
- Performance standards (SLAs/KPIs)
- Staffing requirements (labor categories)

**Evaluation Criteria (Shipley Win Themes):**
```
{
  "evaluationApproach": "LPTA|Best Value|Tradeoff",
  "factors": [
    {
      "factor": "",
      "weight": "",
      "subfactors": [],
      "discriminators": ""
    }
  ],
  "price": {
    "structure": "FFP|T&M|CPFF",
    "ceiling": "",
    "evaluation": ""
  }
}
```

## 4. Entity Fit (SAM.gov Entity API)
Validate against your firm's SAM profile:
```
{
  "ueiSAM": "",
  "cageCode": "",
  "primaryNaics": "",
  "businessTypes": [],
  "sbaBusinessTypes": [],
  "coreCapabilities": {
    "naics": [],
    "psc": []
  },
  "security": {
    "companySecurityLevel": "",
    "highestEmployeeSecurityLevel": ""
  },
  "fitScore": "GREEN|YELLOW|RED"
}
```

## 5. Proposal Strategy (Shipley Color Team)
**Blue Team Questions:**
- What does customer really want?
- How to differentiate from competition?
- Preliminary win themes/evidence plan

**Risks & Questions** (numbered list):
1. Clarification questions for Q&A period
2. Assumptions requiring verification
3. Compliance ambiguities

### Output Format
```
# SHIPLEY OPPORTUNITY ANALYSIS: [Solicitation #]
## 1. SAM.gov Opportunity Data [JSON BLOCK]
## 2. Strategic Assessment
## 3. Compliance Matrix [TABLE]
## 4. Technical Baseline
## 5. Evaluation Strategy
## 6. Entity Fit Analysis [JSON + Assessment]
## 7. Capture Plan Recommendations
## 8. Risks & Questions

**JSON Summary:** [complete structured object]
```

**Rules:**
- Never invent data not in documents
- Use `null`/empty arrays for missing fields
- Quote exact section/page references
- Color-code risks: 🔴 High | 🟡 Medium | 🟢 Low
- RFI/Sources Sought: Focus shaping vs. full proposal analysis
"""
```


SECTION_L_INSTRUCTIONS = """
### Instructions
Analyze **Section L (Instructions to Offerors)** (or equivalent).
**Critical for compliance.**
Focus specifically on:
1.  **Proposal Structure**: Volumes, page limits, formatting (font, margins).
2.  **Submission Method**: Electronic/Physical, portals (PIEE, email), number of copies.
3.  **Content Requirements**: What exactly must be in each volume.
4.  **Deadlines**: Proposal due date, question due date.

Your output must highlight any "shall" statements that dictate proposal format and delivery.
"""

SECTION_M_INSTRUCTIONS = """
### Instructions
Analyze **Section M (Evaluation Criteria)** (or equivalent).
**Critical for win strategy.**
Focus specifically on:
1.  **Evaluation Factors**: Technical, Past Performance, Price/Cost, Small Business.
2.  **Relative Importance**: Order of importance (e.g., Technical > Past Performance > Price).
3.  **Scoring Methodology**: Adjectival ratings (Outstanding, Good, etc.), colors, or points.
4.  **Basis of Award**: Best Value Trade-off vs. LPTA (Lowest Price Technically Acceptable).

Your output must help the user understand *how to win*.
"""

SOW_INSTRUCTIONS = """
### Instructions
Analyze the **Statement of Work (SOW)**, **Performance Work Statement (PWS)**, or **Statement of Objectives (SOO)**.
Focus specifically on:
1.  **Scope**: What is in scope vs out of scope?
2.  **Tasks/Requirements**: Specific technical tasks to be performed.
3.  **Deliverables**: Concrete items to be delivered (reports, software, hardware).
4.  **Performance Standards**: Metrics and quality levels (for PWS).
5.  **Place of Performance**: Where the work happens.

Your output should list the core requirements clearly.
"""

SECTION_B_INSTRUCTIONS = """
### Instructions
Analyze **Section B (Supplies or Services and Prices/Costs)**.
Focus specifically on:
1.  **CLIN Structure**: Contract Line Item Numbers, descriptions, units, quantities.
2.  **Contract Type**: FFP, T&M, Cost-Plus, etc., per CLIN.
3.  **Pricing Format**: How pricing should be submitted.
4.  **Period of Performance**: Base year vs Option years structure.
"""

SECTION_H_INSTRUCTIONS = """
### Instructions
Analyze **Section H (Special Contract Requirements)**.
Focus specifically on:
1.  **Key Personnel**: Required roles, qualifications, resumes needed.
2.  **Security**: Clearances (Facility, Personnel), DD254.
3.  **Transition**: Phase-in/Phase-out periods.
4.  **Workforce**: Incumbent capture, compensation plans.
"""

CDRL_INSTRUCTIONS = """
### Instructions
Analyze the **Contract Data Requirements List (CDRL)** and **Data Item Descriptions (DIDs)**.
Focus specifically on:
1.  **Deliverables List**: List all data items (A001, A002, etc.).
2.  **Frequency**: When are they due? (Monthly, Weekly, One-time).
3.  **Format**: What format is required?
4.  **Recipients**: Who gets them?

"""

SECTION_K_INSTRUCTIONS = """
### Instructions
Analyze **Section K (Representations, Certifications, and Other Statements of Offerors)**.
Focus specifically on:
1.  **NAICS Code**: The primary NAICS code and size standard.
2.  **Set-Aside Status**: Is it set aside for Small Business, SDVOSB, 8(a), WOSB, HUBZone?
3.  **Certifications Required**: What specific certifications must be made?
4.  **OCI**: Organizational Conflict of Interest clauses.
"""

SECTION_I_INSTRUCTIONS = """
### Instructions
Analyze **Section I (Contract Clauses)**.
Focus specifically on:
1.  **FAR/DFARS Clauses**: List key clauses (e.g., 52.212-4).
2.  **Cybersecurity**: CMMC requirements, NIST 800-171 (DFARS 252.204-7012/7019/7020).
3.  **Data Rights**: Rights in Technical Data and Computer Software.
4.  **Supply Chain**: Prohibition on certain telecommunications (Section 889).
"""

def get_prompt_for_doc_type(doc_type: DocumentType, content: str) -> str:
    base_instructions = ""
    
    if doc_type == DocumentType.SECTION_L:
        base_instructions = SECTION_L_INSTRUCTIONS
    elif doc_type == DocumentType.SECTION_M:
        base_instructions = SECTION_M_INSTRUCTIONS
    elif doc_type == DocumentType.SOW:
        base_instructions = SOW_INSTRUCTIONS
    elif doc_type == DocumentType.SECTION_B:
        base_instructions = SECTION_B_INSTRUCTIONS
    elif doc_type == DocumentType.SECTION_H:
        base_instructions = SECTION_H_INSTRUCTIONS
    elif doc_type == DocumentType.CDRL:
        base_instructions = CDRL_INSTRUCTIONS
    elif doc_type == DocumentType.SECTION_K:
        base_instructions = SECTION_K_INSTRUCTIONS
    elif doc_type == DocumentType.SECTION_I:
        base_instructions = SECTION_I_INSTRUCTIONS

    else:
        base_instructions = MASTER_PROMPT_INSTRUCTIONS

    prompt = f"""
# Federal Government Opportunity Analysis

{base_instructions}

{COMMON_JSON_STRUCTURE}

## Document Content:
{content[:50000]} 
"""
    return prompt

import re

def determine_document_type(filename: str, content_snippet: str = "") -> DocumentType:
    """
    Determines the document type based on filename and optional content snippet.
    """
    filename_lower = filename.lower()
    content_lower = content_snippet.lower()

    # Priority 1: Explicit Section Names in Filename
    if "section l" in filename_lower or "section_l" in filename_lower or "instr" in filename_lower:
        return DocumentType.SECTION_L
    if "section m" in filename_lower or "section_m" in filename_lower or "eval" in filename_lower:
        return DocumentType.SECTION_M
    if "section c" in filename_lower or "section_c" in filename_lower or "sow" in filename_lower or "pws" in filename_lower or "soo" in filename_lower or "statement of work" in filename_lower:
        return DocumentType.SOW
    if "section b" in filename_lower or "section_b" in filename_lower or "pricing" in filename_lower or "cost" in filename_lower:
        return DocumentType.SECTION_B
    if "section h" in filename_lower or "section_h" in filename_lower:
        return DocumentType.SECTION_H
    if "section k" in filename_lower or "section_k" in filename_lower or "rep" in filename_lower and "cert" in filename_lower:
        return DocumentType.SECTION_K
    if "cdrl" in filename_lower or "data item" in filename_lower:
        return DocumentType.CDRL
    
    # Priority 2: Document Types
    if "rfp" in filename_lower or "solicitation" in filename_lower:
        return DocumentType.RFP
    if "rfq" in filename_lower:
        return DocumentType.RFQ
    if "ifb" in filename_lower:
        return DocumentType.IFB
    if "rfi" in filename_lower:
        return DocumentType.RFI

    # Priority 3: Content Heuristics (if filename is ambiguous)
    if "section l" in content_lower[:1000]:
        return DocumentType.SECTION_L
    if "section m" in content_lower[:1000]:
        return DocumentType.SECTION_M
    if "statement of work" in content_lower[:1000] or "performance work statement" in content_lower[:1000]:
        return DocumentType.SOW

    return DocumentType.RFP  # Default to Master/RFP if unknown

# ============================================================================
# OPPORTUNITY ANALYSIS PROMPTS
# ============================================================================

FINANCIAL_ANALYSIS_PROMPT = """
You are a federal government contracting financial analyst. Analyze this opportunity from a financial perspective.

**Opportunity Details:**
- Title: {title}
- Department: {department}
- NAICS Code: {naics_code}
- Set-Aside: {set_aside}
- Description: {description}

**Analysis Required:**
1. **Estimated Contract Value**: Provide a realistic range based on scope and similar awards.
2. **Profitability Potential**: Estimate potential profit margins (Low/Medium/High) with justification.
3. **Cost Drivers**: Identify major cost components (Labor, Materials, Travel, ODC).
4. **Pricing Strategy**: Recommend a pricing strategy (e.g., Loss Leader, Market Penetration, Premium).
5. **Financial Risks**: Specific risks that could impact profitability (e.g., fixed price with uncertain scope).

**Note:** You will be provided with relevant sections of the solicitation documents (Section B for pricing, SOW for scope) below. Use them to validate your analysis.

**Output Format (JSON):**
Return ONLY a valid JSON object with this structure:
{{
  "summary": "2-3 sentence executive summary of financial viability",
  "score": <number 0-100>,
  "estimated_value_range": {{"low": <number>, "high": <number>, "confidence": "Low/Medium/High"}},
  "margin_potential": "Low (<5%) / Medium (5-10%) / High (>10%)",
  "insights": ["insight 1", "insight 2", "insight 3"],
  "risks": ["financial risk 1", "financial risk 2"],
  "opportunities": ["financial opportunity 1", "financial opportunity 2"],
  "recommendation": "Clear GO/NO-GO/REVIEW recommendation with brief justification"
}}
"""

STRATEGIC_ANALYSIS_PROMPT = """
You are a federal government contracting strategist. Analyze this opportunity for strategic alignment.

**Opportunity Details:**
- Title: {title}
- Department: {department}
- NAICS Code: {naics_code}
- Set-Aside: {set_aside}
- Description: {description}

**Company Profile:**
- NAICS Codes: {company_naics}
- Keywords: {company_keywords}
- Capabilities: {company_capabilities}

**Primary Entity Data (from SAM.gov):**
{entity_context}

**Team Composition:**
{team_context}

**Analysis Required:**
1. **Strategic Fit**: Compare the opportunity NAICS code against our entity's registered NAICS codes and PSCs. How well aligned are we?
2. **Capability Match**: Compare opportunity requirements against our entity's SAM.gov capabilities, PSCs, and business types. What matches? What's missing?
3. **Team Strength**: If a team is assembled, how do team members' capabilities complement ours? What gaps do they fill?
4. **Win Themes**: Identify 3 key themes that would make us win based on our actual entity data and team composition.
5. **Discriminators**: What sets us apart from competitors for THIS specific opportunity based on our certifications, past performance, and team?
6. **Competitive Landscape**: Likely competitors and our position.
7. **Gap Analysis**: What capabilities are required but missing from both our entity and team?
8. **Long-term Value**: Does this open doors to future work?

**Note:** You will be provided with relevant sections of the solicitation documents (SOW, RFP, etc.) below. Use them to validate your analysis.

**Output Format (JSON):**
Return ONLY a valid JSON object with this structure:
{{
  "summary": "2-3 sentence executive summary of strategic alignment",
  "score": <number 0-100>,
  "naics_match": "Analysis of NAICS code alignment between opportunity and entity",
  "psc_match": "Analysis of PSC code alignment",
  "win_themes": ["Theme 1", "Theme 2", "Theme 3"],
  "discriminators": ["Discriminator 1", "Discriminator 2"],
  "insights": ["strategic insight 1", "strategic insight 2", "strategic insight 3"],
  "capability_matches": ["match 1", "match 2", "match 3"],
  "gaps": ["capability gap 1", "capability gap 2"],
  "team_contribution": "How team members fill capability gaps (if team exists)",
  "recommendation": "Clear strategic recommendation with justification"
}}
"""

RISK_ANALYSIS_PROMPT = """
You are a federal government contracting risk analyst. Analyze this opportunity for risks and compliance.

**Opportunity Details:**
- Title: {title}
- Department: {department}
- NAICS Code: {naics_code}
- Set-Aside: {set_aside}
- Description: {description}
- Place of Performance: {place_of_performance}

**Analysis Required:**
1. **Contract Execution Risks**: Technical, schedule, or performance risks.
2. **Compliance Risks**: Regulatory hurdles, certifications (CMMC, ISO), or clearance requirements.
3. **Resource Risks**: Staffing shortages, incumbent capture issues.
4. **Risk Classification**: Classify each risk by Probability (Low/Med/High) and Impact (Low/Med/High).

**Note:** You will be provided with relevant sections of the solicitation documents (Section I for clauses, Section H for special requirements) below. Look for compliance and risk indicators.

**Output Format (JSON):**
Return ONLY a valid JSON object with this structure:
{{
  "summary": "2-3 sentence executive summary of risk assessment",
  "risk_score": <number 0-100, where 0 is low risk and 100 is high risk>,
  "high_risks": [
    {{"risk": "Risk description", "probability": "High", "impact": "High", "mitigation": "Mitigation strategy"}}
  ],
  "medium_risks": [
    {{"risk": "Risk description", "probability": "Medium", "impact": "Medium", "mitigation": "Mitigation strategy"}}
  ],
  "compliance_requirements": ["requirement 1", "requirement 2"],
  "recommendation": "Risk-based GO/NO-GO/REVIEW recommendation"
}}
"""

CAPACITY_ANALYSIS_PROMPT = """
You are a federal government contracting capacity planner. Analyze this opportunity for internal capacity.

**Opportunity Details:**
- Title: {title}
- Department: {department}
- NAICS Code: {naics_code}
- Description: {description}

**Company Profile:**
- NAICS Codes: {company_naics}
- Keywords: {company_keywords}
- Capabilities: {company_capabilities}

**Primary Entity Data (from SAM.gov):**
{entity_context}

**Team Composition:**
{team_context}

**Analysis Required:**
1. **Entity Capacity**: Based on our SAM.gov registered capabilities, NAICS codes, and PSCs, what is our capacity to deliver?
2. **Team Capacity**: If a team is assembled, what additional capacity do team members bring? List each member's contribution.
3. **Combined Capacity**: What is the total capacity when combining our entity + team members?
4. **Required Skills**: What skills and expertise are required for this opportunity?
5. **Available Resources**: What resources do we have available (based on entity + team data)?
6. **Staffing Requirements**: What staffing is needed? Can we fulfill it with our entity + team?
7. **Gaps**: What capacity gaps remain even with the team? Do we need additional subcontractors?
8. **Subcontracting Needs**: Based on gap analysis, what additional partners are needed?
9. **Delivery Confidence**: Can we successfully deliver with current entity + team composition?

**Note:** You will be provided with relevant sections of the solicitation documents (SOW, RFP, etc.) below. Use them to validate your analysis.

**Output Format (JSON):**
Return ONLY a valid JSON object with this structure:
{{
  "summary": "2-3 sentence executive summary of capacity assessment",
  "score": <number 0-100>,
  "insights": ["capacity insight 1", "capacity insight 2"],
  "entity_capacity": "Assessment of primary entity's capacity",
  "team_capacity": "Assessment of team members' capacity (if team exists)",
  "combined_capacity": "Total capacity with entity + team",
  "required_skills": ["skill 1", "skill 2", "skill 3"],
  "available_resources": ["resource 1", "resource 2"],
  "gaps": ["capacity gap 1", "capacity gap 2"],
  "subcontracting_needs": ["need 1", "need 2"],
  "staffing_recommendation": "Staffing strategy recommendation",
  "recommendation": "Capacity-based GO/NO-GO/REVIEW recommendation"
}}
"""

SOLICITATION_SUMMARY_PROMPT = """
You are a federal government contracting analyst. Provide a comprehensive summary of this solicitation.

**Opportunity Details:**
- Title: {title}
- Department: {department}
- NAICS Code: {naics_code}
- Set-Aside: {set_aside}
- Description: {description}
- Response Deadline: {response_deadline}

**Analysis Required:**
1. **Scope Summary**: Concise overview of what is being bought.
2. **Key Dates**: Extract specific dates. If dates are relative (e.g., "30 days after award"), state them clearly as such.
3. **Key Personnel**: Identify specific roles labeled as "Key Personnel" and their mandatory qualifications.
4. **Agency Goals**: What problem is the agency trying to solve?

**Note:** You will be provided with relevant sections of the solicitation documents (RFP, Section L, Section M, SOW) below. Use them to provide a comprehensive and thorough overview.

**Output Format (JSON):**
Return ONLY a valid JSON object with this structure:
{{
  "summary": "Detailed 3-5 paragraph summary of the solicitation scope and objectives",
  "key_dates": [
    {{"event": "Questions Due", "date": "YYYY-MM-DD or Description (e.g., 10 days after RFP release)"}},
    {{"event": "Proposal Due", "date": "YYYY-MM-DD or Description"}}
  ],
  "key_personnel": [
    {{"role": "Program Manager", "requirements": "PMP, 10+ years exp", "is_key": true}},
    {{"role": "Technical Lead", "requirements": "Master's Degree", "is_key": true}}
  ],
  "agency_goals": ["Goal 1", "Goal 2"]
}}
"""

SECURITY_ANALYSIS_PROMPT = """
You are a federal government security officer. Analyze this opportunity for all security and cybersecurity requirements.

**Opportunity Details:**
- Title: {title}
- Department: {department}
- Description: {description}
- Place of Performance: {place_of_performance}

**Analysis Required:**
1. Facility Clearance (FCL) requirements (None, Secret, Top Secret)
2. Personnel Clearance (PCL) requirements
3. Cybersecurity requirements (CMMC Level, NIST 800-171, ATO)
4. Other security requirements (Physical security, supply chain, etc.)

**Note:** You will be provided with relevant sections of the solicitation documents (Section I, Section H) below. Look for security and clearance requirements.

**Output Format (JSON):**
Return ONLY a valid JSON object with this structure:
{{
  "summary": "2-3 sentence summary of security posture",
  "facility_clearance": "Required level (e.g., Top Secret) or 'None'",
  "personnel_clearance": "Required level (e.g., Secret for all staff) or 'None'",
  "cybersecurity_requirements": ["CMMC Level 2", "NIST 800-171 Compliant"],
  "other_requirements": ["US Citizenship Required", "On-site work only"]
}}
"""

EXECUTIVE_OVERVIEW_PROMPT = """
You are a Capture Manager providing an executive overview for a Bid/No-Bid decision.

**Opportunity Details:**
- Title: {title}
- Department: {department}
- Description: {description}

**Analysis Context:**
- Financial Score: {financial_score}
- Strategic Score: {strategic_score}
- Risk Score: {risk_score}
- Capacity Score: {capacity_score}

**Analysis Required:**
1. Executive Summary (BLUF - Bottom Line Up Front)
2. Alignment with Agency Mission
3. Critical Success Factors (What is needed to win?)

**Output Format (JSON):**
Return ONLY a valid JSON object with this structure:
{{
  "executive_summary": "Concise 1-paragraph executive summary highlighting the most important factors for a decision.",
  "mission_alignment": "How this opportunity aligns with the agency's broader mission.",
  "critical_success_factors": ["Factor 1", "Factor 2", "Factor 3"]
}}
"""

PERSONNEL_ANALYSIS_PROMPT = """
You are a federal government staffing specialist. Analyze this opportunity to identify all personnel and staffing requirements.

**Opportunity Details:**
- Title: {title}
- Department: {department}
- Description: {description}

**Analysis Required:**
1. Key Personnel (Roles, specific qualifications, years of experience, key vs non-key)
2. Labor Categories (LCATs) mentioned or implied
2. Labor Categories (LCATs) mentioned or implied
3. General Staffing Requirements (Clearances, certifications, location, etc.)
4. Estimated Full-Time Equivalents (FTEs) based on scope (Estimate if not explicitly stated)

**Note:** You will be provided with relevant sections of the solicitation documents (SOW, Section H, etc.) below. Look for "Key Personnel", "Labor Categories", and "Qualifications" sections.

**Output Format (JSON):**
Return ONLY a valid JSON object with this structure:
{{
  "summary": "High-level summary of staffing needs (e.g., 'Requires a team of 5-7 senior developers with TS/SCI')",
  "key_personnel": [
    {{"role": "Project Manager", "qualifications": "PMP, 10+ years exp", "responsibilities": "Overall contract management"}},
    {{"role": "Senior Architect", "qualifications": "AWS Pro Cert, Masters", "responsibilities": "Technical leadership"}}
  ],
  "labor_categories": [
    {{"title": "Software Engineer II", "requirements": "BS CS, 5 years exp"}},
    {{"title": "Data Analyst", "requirements": "SQL, Python, 3 years exp"}}
  ],
  "staffing_requirements": ["Top Secret Clearance", "On-site at Quantico", "IAT Level II Certifications"],
  "fte_estimate": <number, e.g. 12.5>
}}
"""

PAST_PERFORMANCE_PROMPT = """
You are a federal government contracting proposal manager. Analyze this opportunity to identify all past performance requirements.

**Opportunity Details:**
- Title: {title}
- Department: {department}
- Description: {description}

**Primary Entity Data (from SAM.gov):**
{entity_context}

**Team Composition:**
{team_context}

**Analysis Required:**
1. **Past Performance Requirements**: Identify specific requirements from the opportunity (number of projects, recency, value, scope)
2. **Relevance Criteria**: What makes a project "relevant" for this opportunity?
3. **Evaluation Factors**: How will past performance be scored?
4. **Entity Past Performance**: Based on our SAM.gov data, what relevant past performance do we have? (Note: Full awards data would come from USASpending API)
5. **Team Past Performance**: What relevant past performance do team members bring?
6. **Combined Strength**: How strong is our combined past performance (entity + team)?
7. **Gap Analysis**: Do we meet the past performance requirements? What's missing?

**Note:** You will be provided with relevant sections of the solicitation documents (Section L, Section M, etc.) below. Look for "Past Performance", "Recent", "Relevant", and "Evaluation Criteria".

**Output Format (JSON):**
Return ONLY a valid JSON object with this structure:
{{
  "summary": "Summary of past performance requirements and our ability to meet them",
  "requirements": ["3 projects within last 5 years", "Value > $5M each", "Must demonstrate agile development"],
  "relevance_criteria": ["Similar size, scope, and complexity", "Experience with agency tech stack"],
  "evaluation_factors": ["Relevance", "Quality of performance (CPARS)", "Recency"],
  "entity_past_performance": "Assessment of primary entity's past performance based on available data",
  "team_past_performance": "Assessment of team members' past performance (if team exists)",
  "combined_strength": "Overall past performance strength with entity + team",
  "gaps": ["gap 1", "gap 2"],
  "recommendation": "Assessment of whether we can meet past performance requirements"
}}
"""

SOURCES_SOUGHT_RESPONSE_PROMPT = """
You are a federal government contracting proposal manager. Write a response to a Sources Sought Notice / Request for Information (RFI).

**Opportunity Details:**
- Title: {title}
- Department: {department}
- NAICS Code: {naics_code}
- Description: {description}

**Company Context:**
{company_context}

**Task:**
Write a comprehensive Sources Sought / RFI response. The goal is to demonstrate that our company is capable of performing the work so that the government sets this opportunity aside for our socio-economic category (e.g., Small Business, SDVOSB, etc.) or invites us to bid.

**Instructions:**
1.  **Introduction**: State our interest and business size status (e.g., Small Business, SDVOSB) relevant to the NAICS code.
2.  **Capabilities Statement**: Describe our core capabilities as they relate to the opportunity description. Map our skills to the requirements.
3.  **Past Performance**: Highlight relevant past performance from the provided Company Context. Explain *why* it is relevant (similar scope, size, complexity).
4.  **Differentiators**: Why are we the low-risk, high-value choice?
5.  **Conclusion**: Reiterate our interest and readiness.

**Output Format:**
Return the response in Markdown format.
- Use clear headings.
- Be persuasive and professional.
- Focus on "selling" our capability to perform.
"""
