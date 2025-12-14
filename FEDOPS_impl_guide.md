# FedOps Implementation Guide: Real-World Examples
## Complete Walkthrough with Code Snippets

**Version**: 1.0  
**Companion to**: fedops-prompts.md  
**Date**: December 2025

---

## TABLE OF CONTENTS

1. [Setup & Configuration](#setup--configuration)
2. [End-to-End Workflow Examples](#end-to-end-workflow-examples)
3. [Integration with Docling + Orchestration](#integration-with-docling--orchestration)
4. [Testing & Quality Validation](#testing--quality-validation)
5. [Monitoring & Audit Trails](#monitoring--audit-trails)
6. [Troubleshooting Common Issues](#troubleshooting-common-issues)

---

## SETUP & CONFIGURATION

### Environment Setup

```bash
# Create virtual environment
python3 -m venv fedops-env
source fedops-env/bin/activate

# Install dependencies
pip install \
  anthropic>=0.25.0 \
  openai>=1.0.0 \
  docling>=1.11.0 \
  pypdfium2>=4.20.0 \
  pydantic>=2.0 \
  python-dotenv>=1.0.0 \
  pyyaml>=6.0

# Create .env file
cat > .env << EOF
ANTHROPIC_API_KEY=sk-ant-xxxxx
OPENAI_API_KEY=sk-xxxxx
LOG_LEVEL=INFO
EOF

chmod 600 .env
```

### Configuration File (config.yaml)

```yaml
# config/fedops_config.yaml

fedops:
  name: "GEDSIO FedOps Pipeline"
  version: "1.0"
  
models:
  primary:
    extraction: "claude-3-5-sonnet-20241022"
    analysis: "claude-3-5-sonnet-20241022"
    writing: "claude-3-5-sonnet-20241022"
  secondary:
    complex_analysis: "claude-opus-4-20250805"
    creative_writing: "gpt-4.5-turbo"
  vision:
    primary: "claude-3-5-sonnet-20241022"  # Has vision capability
    advanced: "qwen-vl-7b"  # For complex layouts

extraction:
  tools:
    primary: "docling"
    fallback: "pypdfium2"
  chunk_size: 4000  # tokens
  chunk_overlap: 200

analysis:
  confidence_threshold: 0.70  # Flag for review if below
  max_requirements_per_doc: 50
  compliance_frameworks:
    - FAR
    - DFARS
    - NIST
    - ISO
    - CMMC

writing:
  proposal_word_count_target: 2500
  readability_target: 8.0  # Flesch-Kincaid
  tone: "professional"

logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  audit_trail: true
  audit_file: "logs/audit_trail.jsonl"

api:
  max_retries: 3
  timeout_seconds: 60
  structured_outputs_beta: true
  beta_header: "structured-outputs-2025-11-13"
```

### Logger Configuration

```python
# logging_config.py

import logging
import logging.config
from datetime import datetime
import json
from pathlib import Path

def setup_logging(config_file: str = "config/fedops_config.yaml"):
    """Configure logging for FedOps pipeline"""
    
    import yaml
    with open(config_file) as f:
        config = yaml.safe_load(f)
    
    log_level = config['logging']['level']
    log_format = config['logging']['format']
    
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(f"logs/fedops_{datetime.now().strftime('%Y%m%d')}.log")
        ]
    )
    
    return logging.getLogger(__name__)

def audit_log(event_type: str, document_id: str, details: dict):
    """Write audit trail entry (required for federal compliance)"""
    
    audit_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": event_type,
        "document_id": document_id,
        "details": details
    }
    
    Path("logs").mkdir(exist_ok=True)
    with open("logs/audit_trail.jsonl", "a") as f:
        f.write(json.dumps(audit_entry) + "\n")
```

---

## END-TO-END WORKFLOW EXAMPLES

### Example 1: Government Contract Analysis (Complete Flow)

```python
# examples/analyze_government_contract.py

import os
import json
from pathlib import Path
from datetime import datetime
from docling.document_converter import DocumentConverter
from fedops_pipeline import FedOpsPipeline
from schemas.extraction import ExtractedDocument
from schemas.analysis import DocumentAnalysis
from logging_config import setup_logging, audit_log

logger = setup_logging()

def analyze_contract_end_to_end(pdf_path: str, contract_id: str):
    """
    Complete workflow: Extract → Analyze → Reference Extract → Summary
    """
    
    logger.info(f"Starting contract analysis for {contract_id}")
    audit_log("WORKFLOW_START", contract_id, {"pdf_path": pdf_path})
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # PHASE 1: EXTRACTION WITH DOCLING
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    logger.info(f"Phase 1: Extracting document with Docling")
    try:
        # Use Docling for structure preservation
        converter = DocumentConverter()
        doc = converter.convert(pdf_path)
        
        # Export to markdown (preserves structure)
        extracted_text = doc.export_to_markdown()
        
        logger.info(f"✓ Docling extraction successful. {len(extracted_text)} chars extracted")
        audit_log("EXTRACTION_COMPLETE", contract_id, {
            "tool": "docling",
            "extracted_chars": len(extracted_text),
            "status": "success"
        })
        
    except Exception as e:
        logger.warning(f"Docling failed: {e}. Falling back to pypdfium2")
        # Fallback implementation here
        audit_log("EXTRACTION_FALLBACK", contract_id, {"error": str(e)})
        raise
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # PHASE 2: STRUCTURED EXTRACTION WITH CLAUDE
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    logger.info(f"Phase 2: Structuring document with Claude (Extraction Layer)")
    
    pipeline = FedOpsPipeline(api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    extraction: ExtractedDocument = pipeline.extract_document(
        document_text=extracted_text,
        document_id=contract_id,
        extraction_tool="docling"
    )
    
    logger.info(f"✓ Extraction structured. Quality score: {extraction.extraction_quality_score}")
    
    # Save extraction for audit trail
    extraction_file = f"outputs/{contract_id}_extraction.json"
    Path("outputs").mkdir(exist_ok=True)
    with open(extraction_file, "w") as f:
        json.dump(json.loads(extraction.model_dump_json()), f, indent=2)
    
    audit_log("EXTRACTION_STRUCTURED", contract_id, {
        "quality_score": extraction.extraction_quality_score,
        "sections_found": len(extraction.sections),
        "tables_found": len(extraction.tables),
        "output_file": extraction_file
    })
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # PHASE 3: COMPLIANCE ANALYSIS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    logger.info(f"Phase 3: Analyzing compliance requirements")
    
    analysis: DocumentAnalysis = pipeline.analyze_document(extraction)
    
    logger.info(
        f"✓ Analysis complete. "
        f"Requirements: {len(analysis.compliance_requirements)}, "
        f"References: {len(analysis.regulatory_references)}, "
        f"Risks: {len(analysis.risks)}"
    )
    
    # Save analysis
    analysis_file = f"outputs/{contract_id}_analysis.json"
    with open(analysis_file, "w") as f:
        json.dump(json.loads(analysis.model_dump_json()), f, indent=2)
    
    audit_log("ANALYSIS_COMPLETE", contract_id, {
        "compliance_requirements": len(analysis.compliance_requirements),
        "regulatory_references": len(analysis.regulatory_references),
        "risks": len(analysis.risks),
        "compliance_readiness": analysis.compliance_readiness,
        "output_file": analysis_file
    })
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # PHASE 4: VERBOSE REFERENCE EXTRACTION
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    logger.info(f"Phase 4: Extracting all regulatory references")
    
    references = pipeline.extract_all_references(
        document_text=extraction.full_text,
        document_id=contract_id
    )
    
    logger.info(f"✓ References extracted. Total: {references.total_references_found}")
    
    # Save references
    references_file = f"outputs/{contract_id}_references.json"
    with open(references_file, "w") as f:
        json.dump(json.loads(references.model_dump_json()), f, indent=2)
    
    audit_log("REFERENCES_EXTRACTED", contract_id, {
        "total_references": references.total_references_found,
        "far_count": len(references.far_citations),
        "dfars_count": len(references.dfars_citations),
        "standards_count": len(references.iso_standards) + len(references.nist_standards),
        "output_file": references_file
    })
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # PHASE 5: QUALITY VALIDATION
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    logger.info(f"Phase 5: Validating output quality")
    
    requires_review = analysis.analysis_confidence < 0.70
    if requires_review:
        logger.warning(f"⚠ Low confidence ({analysis.analysis_confidence}). Flagging for manual review")
        audit_log("QUALITY_FLAG", contract_id, {
            "confidence": analysis.analysis_confidence,
            "reason": "Below 0.70 threshold",
            "review_notes": analysis.review_notes
        })
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # GENERATE SUMMARY REPORT
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    summary_report = {
        "contract_id": contract_id,
        "analysis_timestamp": datetime.utcnow().isoformat(),
        "extraction": {
            "pages": extraction.metadata.total_pages,
            "quality_score": extraction.extraction_quality_score,
            "tables_found": len(extraction.tables),
            "confidence": extraction.metadata.text_confidence
        },
        "analysis": {
            "contract_type": analysis.contract_metadata.contract_type if analysis.contract_metadata else "Unknown",
            "compliance_readiness": analysis.compliance_readiness,
            "complexity": analysis.overall_complexity,
            "requirements": len(analysis.compliance_requirements),
            "risks": len(analysis.risks),
            "confidence": analysis.analysis_confidence
        },
        "references": {
            "total": references.total_references_found,
            "far_citations": len(references.far_citations),
            "dfars_citations": len(references.dfars_citations),
            "standards": len(references.iso_standards) + len(references.nist_standards)
        },
        "actions_required": {
            "requires_manual_review": requires_review,
            "critical_gaps": analysis.critical_gaps,
            "top_risks": [r.title for r in analysis.risks[:3]]
        },
        "output_files": {
            "extraction": extraction_file,
            "analysis": analysis_file,
            "references": references_file
        }
    }
    
    # Save summary
    summary_file = f"outputs/{contract_id}_summary.json"
    with open(summary_file, "w") as f:
        json.dump(summary_report, f, indent=2)
    
    audit_log("WORKFLOW_COMPLETE", contract_id, {
        "status": "success",
        "summary_file": summary_file,
        "requires_review": requires_review
    })
    
    logger.info(f"✓ Workflow complete. Summary saved to {summary_file}")
    
    return {
        "extraction": extraction,
        "analysis": analysis,
        "references": references,
        "summary": summary_report,
        "status": "success"
    }

if __name__ == "__main__":
    # Example usage
    result = analyze_contract_end_to_end(
        pdf_path="contracts/sample_contract.pdf",
        contract_id="CONTRACT_FY2025_001"
    )
    
    print("\n" + "="*60)
    print("CONTRACT ANALYSIS SUMMARY")
    print("="*60)
    print(json.dumps(result["summary"], indent=2))
```

### Example 2: Generating Proposal Response (RFP-Driven)

```python
# examples/generate_proposal_response.py

from fedops_pipeline import FedOpsPipeline
from schemas.analysis import DocumentAnalysis
from schemas.writing import ProposalSection
import os
import json

def generate_proposal_for_rfp(rfp_requirement: str, requirement_number: str, 
                              analysis: DocumentAnalysis):
    """
    Generate one proposal section in response to RFP requirement
    """
    
    pipeline = FedOpsPipeline(api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    # Gather relevant context
    relevant_compliance = [
        req for req in analysis.compliance_requirements 
        if "technical" in req.category.lower() or "approach" in req.category.lower()
    ]
    
    past_performance = [
        "Project ALPHA: Implemented AI-driven document extraction for federal contractor, "
        "processing 50K government contracts with 99.2% accuracy, saving 200 hours/month",
        "Project BETA: Built compliance analysis platform for GSA contractor, "
        "identifying 95% of compliance gaps before contract execution"
    ]
    
    proposal = pipeline.generate_proposal_section(
        rfp_requirement=rfp_requirement,
        requirement_number=requirement_number,
        analysis=analysis,
        past_performance=past_performance
    )
    
    return proposal

def build_complete_proposal(rfp_document: str, rfp_id: str):
    """
    Build complete proposal from RFP requirements
    """
    
    # Parse RFP into individual requirements
    requirements = parse_rfp_sections(rfp_document)
    
    proposal_sections = []
    
    for req_num, req_text in requirements.items():
        print(f"Generating section {req_num}...")
        
        section = generate_proposal_for_rfp(
            rfp_requirement=req_text,
            requirement_number=req_num,
            analysis=get_analysis(rfp_id)
        )
        
        proposal_sections.append({
            "section_number": req_num,
            "section": section.model_dump()
        })
    
    # Compile into proposal document
    proposal_output = {
        "rfp_id": rfp_id,
        "generated_timestamp": datetime.utcnow().isoformat(),
        "sections": proposal_sections,
        "total_word_count": sum(len(s["section"]["body"].split()) for s in proposal_sections),
        "average_readability": sum(s["section"]["readability_score"] for s in proposal_sections) / len(proposal_sections)
    }
    
    # Save proposal
    output_file = f"outputs/{rfp_id}_proposal.json"
    with open(output_file, "w") as f:
        json.dump(proposal_output, f, indent=2)
    
    return proposal_output
```

---

## INTEGRATION WITH DOCLING + ORCHESTRATION

### Docling + Claude Hybrid Extraction

```python
# integration/docling_claude_integration.py

from docling.document_converter import DocumentConverter
from docling.pipeline.document_pipeline import DocumentPipeline
from docling.models import DocumentConvertSettings
from anthropic import Anthropic
import json

class DoclingClaudeExtractor:
    """
    Hybrid approach: Docling for structure, Claude for semantic understanding
    """
    
    def __init__(self, api_key: str):
        self.converter = DocumentConverter()
        self.client = Anthropic(api_key=api_key)
    
    def extract_with_semantic_understanding(self, pdf_path: str):
        """
        1. Extract structure with Docling
        2. Ask Claude to understand semantics and complete extraction
        """
        
        # Step 1: Raw extraction with Docling
        doc = self.converter.convert(pdf_path)
        docling_output = doc.export_to_markdown()
        
        # Step 2: Have Claude understand the semantics
        response = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2048,
            system="You are a semantic understanding agent. Analyze extracted text and identify key semantic units.",
            messages=[{
                "role": "user",
                "content": f"""
                This is extracted document text from Docling. 
                Identify and extract:
                1. Document type/purpose
                2. Key entities (people, organizations, dates)
                3. Semantic sections (even if Docling missed heading structure)
                4. Important claims/assertions
                5. Data relationships
                
                Text:
                {docling_output}
                
                Respond as JSON.
                """
            }]
        )
        
        semantic_analysis = json.loads(response.content[0].text)
        
        return {
            "docling_extraction": docling_output,
            "semantic_analysis": semantic_analysis,
            "combined": {
                "structure": docling_output,
                "semantics": semantic_analysis
            }
        }
```

### DocETL Pipeline Integration

```python
# integration/docetl_integration.py

import yaml
import json
from pathlib import Path

class DocETLPipelineExecutor:
    """
    Execute DocETL YAML pipeline for complex document orchestration
    """
    
    def __init__(self, yaml_config_path: str):
        with open(yaml_config_path) as f:
            self.pipeline_spec = yaml.safe_load(f)
    
    def execute_pipeline(self, input_document: str) -> dict:
        """
        Execute multi-stage DocETL pipeline
        
        Stages:
        1. Split into chunks (Map)
        2. Extract metadata (Map)
        3. Consolidate across chunks (Gather)
        4. Extract references (Map)
        5. Validate quality (Filter)
        """
        
        results = {
            "pipeline": self.pipeline_spec["name"],
            "stages": []
        }
        
        # Example DocETL YAML from prompts file would be executed here
        # For this example, we show the structure
        
        return results
```

---

## TESTING & QUALITY VALIDATION

### Unit Tests for Schemas

```python
# tests/test_schemas.py

import pytest
from datetime import datetime
from schemas.extraction import ExtractedDocument, ExtractedTable, DocumentSection
from schemas.analysis import DocumentAnalysis, ComplianceRequirement, RiskAssessment
from schemas.writing import ProposalSection, ContractSummary

def test_extracted_table_schema():
    """Test table extraction schema"""
    
    table = ExtractedTable(
        title="Price Schedule",
        headers=["Item", "Unit Price", "Quantity"],
        rows=[
            ["Labor - Senior Developer", "150", "1000"],
            ["Travel", "500", "10"]
        ],
        row_count=2,
        col_count=3,
        confidence=0.95
    )
    
    assert table.row_count == 2
    assert table.col_count == 3
    assert table.confidence == 0.95
    
    # Test serialization
    json_str = table.model_dump_json()
    assert "Price Schedule" in json_str

def test_compliance_requirement_schema():
    """Test compliance requirement extraction"""
    
    req = ComplianceRequirement(
        requirement_id="REQ_001",
        requirement_text="Contractor shall implement NIST SP 800-171 controls",
        category="security",
        severity="CRITICAL",
        applicable_to=["contractor"],
        regulatory_framework="NIST",
        page_reference=5,
        confidence=0.95
    )
    
    assert req.severity == "CRITICAL"
    assert req.regulatory_framework == "NIST"
    
    # Validate confidence is 0-1
    assert 0 <= req.confidence <= 1

def test_proposal_section_schema():
    """Test proposal section generation"""
    
    proposal = ProposalSection(
        section_title="Technical Approach",
        requirement_reference="3.1.2",
        body="GEDSIO will implement...",  # Full proposal text
        key_differentiators=["AI-driven compliance"],
        tone="professional",
        readability_score=8.2
    )
    
    assert proposal.readability_score > 8.0
    assert len(proposal.key_differentiators) > 0

def test_confidence_thresholds():
    """Validate confidence scoring"""
    
    # Test that confidence values are properly bounded
    schemas_to_test = [
        ("high", 0.95),
        ("medium", 0.70),
        ("low", 0.50)
    ]
    
    for label, confidence_value in schemas_to_test:
        req = ComplianceRequirement(
            requirement_id=f"REQ_{label}",
            requirement_text="Test",
            category="test",
            severity="LOW",
            applicable_to=["test"],
            regulatory_framework="TEST",
            page_reference=1,
            confidence=confidence_value
        )
        
        assert 0 <= req.confidence <= 1
```

### Integration Tests

```python
# tests/test_integration.py

import pytest
from fedops_pipeline import FedOpsPipeline
import os

@pytest.fixture
def pipeline():
    """Initialize pipeline for tests"""
    return FedOpsPipeline(api_key=os.getenv("ANTHROPIC_API_KEY"))

def test_extraction_roundtrip(pipeline):
    """Test that extraction produces valid schema"""
    
    sample_text = """
    CONTRACT NO. GS-07F-1234
    
    1. SCOPE OF WORK
    The Contractor shall provide AI-driven document processing services.
    
    2. COMPLIANCE REQUIREMENTS
    - NIST SP 800-171 compliance required
    - Annual security assessment mandatory
    """
    
    extraction = pipeline.extract_document(
        document_text=sample_text,
        document_id="TEST_001",
        extraction_tool="docling"
    )
    
    assert extraction.document_id == "TEST_001"
    assert extraction.extraction_quality_score > 0.7
    assert len(extraction.full_text) > 0

def test_analysis_produces_requirements(pipeline):
    """Test that analysis extracts compliance requirements"""
    
    # This would use the extraction from above
    # Then call analyze_document()
    pass

def test_reference_extraction_finds_far_citations(pipeline):
    """Test that FAR citations are extracted"""
    
    contract_text = """
    Per FAR 48 CFR 52.204-21, contractors must implement NIST standards.
    DFARS 252.204-7012 applies to IT security requirements.
    """
    
    references = pipeline.extract_all_references(
        document_text=contract_text,
        document_id="TEST_002"
    )
    
    assert len(references.far_citations) > 0
    assert any("52.204-21" in ref.citation for ref in references.far_citations)
```

---

## MONITORING & AUDIT TRAILS

### Cost Tracking

```python
# monitoring/cost_tracking.py

import json
from datetime import datetime
from pathlib import Path

class CostTracker:
    """Track API costs for budget monitoring"""
    
    def __init__(self, budget_per_month_usd: float = 500):
        self.budget = budget_per_month_usd
        self.costs_log = "logs/api_costs.jsonl"
        Path("logs").mkdir(exist_ok=True)
    
    def log_api_call(self, model: str, input_tokens: int, output_tokens: int):
        """Log API call and calculate cost"""
        
        # Claude 3.5 Sonnet pricing (Dec 2025)
        pricing = {
            "claude-3-5-sonnet-20241022": {
                "input": 3.0 / 1_000_000,  # $3 per 1M tokens
                "output": 15.0 / 1_000_000  # $15 per 1M tokens
            }
        }
        
        price_info = pricing.get(model, pricing["claude-3-5-sonnet-20241022"])
        
        cost = (input_tokens * price_info["input"]) + (output_tokens * price_info["output"])
        
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost_usd": round(cost, 4)
        }
        
        with open(self.costs_log, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
        
        return cost
    
    def get_month_to_date_cost(self) -> float:
        """Calculate current month's spending"""
        
        if not Path(self.costs_log).exists():
            return 0.0
        
        total = 0.0
        current_month = datetime.utcnow().month
        current_year = datetime.utcnow().year
        
        with open(self.costs_log) as f:
            for line in f:
                entry = json.loads(line)
                entry_date = datetime.fromisoformat(entry["timestamp"])
                
                if entry_date.month == current_month and entry_date.year == current_year:
                    total += entry["cost_usd"]
        
        return round(total, 2)
    
    def budget_alert(self):
        """Alert if approaching budget"""
        
        mtd_cost = self.get_month_to_date_cost()
        percent_used = (mtd_cost / self.budget) * 100
        
        if percent_used >= 90:
            return {
                "alert": True,
                "message": f"⚠ Budget alert: {percent_used:.1f}% of ${self.budget}/month used",
                "cost_mtd": mtd_cost,
                "budget": self.budget
            }
        
        return {"alert": False, "cost_mtd": mtd_cost, "budget": self.budget}
```

### Quality Metrics Dashboard

```python
# monitoring/quality_metrics.py

import json
from datetime import datetime
from collections import defaultdict
from pathlib import Path

class QualityMetrics:
    """Track extraction, analysis, and writing quality"""
    
    def __init__(self):
        self.metrics_file = "logs/quality_metrics.jsonl"
    
    def record_extraction_quality(self, document_id: str, quality_score: float, 
                                  extraction_tool: str, page_count: int):
        """Record extraction quality"""
        
        metric = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": "extraction",
            "document_id": document_id,
            "quality_score": quality_score,
            "tool": extraction_tool,
            "pages": page_count
        }
        
        self._write_metric(metric)
    
    def record_analysis_quality(self, document_id: str, confidence: float,
                                requirements_found: int, risks_found: int):
        """Record analysis quality"""
        
        metric = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": "analysis",
            "document_id": document_id,
            "confidence": confidence,
            "requirements": requirements_found,
            "risks": risks_found
        }
        
        self._write_metric(metric)
    
    def record_proposal_quality(self, section_id: str, readability: float,
                                compliance_coverage: float):
        """Record proposal quality"""
        
        metric = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": "proposal",
            "section_id": section_id,
            "readability_score": readability,
            "compliance_coverage": compliance_coverage
        }
        
        self._write_metric(metric)
    
    def _write_metric(self, metric: dict):
        """Write metric to log"""
        Path("logs").mkdir(exist_ok=True)
        with open(self.metrics_file, "a") as f:
            f.write(json.dumps(metric) + "\n")
    
    def get_average_metrics(self, metric_type: str = "extraction") -> dict:
        """Calculate average metrics by type"""
        
        if not Path(self.metrics_file).exists():
            return {}
        
        metrics = defaultdict(list)
        
        with open(self.metrics_file) as f:
            for line in f:
                entry = json.loads(line)
                if entry["type"] == metric_type:
                    metrics["quality_scores"].append(entry.get("quality_score", entry.get("confidence")))
        
        if not metrics["quality_scores"]:
            return {"average": 0.0, "count": 0}
        
        return {
            "average": sum(metrics["quality_scores"]) / len(metrics["quality_scores"]),
            "count": len(metrics["quality_scores"]),
            "min": min(metrics["quality_scores"]),
            "max": max(metrics["quality_scores"])
        }
```

---

## TROUBLESHOOTING COMMON ISSUES

### Issue 1: Low Extraction Confidence

```python
def handle_low_extraction_confidence(document_id: str, extraction_result):
    """
    Handle cases where extraction confidence is below threshold (0.70)
    """
    
    if extraction_result.extraction_quality_score < 0.70:
        logger.warning(f"Low extraction confidence for {document_id}")
        
        # Action 1: Flag for manual review
        audit_log("EXTRACTION_LOW_CONFIDENCE", document_id, {
            "confidence": extraction_result.extraction_quality_score,
            "action": "FLAGGED_FOR_REVIEW"
        })
        
        # Action 2: Try alternative extraction method (Qwen Vision for complex layouts)
        alternative_result = try_qwen_extraction(document_id)
        
        # Action 3: Compare results
        if alternative_result.quality_score > extraction_result.extraction_quality_score:
            logger.info(f"✓ Qwen extraction higher quality. Using alternative.")
            return alternative_result
        
        # Otherwise, use original but flag
        return extraction_result
```

### Issue 2: Incomplete Reference Extraction

```python
def handle_incomplete_references(document_id: str, references_result):
    """
    Handle cases where reference extraction may have missed citations
    """
    
    if references_result.total_references_found < 5:  # Unusually low
        logger.warning(f"Possibly incomplete reference extraction for {document_id}")
        
        # Use regex fallback to find FAR/DFARS citations
        import re
        
        far_pattern = r"48\s*CFR\s+(\d+\.\d+(?:-\d+)?)"
        dfars_pattern = r"DFARS\s+(\d+\.\d+(?:-\d+)?)"
        
        # These would supplement Claude's extraction
        far_found = len(re.findall(far_pattern, document_text))
        dfars_found = len(re.findall(dfars_pattern, document_text))
        
        if far_found > len(references_result.far_citations):
            logger.warning(f"Regex found {far_found} FAR citations vs {len(references_result.far_citations)}")
            audit_log("REFERENCE_EXTRACTION_INCOMPLETE", document_id, {
                "claude_found": len(references_result.far_citations),
                "regex_found": far_found,
                "action": "FLAGGED_FOR_MANUAL_SUPPLEMENTATION"
            })
```

### Issue 3: Compliance Coverage Gap in Proposal

```python
def validate_proposal_compliance_coverage(proposal_section, rfp_requirement):
    """
    Validate that proposal section addresses all key RFP requirements
    """
    
    # Extract requirement keywords
    keywords = extract_keywords(rfp_requirement)
    proposal_text = proposal_section.body.lower()
    
    coverage = {}
    for keyword in keywords:
        covered = keyword.lower() in proposal_text
        coverage[keyword] = covered
    
    coverage_percent = sum(coverage.values()) / len(coverage) * 100
    
    if coverage_percent < 80:  # Flag if <80% coverage
        logger.warning(f"Low compliance coverage: {coverage_percent:.1f}%")
        
        missing_keywords = [k for k, v in coverage.items() if not v]
        
        audit_log("PROPOSAL_COVERAGE_GAP", proposal_section.section_title, {
            "coverage_percent": coverage_percent,
            "missing_keywords": missing_keywords,
            "recommendation": "Revise proposal to explicitly address all keywords"
        })
        
        return False  # Flag for revision
    
    return True  # Adequate coverage
```

---

**End of Implementation Guide**

For questions, refer to fedops-prompts.md for prompt details and schemas.
