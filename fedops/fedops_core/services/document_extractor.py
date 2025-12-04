"""
Document Extraction Service

Specialized extraction service for different government solicitation document types.
Uses detailed prompts from prompts.py to extract structured data from:
- Section L (Instructions to Offerors)
- Section M (Evaluation Criteria)
- Section H (Special Contract Requirements)
- SOW/PWS (Statement of Work)
- Section B (Pricing)
- Section I (Contract Clauses)
- Section K (Representations and Certifications)
"""

import re
import json
import logging
from typing import Dict, List, Optional, Any, Type
from pathlib import Path
from pydantic import BaseModel

from fedops_core.settings import settings
from fedops_core.services.ai_service import AIService
from fedops_core.services.docling_service import DoclingService
from fedops_core.schemas.extraction_schemas import (
    SectionLSchema,
    SectionMSchema,
    SectionHSchema,
    SOWSchema,
    SectionBSchema,
    SectionISchema,
    SectionKSchema,
    CDRLSchema,
)
from fedops_core.prompts import (
    DocumentType,
    determine_document_type,
    get_prompt_for_doc_type,
    SECTION_L_INSTRUCTIONS,
    SECTION_M_INSTRUCTIONS,
    SECTION_H_INSTRUCTIONS,
    SOW_INSTRUCTIONS,
    SECTION_B_INSTRUCTIONS,
    SECTION_I_INSTRUCTIONS,
    SECTION_K_INSTRUCTIONS,
    CDRL_INSTRUCTIONS
)

logger = logging.getLogger(__name__)


class DocumentExtractor:
    """Service for extracting structured data from government solicitation documents"""
    
    def __init__(self):
        self.ai_service = AIService()
        self.docling_service = DoclingService()
        self.schema_map = {
            DocumentType.SECTION_L: SectionLSchema,
            DocumentType.SECTION_M: SectionMSchema,
            DocumentType.SECTION_H: SectionHSchema,
            DocumentType.SOW: SOWSchema,
            DocumentType.SECTION_B: SectionBSchema,
            DocumentType.SECTION_I: SectionISchema,
            DocumentType.SECTION_K: SectionKSchema,
            DocumentType.CDRL: CDRLSchema,
        }
    
    async def extract_all_documents(
        self, 
        files: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Extract structured data from all documents in an opportunity.
        
        Args:
            files: List of dicts with 'file_path' and 'filename' keys
            
        Returns:
            Dictionary organized by document type:
            {
                "section_l": {...},
                "section_m": {...},
                "section_h": {...},
                "sow": {...},
                "section_b": {...},
                "section_i": {...},
                "section_k": {...},
                "cdrl": {...},
                "source_documents": [...]
            }
        """
        logger.info(f"Starting extraction from {len(files)} documents")
        
        extracted_data = {
            "section_l": None,
            "section_m": None,
            "section_h": None,
            "sow": None,
            "section_b": None,
            "section_i": None,
            "section_k": None,
            "cdrl": None,
            "source_documents": []
        }
        
        for file_info in files:
            file_path = file_info.get('file_path')
            filename = file_info.get('filename', Path(file_path).name)
            
            try:
                # Read file content
                content = await self._read_file(file_path)
                if not content:
                    logger.warning(f"No content extracted from {filename}")
                    continue
                
                # Determine document type
                doc_type = determine_document_type(filename, content[:1000])
                logger.info(f"Detected {filename} as {doc_type.value}")
                
                # Extract based on type (pass file_path for table extraction)
                extracted = await self._extract_by_type(doc_type, content, filename, file_path)
                
                if extracted:
                    # Store in appropriate section
                    section_key = self._get_section_key(doc_type)
                    if section_key:
                        extracted_data[section_key] = extracted
                        extracted_data["source_documents"].append({
                            "filename": filename,
                            "type": doc_type.value,
                            "section": section_key
                        })
                        logger.info(f"Successfully extracted {section_key} from {filename}")
                
            except Exception as e:
                logger.error(f"Error extracting from {filename}: {e}", exc_info=True)
                continue
        
        logger.info(f"Extraction complete. Extracted sections: {[k for k, v in extracted_data.items() if v and k != 'source_documents']}")
        return extracted_data
    
    async def _read_file(self, file_path: str, use_docling: bool = False) -> Optional[str]:
        """Read file content with multiple fallback methods"""
        try:
            # For PDFs, check if it's scanned and needs OCR
            if file_path.lower().endswith('.pdf'):
                # Check if PDF is scanned
                is_scanned = self.docling_service.is_scanned_pdf(file_path)
                
                if is_scanned or use_docling:
                    logger.info(f"Using Docling for PDF parsing: {file_path} (scanned: {is_scanned})")
                    content = await self.docling_service.parse_with_fallback(file_path)
                    if content:
                        return content
            
            # Try reading as text first
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                if content.strip():
                    return content
            
            # For PDFs, try PDF parsing
            if file_path.lower().endswith('.pdf'):
                return await self._parse_pdf(file_path)
                
        except Exception as e:
            logger.error(f"Error reading {file_path}: {e}")
        
        return None
    
    async def _parse_pdf(self, file_path: str) -> Optional[str]:
        """Parse PDF file"""
        try:
            from pypdf import PdfReader
            reader = PdfReader(file_path)
            text_parts = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)
            return "\n".join(text_parts)
        except ImportError:
            try:
                from PyPDF2 import PdfReader
                reader = PdfReader(file_path)
                text_parts = []
                for page in reader.pages:
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)
                return "\n".join(text_parts)
            except ImportError:
                logger.warning("Neither pypdf nor PyPDF2 available for PDF parsing")
        except Exception as e:
            logger.error(f"Error parsing PDF {file_path}: {e}")
        
        return None
    
    def _get_section_key(self, doc_type: DocumentType) -> Optional[str]:
        """Map DocumentType to section key"""
        mapping = {
            DocumentType.SECTION_L: "section_l",
            DocumentType.SECTION_M: "section_m",
            DocumentType.SECTION_H: "section_h",
            DocumentType.SOW: "sow",
            DocumentType.SECTION_B: "section_b",
            DocumentType.SECTION_I: "section_i",
            DocumentType.SECTION_K: "section_k",
            DocumentType.CDRL: "cdrl"
        }
        return mapping.get(doc_type)
    
    async def _extract_by_type(
        self, 
        doc_type: DocumentType, 
        content: str,
        filename: str,
        file_path: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Route to appropriate extraction method based on document type"""
        
        # Limit content size
        if len(content) > 100000:
            logger.info(f"Truncating {filename} from {len(content)} to 100000 characters")
            content = content[:100000]
        
        # Check if this is a table-heavy section and we have file path
        use_tables = (
            file_path and 
            self.docling_service.is_table_heavy_section(doc_type.value)
        )
        
        extraction_methods = {
            DocumentType.SECTION_L: self.extract_section_l,
            DocumentType.SECTION_M: lambda c: self.extract_section_m(c, file_path) if use_tables else self.extract_section_m(c),
            DocumentType.SECTION_H: self.extract_section_h,
            DocumentType.SOW: self.extract_sow,
            DocumentType.SECTION_B: lambda c: self.extract_section_b(c, file_path) if use_tables else self.extract_section_b(c),
            DocumentType.SECTION_I: self.extract_section_i,
            DocumentType.SECTION_K: self.extract_section_k,
            DocumentType.CDRL: lambda c: self.extract_cdrl(c, file_path) if use_tables else self.extract_cdrl(c)
        }
        
        method = extraction_methods.get(doc_type)
        if method:
            return await method(content)
        
        logger.debug(f"No extraction method for {doc_type.value}")
        return None
    
    async def extract_section_l(self, content: str) -> Dict[str, Any]:
        """Extract structured data from Section L (Instructions to Offerors)"""
        prompt = f"{SECTION_L_INSTRUCTIONS}\n\nDocument Content:\n{content}"
        return await self._ai_extract(prompt, "Section L", SectionLSchema)
    
    async def extract_section_m(self, content: str, file_path: Optional[str] = None) -> Dict[str, Any]:
        """Extract evaluation criteria from Section M"""
        
        # Try to extract tables if file path provided
        tables_markdown = ""
        if file_path:
            try:
                tables = await self.docling_service.extract_tables(file_path)
                if tables:
                    logger.info(f"Extracted {len(tables)} tables from Section M using Docling")
                    tables_markdown = "\n\n## Extracted Evaluation Tables:\n\n"
                    for idx, table in enumerate(tables):
                        tables_markdown += f"### Table {idx + 1}"
                        if table.caption:
                            tables_markdown += f": {table.caption}"
                        tables_markdown += f"\n{table.markdown}\n\n"
            except Exception as e:
                logger.warning(f"Could not extract tables from Section M: {e}")
        
        full_content = content if not tables_markdown else f"{content}\n\n{tables_markdown}"
        prompt = f"{SECTION_M_INSTRUCTIONS}\n\nDocument Content:\n{full_content}"
        return await self._ai_extract(prompt, "Section M", SectionMSchema)
    
    async def extract_section_h(self, content: str) -> Dict[str, Any]:
        """Extract key personnel, security, transition requirements from Section H"""
        prompt = f"{SECTION_H_INSTRUCTIONS}\n\nDocument Content:\n{content}"
        return await self._ai_extract(prompt, "Section H", SectionHSchema)
    
    async def extract_sow(self, content: str) -> Dict[str, Any]:
        """Extract tasks, deliverables, performance requirements from SOW"""
        prompt = f"{SOW_INSTRUCTIONS}\n\nDocument Content:\n{content}"
        return await self._ai_extract(prompt, "SOW", SOWSchema)
    
    async def extract_section_b(self, content: str, file_path: Optional[str] = None) -> Dict[str, Any]:
        """Extract pricing structure, CLINs, contract value from Section B"""
        
        # If we have a file path, try to extract tables with Docling
        tables_markdown = ""
        if file_path:
            try:
                tables = await self.docling_service.extract_tables(file_path)
                if tables:
                    logger.info(f"Extracted {len(tables)} tables from Section B using Docling")
                    tables_markdown = "\n\n## Extracted Tables (Structured):\n\n"
                    for idx, table in enumerate(tables):
                        tables_markdown += f"### Table {idx + 1}"
                        if table.caption:
                            tables_markdown += f": {table.caption}"
                        tables_markdown += f"\n{table.markdown}\n\n"
            except Exception as e:
                logger.warning(f"Could not extract tables from Section B: {e}")
        
        # Combine content with extracted tables
        full_content = content
        if tables_markdown:
            full_content = f"{content}\n\n{tables_markdown}"
        
        prompt = f"{SECTION_B_INSTRUCTIONS}\n\nDocument Content:\n{full_content}"
        return await self._ai_extract(prompt, "Section B", SectionBSchema)
    
    async def extract_section_i(self, content: str) -> Dict[str, Any]:
        """Extract contract clauses and compliance requirements from Section I"""
        prompt = f"{SECTION_I_INSTRUCTIONS}\n\nDocument Content:\n{content}"
        return await self._ai_extract(prompt, "Section I", SectionISchema)
    
    async def extract_section_k(self, content: str) -> Dict[str, Any]:
        """Extract representations and certifications from Section K"""
        prompt = f"{SECTION_K_INSTRUCTIONS}\n\nDocument Content:\n{content}"
        return await self._ai_extract(prompt, "Section K", SectionKSchema)
    
    async def extract_cdrl(self, content: str, file_path: Optional[str] = None) -> Dict[str, Any]:
        """Extract Contract Data Requirements List"""
        
        # Try to extract DD Form 1423 tables
        tables_markdown = ""
        if file_path:
            try:
                tables = await self.docling_service.extract_tables(file_path)
                if tables:
                    logger.info(f"Extracted {len(tables)} CDRL tables using Docling")
                    tables_markdown = "\n\n## Extracted CDRL Tables (DD Form 1423):\n\n"
                    for idx, table in enumerate(tables):
                        tables_markdown += f"### Table {idx + 1}"
                        if table.caption:
                            tables_markdown += f": {table.caption}"
                        tables_markdown += f"\n{table.markdown}\n\n"
            except Exception as e:
                logger.warning(f"Could not extract tables from CDRL: {e}")
        
        full_content = content if not tables_markdown else f"{content}\n\n{tables_markdown}"
        prompt = f"{CDRL_INSTRUCTIONS}\n\nDocument Content:\n{full_content}"
        return await self._ai_extract(prompt, "CDRL", CDRLSchema)
    
    async def _ai_extract(
        self,
        prompt: str,
        section_name: str,
        schema: Optional[Type[BaseModel]] = None
    ) -> Optional[Dict[str, Any]]:
        """Use AI to extract structured data using section-specific prompts"""
        try:
            logger.info(f"Extracting {section_name} using AI")
            
            # If schema provided, use schema-based extraction
            if schema:
                validated_result = await self.ai_service.analyze_with_schema(
                    prompt,
                    schema,
                    use_structured_output=True
                )
                
                if validated_result:
                    # Convert Pydantic model to dict
                    result_dict = validated_result.model_dump()
                    logger.info(f"Successfully extracted and validated {section_name}")
                    return result_dict
                else:
                    logger.warning(f"Schema validation failed for {section_name}, falling back to unvalidated extraction")
            
            # Fallback to standard extraction
            result = await self.ai_service.analyze_opportunity(prompt)
            
            # Check if we got a valid result
            if result and isinstance(result, dict):
                # Check if it's an error response from AIService
                if result.get('status') == 'error':
                    logger.error(f"AI service returned error for {section_name}: {result.get('error')}")
                    return None
                
                logger.info(f"Successfully extracted {section_name} with {len(result)} fields")
                return result
            else:
                logger.warning(f"AI service returned invalid response for {section_name}")
                return None
                
        except Exception as e:
            logger.error(f"Error extracting {section_name}: {e}", exc_info=True)
            return None
