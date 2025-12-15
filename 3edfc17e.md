# GEDSIO Production-Ready Prompts

## Production Prompt 1: Document Classification

Copy and use this directly with your LLM:

```
ROLE: Government Solicitation Document Analyzer

TASK: Classify the structure of provided solicitation documents.

GOVERNMENT SOLICITATION CONTEXT:
Federal solicitations follow FAR 33.2 with sections A-M:
- Sections A-K: Administrative and contract content
- Section L: Proposal Preparation Instructions (PAGE LIMITS, VOLUMES, FORMATTING)
- Section M: Evaluation Criteria (SCORING METHODOLOGY)
- Section C: Statement of Work (TECHNICAL REQUIREMENTS)

TWO PRIMARY PATTERNS:
1. MULTI-DOCUMENT: Separate files per section
   Example files: "RFP_Cover_Section_A.pdf", "RFP_SOW_Section_C.pdf", "RFP_Evals_Section_M.pdf"
   
2. SINGLE-DOCUMENT: All sections in one PDF
   Example: "Full_RFP_Combined.pdf" containing A through M

YOUR INPUT:
A list of document filenames and their content for one opportunity.

YOUR OUTPUT:
JSON with classification, document inventory, and extraction strategy.

CLASSIFICATION RULES:
- If >50% of content is clearly from different sections in different files → MULTI_DOCUMENT
- If all sections visible in one file with clear dividers (Section A, Section B, etc.) → SINGLE_DOCUMENT  
- If files are not clearly mapped to sections (e.g., Technical.pdf, Commercial.pdf) → HYBRID

ANALYZE THE FOLLOWING DOCUMENTS:

[DOCUMENTS WILL BE PROVIDED HERE]

PROVIDE JSON RESPONSE:
{
  "classification": "MULTI_DOCUMENT | SINGLE_DOCUMENT | HYBRID",
  "confidence": "HIGH | MEDIUM | LOW",
  "documents": [
    {
      "filename": "exact filename",
      "likely_section": "A-M or array",
      "extraction_priority": 1-5,
      "notes": "why this section is important"
    }
  ],
  "extraction_sequence": ["filename1", "filename2", "filename3"],
  "critical_sections_identified": ["L", "M", "C"],
  "strategy": "brief description of how to proceed"
}
```

---

## Production Prompt 2: Section Detection (Single Document)

```
ROLE: Document Section Parser

TASK: Identify where each section (A-M) begins and ends in a single government solicitation document.

CONTEXT:
This is a SINGLE solicitation document containing multiple sections.
Sections should have clear headers like "Section A:", "Section L:", etc.
Some sections may not be present (e.g., Section D is rarely used in modern solicitations).

STANDARD SECTIONS:
- A: Information to Offerors (typically 1-3 pages)
- B: Supplies/Services and Price (typically 2-5 pages)
- C: Description/SOW (typically 5-20 pages) ← CRITICAL
- D: Packaging and Marketing (rarely present)
- E: Inspection and Acceptance (typically 1-3 pages)
- F: Deliveries or Performance (typically 1-3 pages)
- G: Contract Administrative Data (typically 1-2 pages)
- H: Special Contract Requirements (typically 2-10 pages)
- I: Contract Clauses (typically 5-20 pages)
- J: Attachments Index (typically 1 page)
- K: Representations and Certifications (typically 2-5 pages)
- L: Proposal Preparation Instructions (typically 3-10 pages) ← CRITICAL
- M: Evaluation Criteria (typically 3-10 pages) ← CRITICAL

KEY EXTRACTION TARGETS:
From Section L: Page limits, volume structure (e.g., "Technical Volume max 50 pages"), formatting rules
From Section M: Evaluation factors, weights (e.g., "Technical 40%, Price 30%, Past Performance 30%")
From Section C: Deliverables, compliance requirements, security requirements

DOCUMENT TEXT:
[FULL DOCUMENT TEXT WILL BE PROVIDED HERE]

PROVIDE JSON RESPONSE:
{
  "document_length": "number of lines",
  "sections_detected": [
    {
      "section_letter": "A",
      "section_title": "Information to Offerors or Quoters",
      "start_line": 5,
      "end_line": 87,
      "detected_by": "explicit header | keyword matching | logical deduction",
      "confidence": "HIGH | MEDIUM | LOW"
    }
  ],
  "critical_findings": {
    "section_l": {
      "found": true,
      "page_limits": "extracted page limit info",
      "volumes": "if mentioned",
      "formatting": "key formatting requirements"
    },
    "section_m": {
      "found": true,
      "evaluation_factors": ["Factor 1: Weight%", "Factor 2: Weight%"],
      "total_weight": "should equal 100%"
    },
    "section_c": {
      "found": true,
      "sow_identified": true,
      "line_range": "start-end"
    }
  },
  "parsing_confidence": "HIGH | MEDIUM | LOW",
  "recommendations": ["recommendation 1", "recommendation 2"]
}
```

---

## Production Prompt 3: Requirement Extraction

```
ROLE: Requirements Extraction Specialist

TASK: Extract and structure all requirements from a government solicitation section.

CONTEXT:
You are analyzing one specific section (e.g., Section C - SOW, or Section H - Special Requirements).
Your job is to identify each requirement, categorize it, and extract key attributes.

REQUIREMENT TYPES:
- MANDATORY: Must be in proposal (marked with "shall", "must", "required")
- CONDITIONAL: Required if [condition] (marked with "if [X] then [Y]")
- OPTIONAL: Nice to have (marked with "may", "should", "could")

REQUIREMENT CATEGORIES:
- TECHNICAL: Technology, architecture, approach
- COMPLIANCE: Regulatory, standards, certifications
- DELIVERABLE: Documents, code, reports to deliver
- PERFORMANCE: Metrics, SLAs, uptime, response times
- SECURITY: Clearances, certifications, data handling
- PERSONNEL: Staffing, qualifications, experience
- SCHEDULE: Dates, timelines, delivery windows
- ORGANIZATIONAL: Structure, processes, governance

SECTION TEXT:
[SECTION TEXT WILL BE PROVIDED HERE]

EXTRACT ALL REQUIREMENTS AS JSON:
{
  "section": "C",
  "section_title": "extracted from text",
  "total_requirements_found": number,
  "requirements": [
    {
      "req_id": "C_001",
      "requirement_text": "quoted directly from document",
      "type": "MANDATORY | CONDITIONAL | OPTIONAL",
      "category": "TECHNICAL | COMPLIANCE | DELIVERABLE | PERFORMANCE | SECURITY | PERSONNEL | SCHEDULE | ORGANIZATIONAL",
      "key_metrics": ["metric1: value1", "metric2: value2"],
      "associated_dates": ["YYYY-MM-DD: description"],
      "must_include_in_proposal": "yes | maybe | no",
      "proposal_response_area": "Where in proposal this should be addressed"
    }
  ],
  "summary": {
    "mandatory_requirements": number,
    "conditional_requirements": number,
    "optional_requirements": number,
    "deliverables_list": ["deliverable 1", "deliverable 2"],
    "key_dates": ["date: description"],
    "compliance_requirements": ["requirement 1", "requirement 2"]
  }
}
```

---

## Production Prompt 4: Section M to C Mapping

```
ROLE: Evaluation Strategy Mapper

TASK: Connect evaluation criteria (Section M) to requirements (Section C).

CONTEXT:
Section M shows HOW proposals will be scored.
Section C shows WHAT must be done.
This mapping connects them: "To score well on Evaluation Factor M.1 (Technical Approach),
the proposal must address Requirements C.3.1, C.3.2, and C.3.5."

SECTION M TEXT (Evaluation Criteria):
[SECTION M WILL BE PROVIDED HERE]

SECTION C TEXT (Statement of Work/Requirements):
[SECTION C WILL BE PROVIDED HERE]

CREATE MAPPING AS JSON:
{
  "evaluation_mapping": [
    {
      "evaluation_factor": "M.1 Technical Approach",
      "weight_percent": 40,
      "scoring_description": "How is this factor scored?",
      "critical_success_factors": [
        "CSF1: description",
        "CSF2: description"
      ],
      "linked_requirements": [
        {
          "requirement_id": "C_001",
          "requirement_text": "quoted",
          "relationship": "This evaluation factor measures how well proposal addresses this requirement"
        }
      ],
      "proposal_implications": "What must proposal include to score well?"
    }
  ],
  "scoring_summary": {
    "technical": "40%",
    "management": "20%",
    "past_performance": "20%",
    "price": "20%"
  },
  "win_strategy": {
    "must_haves": ["3-5 non-negotiable items"],
    "differentiators": ["2-3 ways to stand out"],
    "risks_to_avoid": ["2-3 common mistakes"]
  }
}
```

---

## Production Prompt 5: Generate Executive Summary

```
ROLE: Executive Summary Generator

TASK: Create a brief, actionable summary of a solicitation section for business team.

CONTEXT:
Your audience is BUSINESS DEVELOPMENT and PROPOSAL TEAM.
They need to understand: What's required? Why does it matter? How should we respond?

SECTION TEXT:
[TEXT PROVIDED HERE]

SECTION TYPE: [C | L | M | H | other]

GENERATE SUMMARY:
{
  "executive_summary": {
    "headline": "One sentence: What is this section about?",
    "key_takeaways": [
      "Takeaway 1: What matters most?",
      "Takeaway 2: What's required?",
      "Takeaway 3: What's the risk if we miss this?"
    ]
  },
  "proposal_response": {
    "where_to_address": "In what section(s) of OUR proposal?",
    "what_to_include": ["item 1", "item 2", "item 3"],
    "approximate_pages": "2-3 pages for this topic",
    "tone_and_approach": "How should we present this? (Technical deep-dive? Executive summary? Case study?)"
  },
  "red_flags": [
    {
      "flag": "Description of unusual or risky requirement",
      "severity": "HIGH | MEDIUM | LOW",
      "our_response": "How we should handle this"
    }
  ],
  "opportunities": [
    {
      "opportunity": "Where can we differentiate?",
      "approach": "How to build this into proposal?"
    }
  ],
  "questions_for_customer": [
    "Question 1 we should ask if unclear?",
    "Question 2?"
  ]
}
```

---

## Production Prompt 6: Smart Document Slideout (for UI)

```
ROLE: Document Content Formatter

TASK: Prepare document content for UI display in a slideout panel.

CONTEXT:
User clicks on a document name and sees a panel showing:
1. Full document text
2. Section highlighting (if applicable)
3. Key extractions (requirements, dates, metrics)
4. Quick summary

DOCUMENT DATA:
{
  "filename": "RFP_Section_M_Evaluation.pdf",
  "document_text": "[FULL TEXT HERE]",
  "sections_detected": [
    {"section": "M", "start": 0, "end": 500}
  ],
  "requirements_extracted": [
    {"id": "M_001", "text": "requirement text"}
  ]
}

FORMAT FOR UI DISPLAY:
{
  "filename": "displayed at top",
  "metadata": {
    "pages": number,
    "size_kb": number,
    "extraction_date": "YYYY-MM-DD"
  },
  "display_sections": [
    {
      "type": "summary",
      "content": "AI-generated 2-3 sentence summary"
    },
    {
      "type": "highlights",
      "items": [
        "Key finding 1",
        "Key finding 2",
        "Key date: deadline"
      ]
    },
    {
      "type": "full_text",
      "content": "Full document text with HTML markup for sections",
      "markup": "<div class='section-m'>...full text...</div>"
    },
    {
      "type": "requirements_table",
      "headers": ["ID", "Requirement", "Category"],
      "rows": [
        ["M_001", "requirement text", "EVALUATION"]
      ]
    }
  ]
}
```

---

## Production Prompt 7: Batch Classification (for bulk opportunities)

```
ROLE: Batch Solicitation Processor

TASK: Classify multiple opportunities at once.

INPUT:
Array of opportunities, each with file list.

FOR EACH OPPORTUNITY:
- Determine: SINGLE_DOCUMENT or MULTI_DOCUMENT
- Identify critical sections present
- Recommend extraction sequence

OPPORTUNITIES:
[
  {
    "opportunity_id": "OPP-001",
    "files": ["file1.pdf", "file2.pdf", "file3.pdf"]
  },
  {
    "opportunity_id": "OPP-002",
    "files": ["full_rfp.pdf"]
  }
]

RETURN:
{
  "batch_results": [
    {
      "opportunity_id": "OPP-001",
      "classification": "MULTI_DOCUMENT | SINGLE_DOCUMENT",
      "reason": "brief explanation",
      "extraction_priority": 1-5,
      "estimated_processing_time": "minutes"
    }
  ],
  "batch_summary": {
    "total_opportunities": number,
    "multi_document_count": number,
    "single_document_count": number
  }
}
```

---

## Usage Examples

### Example 1: Start with a New Opportunity

```bash
# Step 1: User uploads files for new opportunity
# Files: RFP_Cover.pdf, RFP_SOW.pdf, RFP_Evals.pdf

# Step 2: Run Prompt 1 (Classification)
# Input: List of 3 files
# Output: "MULTI_DOCUMENT - Extract each file separately, map Section A to Cover, Section C to SOW, Section M to Evals"

# Step 3: Extract text from each file and store in DB

# Step 4: Run Prompt 2 (Section Detection)
# For single-document files, identify section boundaries
# For multi-document, map to likely sections

# Step 5: Run Prompt 3 (Requirement Extraction)
# Extract requirements from Section C (SOW)

# Step 6: Run Prompt 4 (Evaluation Mapping)
# Map Section M criteria to Section C requirements

# Step 7: Run Prompt 5 (Summary Generation)
# Generate executive summary for business team

# Step 8: UI displays document list
# User can click any document to see slideout with formatted content from Prompt 6
```

### Example 2: Quick Processing of Similar Opportunity

```bash
# This is a follow-on to a previous opportunity
# Run Prompt 7 (Batch) with classification patterns from previous opportunity
# System recognizes: "This looks like same format as OPP-001"
# Applies cached extraction strategy
# Results ready in 2-3 minutes instead of 10-15 minutes
```

---

## Implementation Checklist

- [ ] Store Prompts 1-7 in your system
- [ ] Test Prompts 1 & 2 with sample RFPs from SAM.gov
- [ ] Build database schema (sections, requirements, mappings)
- [ ] Integrate PDF text extraction (using PDF library or Claude's vision)
- [ ] Build document list UI component
- [ ] Build slideout panel component (Prompt 6 output → UI)
- [ ] Test end-to-end with 3-5 real opportunities
- [ ] Measure accuracy (section detection, requirement extraction)
- [ ] Add performance monitoring (time per document, API costs)
- [ ] Document learned patterns (save classification results for future reference)

---

## LLM Selection Notes

### Claude (Recommended for this task)
- Vision capabilities for PDF processing
- Strong at structured data extraction
- Good at connecting requirements across documents
- Context window handles long solicitations well

### GPT-4
- Works but requires separate PDF parser
- Good at reasoning about requirement relationships
- Can handle complexity well

### Both approaches
- Use LLM for classification and extraction (Prompts 1-5)
- Build custom logic for UI display (Prompt 6)
- Cache results to minimize API calls

---

## Performance Optimization

### Caching Strategy
```
Cache by: [OpportunityID]_[SectionLetter]
Example: OPP_SAM_12345_SECTION_M
TTL: 30 days (re-extract if solicitation updated)
```

### Batch Processing
- Process similar opportunities together
- Share classification patterns
- Build opportunity templates

### Cost Optimization
- Use Prompt 1 only on new opportunities
- Cache Prompts 2-5 outputs
- Use cheaper LLM for UI formatting (Prompt 6)
- Process in batch mode if possible
