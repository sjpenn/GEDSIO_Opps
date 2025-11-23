
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

MASTER_PROMPT_INSTRUCTIONS = """
### Instructions
Analyze the provided government solicitation document(s) (RFP, RFQ, etc.) and provide a comprehensive analysis.
Focus on:
1.  **Opportunity Metadata**: Agency, Value, Dates, Set-asides.
2.  **Mandatory Requirements**: Go/No-Go factors.
3.  **Scope of Work**: Key tasks and deliverables.
4.  **Evaluation Criteria**: How the winner is chosen.
5.  **Submission Instructions**: Key dates and format.

Generate a detailed Markdown report and structured JSON data.
"""

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
