import os
import json
from typing import Optional, List, Dict, Any
from pathlib import Path
from datetime import datetime

from anthropic import Anthropic
from docling.document_converter import DocumentConverter

from fedops_core.schemas.extraction import ExtractedDocument
from fedops_core.schemas.analysis import DocumentAnalysis
from fedops_core.schemas.writing import ProposalSection, ReferenceExtraction
from fedops_core.schemas.vision import OCRExtraction

from fedops_core.prompts import (
    EXTRACTION_SYSTEM_PROMPT,
    ANALYSIS_SYSTEM_PROMPT,
    WRITING_SYSTEM_PROMPT,
    VISION_SYSTEM_PROMPT,
    CONTRACT_ANALYSIS_USER_PROMPT,
    PROPOSAL_RESPONSE_USER_PROMPT,
    VERBOSE_REFERENCE_EXTRACTION_USER_PROMPT
)
from fedops_core.audit_logger import setup_logging, audit_log

logger = setup_logging()

class FedOpsPipeline:
    """
    Orchestrates the federal document processing workflow:
    Extraction -> Analysis -> Proposal Generation
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY must be set")
            
        self.client = Anthropic(api_key=self.api_key)
        self.converter = DocumentConverter()
        
        # Configuration
        self.model = "claude-3-5-sonnet-20241022"
        self.headers = {"anthropic-beta": "structured-outputs-2024-12-09"} # Updated header for beta

    def extract_document(self, document_text: str, document_id: str, extraction_tool: str = "docling") -> ExtractedDocument:
        """
        Phase 2: Structure extracted text into ExtractedDocument schema
        """
        logger.info(f"Structuring document {document_id}")
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=8192,
            system=EXTRACTION_SYSTEM_PROMPT,
            messages=[{
                "role": "user",
                "content": f"Extract this document content into the structured schema:\n\n{document_text[:100000]}" # Truncate if too large for single pass, ideally chunking
            }],
            tools=[{
                "name": "extract_document",
                "description": "Extract structured document data",
                "input_schema": ExtractedDocument.model_json_schema()
            }],
            tool_choice={"type": "tool", "name": "extract_document"}
        )
        
        # In actual Structured Outputs, we'd parse tool usage. 
        # For now assuming tool use response pattern.
        tool_use = next(block for block in response.content if block.type == "tool_use")
        extraction_data = tool_use.input
        
        # Create object
        extraction = ExtractedDocument(**extraction_data)
        
        audit_log("EXTRACTION_STRUCTURED", document_id, {
            "quality_score": extraction.extraction_quality_score,
            "sections_found": len(extraction.sections)
        })
        
        return extraction

    def analyze_document(self, extracted_doc: ExtractedDocument) -> DocumentAnalysis:
        """
        Phase 3: Analyze compliance and risks
        """
        logger.info(f"Analyzing document {extracted_doc.document_id}")
        
        # Serialize extraction for context
        # We might need to summarize if it's too large, but passing full structure is best
        doc_context = extracted_doc.model_dump_json()
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=8192,
            system=ANALYSIS_SYSTEM_PROMPT,
            messages=[{
                "role": "user",
                "content": f"{CONTRACT_ANALYSIS_USER_PROMPT}\n\nDOCUMENT:\n{doc_context[:150000]}"
            }],
            tools=[{
                "name": "analyze_document",
                "description": "Analyze document for compliance",
                "input_schema": DocumentAnalysis.model_json_schema()
            }],
            tool_choice={"type": "tool", "name": "analyze_document"}
        )
        
        tool_use = next(block for block in response.content if block.type == "tool_use")
        analysis_data = tool_use.input
        
        analysis = DocumentAnalysis(**analysis_data)
        
        audit_log("ANALYSIS_COMPLETE", extracted_doc.document_id, {
            "requirements_count": len(analysis.compliance_requirements),
            "risks_count": len(analysis.risks)
        })
        
        return analysis

    def extract_all_references(self, document_text: str, document_id: str) -> ReferenceExtraction:
        """
        Phase 4: Verbose reference extraction
        """
        logger.info(f"Extracting references for {document_id}")
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=8192,
            system=ANALYSIS_SYSTEM_PROMPT, # Uses analysis expertise
            messages=[{
                "role": "user",
                "content": f"{VERBOSE_REFERENCE_EXTRACTION_USER_PROMPT}\n\nDOCUMENT:\n{document_text[:100000]}"
            }],
             tools=[{
                "name": "extract_references",
                "description": "Extract all regulatory references",
                "input_schema": ReferenceExtraction.model_json_schema()
            }],
            tool_choice={"type": "tool", "name": "extract_references"}
        )
        
        tool_use = next(block for block in response.content if block.type == "tool_use")
        ref_data = tool_use.input
        
        references = ReferenceExtraction(**ref_data)
        
        audit_log("REFERENCES_EXTRACTED", document_id, {
            "total_found": references.total_references_found
        })
        
        return references

    def generate_proposal_section(
        self, 
        rfp_requirement: str, 
        requirement_number: str,
        analysis: DocumentAnalysis,
        past_performance: List[str]
    ) -> ProposalSection:
        """
        Generate a proposal response section
        """
        logger.info(f"Generating proposal section {requirement_number}")
        
        # Prepare context variables
        contract_info = analysis.contract_metadata.model_dump_json() if analysis.contract_metadata else "N/A"
        compliance_reqs = json.dumps([req.model_dump() for req in analysis.compliance_requirements][:20]) # Limit context
        pp_context = "\n".join(past_performance)
        tech_capabilities = "GEDSIO specializes in AI-driven document processing, federal compliance automation, and secure cloud infrastructure."
        
        formatted_prompt = PROPOSAL_RESPONSE_USER_PROMPT.format(
            requirement_text=rfp_requirement,
            contract_info=contract_info,
            compliance_requirements=compliance_reqs,
            past_performance=pp_context,
            technical_capabilities=tech_capabilities,
            requirement_number=requirement_number
        )
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=WRITING_SYSTEM_PROMPT,
            messages=[{
                "role": "user",
                "content": formatted_prompt
            }],
            tools=[{
                "name": "write_proposal",
                "description": "Write a proposal section",
                "input_schema": ProposalSection.model_json_schema()
            }],
            tool_choice={"type": "tool", "name": "write_proposal"}
        )
        
        tool_use = next(block for block in response.content if block.type == "tool_use")
        prop_data = tool_use.input
        
        proposal = ProposalSection(**prop_data)
        
        audit_log("PROPOSAL_SECTION_GENERATED", analysis.document_id, {
            "section": requirement_number,
            "readability": proposal.readability_score
        })
        
        return proposal
