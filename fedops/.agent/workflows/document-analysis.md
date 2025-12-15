---
description: How to process and analyze opportunity documents using the document classification and section parsing system
---

# Document Analysis Workflow

This workflow describes how to process government solicitation documents for opportunities, including classification, section detection, and structured extraction.

## Overview

The document analysis process follows the GEDSIO 7-prompt system:

1. **Prompt 1**: Document Classification (SINGLE vs MULTI-DOCUMENT)
2. **Prompt 2**: Section Boundary Detection (find A-M sections)
3. **Prompt 3**: Requirement Extraction (parse requirements)
4. **Prompt 4**: Evaluation Mapping (link Section M to Section C)
5. **Prompt 5**: Executive Summary (2-min brief)
6. **Prompt 6**: UI Formatting (slideout display)
7. **Prompt 7**: Batch Classification (bulk processing)

---

## Step 1: Document Ingestion

Upload documents for an opportunity via the API or UI.

Documents are stored in the `stored_files` table with:
- `opportunity_id`: Links to the opportunity
- `filename`: Original filename
- `file_path`: Path to stored file
- `parsed_content`: Extracted text content
- `file_type`: MIME type

```python
# Example: Files are automatically extracted when uploaded
# The DocumentExtractor service handles PDF/DOCX parsing
```

---

## Step 2: Document Classification

Run classification to determine if the opportunity is SINGLE_DOCUMENT, MULTI_DOCUMENT, or HYBRID.

```python
from fedops_core.services.classification_service import ClassificationService

# In your async endpoint:
classification_service = ClassificationService(db)
classification = await classification_service.classify_opportunity(opportunity_id)

print(f"Type: {classification.classification_type}")
print(f"Confidence: {classification.confidence}")
print(f"Amendments: {classification.amendment_count}")
```

### Amendment Handling

The classification system automatically detects amendments:
- Files named "Amendment 0001", "Mod 01", etc. are flagged as amendments
- Amendments do NOT change the classification (SINGLE stays SINGLE)
- Amendments are tracked separately in `amendment_files` field

---

## Step 3: Section Detection (Single-Doc Only)

For SINGLE_DOCUMENT opportunities, detect section A-M boundaries.

```python
# For each file in a single-document opportunity:
sections = await classification_service.detect_sections(file_id)

for section in sections:
    print(f"Section {section.section_letter}: lines {section.start_line}-{section.end_line}")
    print(f"  Title: {section.section_title}")
    print(f"  Confidence: {section.confidence_level}")
```

---

## Step 4: Section Extraction

Extract structured data from each detected section using section-specific prompts.

```python
from fedops_core.services.document_extractor import DocumentExtractor

extractor = DocumentExtractor()

# For single-document with detected sections:
for section in sections:
    if section.section_letter == "L":
        result = extractor.extract_section_l(section.content)
    elif section.section_letter == "M":
        result = extractor.extract_section_m(section.content)
    elif section.section_letter == "C":
        result = extractor.extract_sow(section.content)
    # ... etc.
```

---

## Step 5: Requirement Extraction

Extract requirements from Section C (SOW) with categorization.

Requirements are stored in `extracted_requirements` table with:
- `requirement_id`: e.g., "C_156_1"
- `requirement_text`: Full requirement text
- `category`: FUNCTIONAL, TECHNICAL, COMPLIANCE, etc.
- `compliance_level`: MANDATORY, CONDITIONAL, OPTIONAL

---

## Step 6: Evaluation Mapping

Map Section M evaluation criteria to Section C requirements.

Stored in `evaluation_mappings` table with:
- `evaluation_factor`: e.g., "Technical Approach (40%)"
- `weight_percent`: Numeric weight
- `related_requirement_ids`: Array of requirement IDs

---

## Step 7: Summary Generation

Generate summaries for each section for quick review.

Stored in `section_summaries` table with:
- `summary_text`: 2-3 sentence summary
- `key_findings`: Array of key findings
- `red_flags`: Array of risks/concerns
- `questions_to_ask`: Clarification questions

---

## API Endpoints

### Classify Opportunity

```
POST /api/v1/opportunities/{opportunity_id}/classify
```

Triggers classification and returns the DocumentClassification record.

### Get Classification

```
GET /api/v1/opportunities/{opportunity_id}/classification
```

Returns existing classification for an opportunity.

### Get Sections

```
GET /api/v1/opportunities/{opportunity_id}/sections
```

Returns all detected sections for an opportunity.

### Reclassify

```
POST /api/v1/opportunities/{opportunity_id}/reclassify
```

Force re-classification (deletes existing and runs again).

---

## Database Tables

| Table | Purpose |
|-------|---------|
| `document_classifications` | Stores SINGLE/MULTI/HYBRID classification per opportunity |
| `document_sections` | Stores detected section boundaries (A-M) |
| `section_summaries` | AI-generated summaries for each section |
| `extracted_requirements` | Individual requirements from sections |
| `evaluation_mappings` | Section M criteria mapped to requirements |

---

## Troubleshooting

### Classification returns HYBRID when it should be SINGLE

Check if amendment files are not being detected. Add patterns to `AMENDMENT_PATTERNS` in `classification_service.py` if needed.

### Section boundaries are incorrect

Use `reclassify_opportunity()` to force re-detection. If consistently wrong, the document may have non-standard section headers.

### Missing sections

Some sections (D, E, G) are rarely used in modern solicitations. If critical sections (L, M, C) are missing, check the document format.
