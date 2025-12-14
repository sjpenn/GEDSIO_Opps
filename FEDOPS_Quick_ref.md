# FedOps Quick Reference: Model Selection & Structured Prompts
## At-a-Glance Implementation Guide

**Version**: 1.0  
**Date**: December 2025  
**For**: GEDSIO LLC FedOps Application  

---

## QUICK MODEL SELECTION MATRIX

### Which Model for Which Task?

| Task | Primary Model | Schema | Example Use Case |
|------|---------------|--------|------------------|
| **Extract PDF text/tables** | `claude-3-5-sonnet-20241022` | `ExtractedDocument` | Government contracts, RFPs |
| **Analyze compliance** | `claude-3-5-sonnet-20241022` | `DocumentAnalysis` | FAR/DFARS compliance gaps |
| **Write proposal** | `claude-3-5-sonnet-20241022` | `ProposalSection` | RFP response narratives |
| **Extract references** | `claude-3-5-sonnet-20241022` | `ReferenceExtraction` | FAR/DFARS/NIST citations |
| **Complex analysis** | `claude-opus-4-20250805` | `DocumentAnalysis` | Multi-document synthesis |
| **Creative proposals** | `gpt-4.5-turbo` | `ProposalSection` | Innovation narratives |
| **Vision/OCR** | `claude-3-5-sonnet-20241022` | `OCRExtraction` | Scanned forms, images |
| **Complex layouts** | `Qwen 3-VL` (local) | `OCRExtraction` | Multi-column regulations |

---

## STRUCTURED OUTPUT SCHEMAS AT A GLANCE

### 1. ExtractedDocument (Extraction Layer Output)
```python
{
  "document_id": "CONTRACT_001",
  "title": "GSA Contract 123",
  "full_text": "...",  # Complete extracted text
  "sections": [...],  # Hierarchical document structure
  "tables": [...],    # All tables with structure preserved
  "text_chunks": [...],  # Pre-chunked for analysis
  "extraction_quality_score": 0.94,  # 0-1
  "metadata": {
    "source_file": "contract.pdf",
    "extraction_tool": "docling",
    "total_pages": 45,
    "text_confidence": 0.98
  }
}
```

### 2. DocumentAnalysis (Analysis Layer Output)
```python
{
  "document_id": "CONTRACT_001",
  "compliance_requirements": [
    {
      "requirement_id": "REQ_001",
      "requirement_text": "Contractor shall implement NIST SP 800-171",
      "category": "security",
      "severity": "CRITICAL",
      "regulatory_framework": "NIST",
      "page_reference": 5,
      "confidence": 0.95
    }
  ],
  "regulatory_references": [...],  # FAR, DFARS, NIST citations
  "risks": [...],  # Risk assessment with scores
  "contract_metadata": {
    "contract_type": "Fixed-Price",
    "parties": ["Government", "Contractor Name"],
    "contract_value": 500000,
    "performance_start_date": "2025-01-01"
  },
  "executive_summary": "Contract requiring...",  # 400-500 words
  "compliance_readiness": 65,  # 0-100 score
  "analysis_confidence": 0.92
}
```

### 3. ReferenceExtraction (Complete Reference Catalog)
```python
{
  "far_citations": [
    {
      "citation": "48 CFR 52.204-21",
      "title": "Basic Safeguards of Contractor...",
      "context": "Flow-down requirement",
      "impact_level": "CRITICAL"
    }
  ],
  "dfars_citations": [...],
  "iso_standards": [...],
  "nist_standards": [...],
  "external_documents": [...],
  "total_references_found": 47,
  "critical_references": [
    "48 CFR 52.204-21",
    "DFARS 252.204-7012"
  ],
  "regulatory_framework": "FAR/DFARS hybrid",
  "compliance_complexity": "High"
}
```

### 4. ProposalSection (Writing Layer Output)
```python
{
  "section_title": "Technical Approach",
  "requirement_reference": "3.1.2",
  "body": "GEDSIO will implement...",  # 2000+ words
  "key_differentiators": [
    "AI-driven compliance automation",
    "99.2% extraction accuracy",
    "Federal-grade security"
  ],
  "past_performance_examples": [
    "Project ALPHA: Processed 50K documents",
    "Project BETA: Achieved 95% compliance gap detection"
  ],
  "compliance_statements": [
    "Will comply with NIST SP 800-171",
    "Security assessments annual"
  ],
  "readability_score": 8.4,  # Flesch-Kincaid
  "tone": "professional"
}
```

### 5. OCRExtraction (Vision Layer Output)
```python
{
  "extracted_text": "All legible text from image...",
  "ocr_confidence": 0.95,  # 0-1
  "document_type_detected": "Government Form",
  "form_number": "SF-86",
  "form_fields": {
    "Name": "John Doe",
    "SSN": "XXX-XX-1234",
    "Date": "2025-01-15"
  },
  "illegible_sections": [],
  "image_quality": "Excellent",
  "required_fields_missing": []
}
```

---

## SYSTEM PROMPTS QUICK REFERENCE

### Extraction Layer
**Role**: Document structure extractor  
**Goal**: Preserve exact text, structure, tables  
**Constraint**: No interpretation, only extraction  
**Output**: ExtractedDocument JSON

### Analysis Layer
**Role**: Federal compliance analyst  
**Goal**: Identify all compliance requirements, regulatory references, risks  
**Expertise**: FAR, DFARS, NIST, CMMC, government contracting  
**Output**: DocumentAnalysis + ReferenceExtraction JSON

### Writing Layer
**Role**: Federal proposal writer (GEDSIO perspective)  
**Goal**: Create compelling, compliant proposal responses  
**Voice**: Professional, specific, evidence-based  
**Output**: ProposalSection JSON

### Vision Layer
**Role**: OCR and form extraction specialist  
**Goal**: Extract text and structured data from images/scans  
**Specialty**: Government forms (SF-86, SAM, CMMC)  
**Output**: OCRExtraction JSON

---

## IMPLEMENTATION CHECKLIST (COPY-PASTE READY)

### Week 1: Setup & Configuration
```
□ Create Python virtual environment
□ Install packages (anthropic, docling, pydantic, etc.)
□ Configure .env with API keys
□ Setup logging and audit trail
□ Load YAML configuration
□ Create output directories (outputs/, logs/)
```

### Week 2: Test Each Layer
```
□ Test extraction layer on 3 sample contracts
□ Test analysis layer - verify 10+ requirements found
□ Test reference extraction - confirm FAR/DFARS citations
□ Test vision layer on scanned government form
□ Validate all outputs against schemas (zero JSON errors)
□ Record confidence scores for each test
```

### Week 3: Optimize & Benchmark
```
□ Benchmark extraction quality (vs manual gold standard)
□ Compare analysis completeness (requirements count)
□ Measure proposal readability (target 8.0+)
□ Track API costs per document type
□ Set up cost monitoring dashboard
□ Establish confidence thresholds (70% minimum)
```

### Week 4: Production Deployment
```
□ Finalize all Pydantic schemas
□ Enable Structured Outputs beta header
□ Implement error handling + fallbacks
□ Setup audit logging for federal compliance
□ Create quality metrics dashboard
□ Test end-to-end workflow (extract → analyze → propose)
□ Document all prompts in prompts.md
□ Deploy to production environment
```

---

## COMMON PROMPT PATTERNS

### Pattern 1: Extraction with Quality Check
```
SYSTEM: [Extraction Layer System Prompt from Part 2.1]

USER:
Extract this government contract with precision.
Preserve all structure: headings, lists, tables, citations.
Return ExtractedDocument JSON.

DOCUMENT TEXT:
[contract text here]
```

**Expected Output**: ExtractedDocument with quality_score 0.85+

---

### Pattern 2: Compliance Analysis with Chain-of-Thought
```
SYSTEM: [Analysis Layer System Prompt from Part 2.2]

USER:
Analyze this contract for:
1. Compliance requirements (explicit obligations)
2. Regulatory references (FAR, DFARS, NIST)
3. Risk assessment (likelihood × impact)
4. Executive summary (400-500 words)

DOCUMENT:
[extracted document JSON]

Return DocumentAnalysis JSON.
```

**Expected Output**: 15+ requirements, FAR/DFARS citations, risk scores

---

### Pattern 3: Proposal Generation with Requirement Mapping
```
SYSTEM: [Writing Layer System Prompt from Part 2.3]

USER:
RFP REQUIREMENT:
[3.1.2 Technical Approach text]

COMPLIANCE CONTEXT:
- NIST SP 800-171 required
- Annual audits mandatory
- Data handling restrictions

PAST PERFORMANCE:
- Project ALPHA: 50K documents, 99.2% accuracy

Generate compelling 2000+ word proposal response mapping 
to requirement [3.1.2]. Include competitive differentiators.
Return ProposalSection JSON.
```

**Expected Output**: ProposalSection with body, differentiators, readability 8.0+

---

### Pattern 4: Vision/OCR for Scanned Forms
```
SYSTEM: [Vision Layer System Prompt from Part 2.4]

USER:
This is a scanned SF-86 security clearance form.
Extract all form fields and values.
Note any illegible sections or missing required fields.

[IMAGE - base64 encoded]

Return OCRExtraction JSON.
```

**Expected Output**: OCRExtraction with form_fields extracted, confidence 0.90+

---

## STRUCTURED OUTPUTS API USAGE

### Enable Beta Header
```python
headers = {
    "anthropic-beta": "structured-outputs-2025-11-13"
}
```

### Make Request with Schema
```python
response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=4096,
    messages=[{
        "role": "user",
        "content": "Extract this document..."
    }],
    # NEW: Structured outputs
    output_format={
        "type": "json",
        "schema": ExtractedDocument.model_json_schema()
    }
)

# Parse guaranteed-valid JSON
result = ExtractedDocument(**json.loads(response.content[0].text))
```

**Benefit**: Zero JSON parsing errors. Schema validation guaranteed.

---

## COST OPTIMIZATION QUICK TIPS

| Action | Savings | Difficulty |
|--------|---------|------------|
| Use Claude 3.5 instead of Opus for routine tasks | 5x cheaper | Easy |
| Batch small documents together | 20% reduction | Medium |
| Use local Qwen Vision for complex layouts | 100% free | Medium |
| Cache FAR/DFARS reference lookups | 30% reduction | Hard |
| Reuse extraction across multiple analyses | 40% reduction | Medium |

**Estimated cost per contract**: $1-2 with optimization

---

## TROUBLESHOOTING DECISION TREE

### Problem: Low Extraction Confidence (<0.70)
→ **Check**: Is the PDF scanned/poor quality?  
→ **If yes**: Try vision model instead  
→ **If no**: Flag for manual review or use fallback (pypdfium2)  

### Problem: Missing Compliance Requirements
→ **Check**: Is compliance_readiness score low?  
→ **If yes**: Run reference extraction separately  
→ **If no**: Ask Claude to re-analyze with specific frameworks (FAR, DFARS, NIST)  

### Problem: Low Proposal Readability (<8.0)
→ **Check**: Is word count too high?  
→ **If yes**: Reduce verbosity or split into multiple sections  
→ **If no**: Use GPT-4.5 for polishing (creative rewrite)  

### Problem: Vision OCR Confidence Low (<0.80)
→ **Check**: Is image too small/blurry?  
→ **If yes**: Recommend rescanning at 300+ DPI  
→ **If no**: Try Qwen 3-VL locally (better for complex layouts)  

---

## FEDERAL COMPLIANCE REQUIREMENTS

### Audit Trail (Required for Government Contracts)
```python
audit_log("EXTRACTION_COMPLETE", contract_id, {
    "tool": "docling",
    "quality": 0.94,
    "timestamp": datetime.utcnow().isoformat(),
    "status": "success"
})
```

### Model Transparency
Document which model processed what:
- Extraction: Docling (MIT licensed) + Claude
- Analysis: Claude 3.5 Sonnet (Anthropic)
- Writing: Claude 3.5 Sonnet (Anthropic)
- Vision: Claude 3.5 Vision (Anthropic)

### Confidence Scoring
All outputs must include confidence (0-1):
- Flag for review if < 0.70
- Use honest assessment (not inflated)
- Calibrate per task type

---

## ONE-LINER COMMANDS

```bash
# Test extraction
python -c "from fedops_pipeline import FedOpsPipeline; p = FedOpsPipeline('key'); print(p.extract_document(text, 'TEST_001'))"

# Check costs YTD
grep "cost_usd" logs/api_costs.jsonl | awk '{sum+=$NF} END {print "Total: $" sum}'

# View audit trail
tail -20 logs/audit_trail.jsonl | jq '.'

# Count FAR citations found
grep "far_citations" outputs/*_references.json | wc -l
```

---

## GETTING HELP

### Refer to Full Documentation
- **Prompts & Schemas**: `fedops-prompts.md`
- **Implementation Examples**: `fedops-implementation.md`
- **Architecture**: `Hybrid Document Processing Pipeline.md` (main guide)

### Common Questions

**Q: Which model is cheapest?**  
A: Claude 3.5 Sonnet ($3/$15 per 1M tokens). GPT-4.5 is 5x more expensive.

**Q: How do I ensure federal compliance?**  
A: Enable audit logging, document model choices, score all outputs for confidence.

**Q: Can I use local models?**  
A: Yes - Docling (extraction) and Qwen 3-VL (vision) run locally for free.

**Q: What if a document has low confidence?**  
A: Flag for manual review, try fallback tool, or use vision model if scanned.

**Q: How do I improve proposal quality?**  
A: Use readability scoring (8.0+ target), iterate with GPT-4.5, validate compliance coverage.

---

## NEXT STEPS

1. **Copy fedops-prompts.md** into your FedOps application
2. **Implement each schema** from Part 1 (Pydantic models)
3. **Test extraction layer** on 3 sample contracts
4. **Deploy analysis layer** and validate requirements found
5. **Build proposal generation** with system prompt + examples
6. **Enable structured outputs** beta header in API calls
7. **Setup audit logging** for federal compliance
8. **Monitor costs** with cost_tracking.py
9. **Go production** when all quality checks pass

---

**Version**: 1.0  
**Status**: Production-Ready  
**Last Updated**: December 13, 2025  
**Author**: Steve Penn, GEDSIO LLC

For updates, refer to main architecture document: `Hybrid Document Processing Pipeline: Model Selection & Architecture Guide`
