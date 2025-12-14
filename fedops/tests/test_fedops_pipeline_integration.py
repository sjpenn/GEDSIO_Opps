import pytest
from unittest.mock import MagicMock, patch
import os
import json
from datetime import datetime

from fedops_core.pipelines.fedops_pipeline import FedOpsPipeline
from fedops_core.schemas.extraction import ExtractedDocument
from fedops_core.schemas.analysis import DocumentAnalysis, ComplianceRequirement
from fedops_core.schemas.writing import ProposalSection, ReferenceExtraction

@pytest.fixture
def mock_anthropic():
    with patch("fedops_core.pipelines.fedops_pipeline.Anthropic") as mock:
        yield mock

@pytest.fixture
def pipeline(mock_anthropic):
    return FedOpsPipeline(api_key="test-key")

def test_extract_document_structure(pipeline, mock_anthropic):
    """Test extraction phase"""
    # Mock response
    mock_message = MagicMock()
    mock_block = MagicMock()
    mock_block.type = "tool_use"
    mock_block.input = {
        "document_id": "TEST_DOC",
        "title": "Test Contract",
        "full_text": "Content",
        "sections": [{"heading": "1. Scope", "content": "Scope content", "page_number": 1}],
        "tables": [],
        "text_chunks": ["Content"],
        "metadata": {
            "source_file": "test.pdf",
            "extraction_tool": "docling",
            "total_pages": 1,
            "processing_time_seconds": 1.0
        }
    }
    mock_message.content = [mock_block]
    pipeline.client.messages.create.return_value = mock_message

    # Run
    result = pipeline.extract_document("Raw content", "TEST_DOC")

    # Verify
    assert isinstance(result, ExtractedDocument)
    assert result.document_id == "TEST_DOC"
    assert result.sections[0].heading == "1. Scope"
    pipeline.client.messages.create.assert_called_once()

def test_analyze_document(pipeline, mock_anthropic):
    """Test analysis phase"""
    # Mock input extracted doc
    extracted_doc = ExtractedDocument(
        document_id="TEST_DOC",
        full_text="Content",
        sections=[{"heading": "1. Scope", "content": "Scope content", "page_number": 1}],
        text_chunks=["Content"],
        metadata={
            "source_file": "test.pdf",
            "extraction_tool": "docling",
            "total_pages": 1,
            "processing_time_seconds": 1.0,
            "text_confidence": 0.99,
            "table_confidence": 0.99
        }
    )

    # Mock response
    mock_message = MagicMock()
    mock_block = MagicMock()
    mock_block.type = "tool_use"
    mock_block.input = {
        "document_id": "TEST_DOC",
        "analysis_timestamp": datetime.utcnow().isoformat(),
        "compliance_requirements": [
            {
                "requirement_id": "REQ_001",
                "requirement_text": "Must do X",
                "category": "Security",
                "severity": "HIGH",
                "applicable_to": ["Vendor"],
                "regulatory_framework": "NIST",
                "page_reference": 1,
                "confidence": 0.95
            }
        ],
        "regulatory_references": [],
        "risks": [],
        "executive_summary": "Summary",
        "key_findings": ["Finding"],
        "overall_complexity": "Simple",
        "compliance_readiness": 80,
        "implementation_effort": "Low"
    }
    mock_message.content = [mock_block]
    pipeline.client.messages.create.return_value = mock_message

    # Run
    result = pipeline.analyze_document(extracted_doc)

    # Verify
    assert isinstance(result, DocumentAnalysis)
    assert len(result.compliance_requirements) == 1
    assert result.compliance_requirements[0].requirement_id == "REQ_001"

def test_extract_references(pipeline, mock_anthropic):
    """Test reference extraction"""
    mock_message = MagicMock()
    mock_block = MagicMock()
    mock_block.type = "tool_use"
    mock_block.input = {
        "reference_type": "verbose",
        "total_references_found": 1,
        "far_citations": [],
        "dfars_citations": [],
        "iso_standards": [],
        "nist_standards": [],
        "industry_standards": [],
        "external_documents": [],
        "appendix_references": [],
        "critical_references": [],
        "optional_references": [],
        "regulatory_framework": "FAR",
        "compliance_complexity": "Low"
    }
    mock_message.content = [mock_block]
    pipeline.client.messages.create.return_value = mock_message

    result = pipeline.extract_all_references("Content", "TEST_DOC")
    
    assert isinstance(result, ReferenceExtraction)
    assert result.total_references_found == 1

def test_generate_proposal(pipeline, mock_anthropic):
    """Test proposal generation"""
    # Mock inputs
    analysis = MagicMock()
    analysis.contract_metadata = None
    analysis.compliance_requirements = []
    analysis.document_id = "TEST_DOC"

    mock_message = MagicMock()
    mock_block = MagicMock()
    mock_block.type = "tool_use"
    mock_block.input = {
        "section_title": "3.1 Approach",
        "body": "We proposal...",
        "readability_score": 0.9
    }
    mock_message.content = [mock_block]
    pipeline.client.messages.create.return_value = mock_message

    result = pipeline.generate_proposal_section(
        "Req text", "1.0", analysis, ["Past perf"]
    )

    assert isinstance(result, ProposalSection)
    assert result.section_title == "3.1 Approach"
