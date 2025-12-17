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
from fedops_core.services.section_shredder import SectionShredder
from fedops_core.services.extraction_progress import extraction_progress

logger = logging.getLogger(__name__)


class DocumentExtractor:
    """Service for extracting structured data from government solicitation documents"""
    
    def __init__(self):
        self.ai_service = AIService()
        self.docling_service = DoclingService()
        self.section_shredder = SectionShredder()
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
        # Mapping from section letter to DocumentType
        self.section_letter_to_type = {
            'L': DocumentType.SECTION_L,
            'M': DocumentType.SECTION_M,
            'H': DocumentType.SECTION_H,
            'C': DocumentType.SOW,
            'B': DocumentType.SECTION_B,
            'I': DocumentType.SECTION_I,
            'K': DocumentType.SECTION_K,
        }

    async def extract_all_documents(
        self, 
        files: List[Dict[str, str]],
        opportunity_id: Optional[int] = None,
        quick_scan: bool = False
    ) -> Dict[str, Any]:
        """
        Extract structured data from all documents in an opportunity.
        
        Args:
            files: List of dicts with 'file_path' and 'filename' keys
            opportunity_id: Optional ID for progress tracking
            
        Returns:
            Dictionary organized by document type
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
        
        total_files = len(files)
        
        for idx, file_info in enumerate(files):
            file_path = file_info.get('file_path')
            file_id = file_info.get('id')
            filename = file_info.get('filename', Path(file_path).name)
            
            # Update progress
            if opportunity_id:
                # Map 0-100% of file processing to 10-60% of overall workflow
                files_percent = int((idx / total_files) * 50) + 10
                extraction_progress.update(
                    opportunity_id, 
                    filename=filename, 
                    message=f"Step 2/5: Analyzing {filename} ({idx+1}/{total_files})...", 
                    percent=files_percent
                )
            
            try:
                # Read file content
                content = await self._read_file(file_path)
                if not content:
                    logger.warning(f"No content extracted from {filename}")
                    continue
                
                # Determine document type (pass more content for better detection)
                doc_type = determine_document_type(filename, content[:5000])
                logger.info(f"Detected {filename} as {doc_type.value}")
                
                # QUICK SCAN FILTER
                if quick_scan and doc_type not in [DocumentType.SOW, DocumentType.SECTION_M]:
                    logger.info(f"Quick Scan: Skipping {doc_type.value} ({filename})")
                    continue
                
                # Handle combined RFPs by shredding into sections
                if doc_type in [DocumentType.RFP_COMBINED, DocumentType.RFP]:
                    await self._process_combined_rfp(
                        content, filename, file_path, extracted_data, file_id
                    )
                    continue
                
                # Handle amendments - extract new/modified data
                if doc_type == DocumentType.AMENDMENT:
                    await self._process_amendment(
                        content, filename, file_path, extracted_data, file_id
                    )
                    continue
                
                # Extract based on type (pass file_path for table extraction)
                extracted = await self._extract_by_type(doc_type, content, filename, file_path)
                
                if extracted:
                    # Store in appropriate section
                    section_key = self._get_section_key(doc_type)
                    if section_key:
                        extracted_data[section_key] = extracted
                        extracted_data["source_documents"].append({
                            "id": file_id,
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
    
    async def _process_combined_rfp(
        self,
        content: str,
        filename: str,
        file_path: str,
        extracted_data: Dict[str, Any],
        file_id: Optional[int] = None
    ) -> None:
        """
        Process a combined RFP document by shredding it into sections.
        
        Uses SectionShredder to detect section boundaries and extract
        each section with appropriate prompts.
        """
        logger.info(f"Processing combined RFP: {filename}")
        
        # Shred into sections
        shredded = self.section_shredder.shred_to_extractions(content)
        logger.info(f"Shredded {filename} into {len(shredded)} sections: {list(shredded.keys())}")
        
        # Extract each section with appropriate method
        for section_letter, section_info in shredded.items():
            section_content = section_info.get('content', '')
            
            # Skip if section is too short
            if len(section_content) < 100:
                logger.debug(f"Skipping Section {section_letter} - too short ({len(section_content)} chars)")
                continue
            
            # Get the DocumentType for this section
            doc_type = self.section_letter_to_type.get(section_letter)
            if not doc_type:
                logger.debug(f"No extraction method for Section {section_letter}")
                continue
            
            # Extract using appropriate method
            try:
                extracted = await self._extract_by_type(
                    doc_type, section_content, f"{filename}#Section{section_letter}", file_path
                )
                
                if extracted:
                    section_key = self._get_section_key(doc_type)
                    if section_key:
                        # Don't overwrite if already extracted from dedicated file
                        if extracted_data.get(section_key) is None:
                            extracted_data[section_key] = extracted
                            extracted_data["source_documents"].append({
                                "id": file_id,
                                "filename": filename,
                                "type": f"combined_rfp_section_{section_letter.lower()}",
                                "section": section_key,
                                "confidence": section_info.get('confidence', 'medium')
                            })
                            logger.info(f"Extracted Section {section_letter} from combined RFP")
                        else:
                            logger.info(f"Section {section_letter} already extracted, skipping")
                            
            except Exception as e:
                logger.error(f"Error extracting Section {section_letter} from {filename}: {e}")
    
    async def _process_amendment(
        self,
        content: str,
        filename: str,
        file_path: str,
        extracted_data: Dict[str, Any],
        file_id: Optional[int] = None
    ) -> None:
        """
        Process an amendment document.
        
        Amendments may contain updates to any section - try to detect and merge.
        """
        logger.info(f"Processing amendment: {filename}")
        
        # Try to shred the amendment to find which sections are modified
        shredded = self.section_shredder.shred_to_extractions(content)
        
        if shredded:
            # Process as combined RFP but with amendment precedence
            for section_letter, section_info in shredded.items():
                section_content = section_info.get('content', '')
                
                if len(section_content) < 50:
                    continue
                    
                doc_type = self.section_letter_to_type.get(section_letter)
                if not doc_type:
                    continue
                
                try:
                    extracted = await self._extract_by_type(
                        doc_type, section_content, f"{filename}#Section{section_letter}", file_path
                    )
                    
                    if extracted:
                        section_key = self._get_section_key(doc_type)
                        if section_key:
                            # Amendments OVERRIDE existing data
                            extracted_data[section_key] = extracted
                            extracted_data["source_documents"].append({
                                "id": file_id,
                                "filename": filename,
                                "type": f"amendment_section_{section_letter.lower()}",
                                "section": section_key,
                                "is_amendment": True
                            })
                            logger.info(f"Amendment updated Section {section_letter}")
                            
                except Exception as e:
                    logger.error(f"Error processing amendment Section {section_letter}: {e}")
        else:
            logger.info(f"No specific sections detected in amendment {filename}")

    
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
        # Truncate content to fit in context window
        max_chars = 40000
        if len(content) > max_chars:
            logger.warning(f"Truncating content from {len(content)} to {max_chars} chars")
            content = content[:max_chars]
        
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
    
    # ========== NEW: Batch Ingestion Methods (Phase 1) ==========
    
    async def ingest_all_documents(
        self,
        files: List[Dict[str, Any]],
        opportunity_id: int,
        db_session=None,
        fast_mode: bool = False,
        turbo_mode: bool = False
    ) -> Dict[str, Any]:
        """
        Phase 1: Batch ingest all documents using Docling chunker.
        
        Uses parallel processing (asyncio.gather) to speed up ingestion.
        
        Args:
            files: List of dicts with 'file_path', 'filename', 'id' keys
            opportunity_id: The opportunity ID
            db_session: Optional database session for chunk storage
            fast_mode: If True, uses fast parsing options (skips TSR/OCR)
            turbo_mode: If True, skips vector storage entirely for fastest processing
            
        Returns:
            Summary of ingestion results
        """
        from fedops_core.services.docling_chunker import DoclingChunker
        from fedops_core.services.vector_store import VectorStore
        import asyncio
        
        logger.info(f"Starting batch ingestion of {len(files)} documents for opportunity {opportunity_id} (Fast Mode: {fast_mode}, Turbo Mode: {turbo_mode})")
        
        # Initialize services - skip vector store in turbo mode
        vector_store = None if turbo_mode else VectorStore()
        chunker = DoclingChunker(vector_store=vector_store, db_session=db_session)
        
        results = {
            "opportunity_id": opportunity_id,
            "total_files": len(files),
            "successful": 0,
            "failed": 0,
            "total_chunks": 0,
            "file_results": [],
            "docling_outputs": []
        }
        
        # Concurrency limit (3 concurrent Docling processes is safe for memory)
        semaphore = asyncio.Semaphore(3)
        
        async def process_file(file_info):
            async with semaphore:
                file_path = file_info.get('file_path')
                file_id = file_info.get('id', 0)
                filename = file_info.get('filename', '')
                
                try:
                    logger.info(f"Processing {filename}...")
                    # Pass extra args via **kwargs if supported by chunker, 
                    # but DoclingChunker needs update to accept fast_mode.
                    # For now, we assume DoclingChunker will be updated or we rely on defaults.
                    
                    ingest_result = await chunker.ingest_document(
                        file_path=file_path,
                        opportunity_id=opportunity_id,
                        stored_file_id=file_id,
                        store_vectors=not turbo_mode,
                        fast_mode=fast_mode
                    )
                    
                    return {
                        "file_info": file_info,
                        "result": ingest_result,
                        "success": ingest_result.success,
                        "error": None
                    }
                except Exception as e:
                    logger.error(f"Error ingesting {filename}: {e}")
                    return {
                        "file_info": file_info,
                        "result": None,
                        "success": False,
                        "error": str(e)
                    }

        # Run all tasks in parallel
        tasks = [process_file(f) for f in files]
        file_results_list = await asyncio.gather(*tasks)
        
        # Aggregate results
        for item in file_results_list:
            file_info = item["file_info"]
            ingest_result = item["result"]
            
            if item["success"] and ingest_result:
                results["successful"] += 1
                results["total_chunks"] += ingest_result.num_chunks
                
                if ingest_result.docling_json:
                    results["docling_outputs"].append({
                        "file_id": file_info.get('id'),
                        "filename": file_info.get('filename'),
                        "docling_json": ingest_result.docling_json
                    })
                    
                results["file_results"].append({
                    "file_id": file_info.get('id'),
                    "filename": file_info.get('filename'),
                    "success": True,
                    "num_chunks": ingest_result.num_chunks,
                    "num_pages": ingest_result.num_pages,
                    "num_tables": ingest_result.num_tables,
                    "error": None
                })
            else:
                results["failed"] += 1
                results["file_results"].append({
                    "file_id": file_info.get('id'),
                    "filename": file_info.get('filename'),
                    "success": False,
                    "error": item["error"] or ingest_result.error if ingest_result else "Unknown error"
                })
        
        logger.info(f"Ingestion complete: {results['successful']}/{results['total_files']} files, {results['total_chunks']} chunks")
        return results
    
    async def analyze_with_retrieval(
        self,
        opportunity_id: int,
        section_type: str,
        custom_query: Optional[str] = None,
        top_k: int = 15
    ) -> Optional[Dict[str, Any]]:
        """
        Phase 2: Analyze a section using vector retrieval.
        
        Retrieves relevant chunks via semantic search, then runs AI extraction.
        
        Args:
            opportunity_id: The opportunity ID
            section_type: Section to analyze (L, M, H, C, B, I, K)
            custom_query: Optional custom search query
            top_k: Number of chunks to retrieve
            
        Returns:
            Extracted structured data for the section
        """
        from fedops_core.services.docling_chunker import DoclingChunker
        from fedops_core.services.vector_store import VectorStore
        
        logger.info(f"Analyzing section {section_type} for opportunity {opportunity_id} using vector retrieval")
        
        vector_store = VectorStore()
        chunker = DoclingChunker(vector_store=vector_store)
        
        # Retrieve relevant chunks
        if custom_query:
            chunks = await chunker.semantic_search(custom_query, opportunity_id, top_k)
        else:
            chunks = await chunker.get_chunks_for_section(opportunity_id, section_type, top_k)
        
        if not chunks:
            logger.warning(f"No chunks found for section {section_type}")
            return None
        
        # Combine chunk content with source citations
        combined_content = []
        for chunk in chunks:
            source_info = f"[Page {chunk.page_number}]" if chunk.page_number else ""
            combined_content.append(f"{source_info}\n{chunk.content}")
        
        content = "\n\n---\n\n".join(combined_content)
        
        # Get the document type for this section
        doc_type = self.section_letter_to_type.get(section_type.upper())
        if not doc_type:
            logger.warning(f"Unknown section type: {section_type}")
            return None
        
        # Extract using existing methods
        extracted = await self._extract_by_type(doc_type, content, f"Section {section_type}", None)
        
        if extracted:
            # Add source tracking
            extracted["_source_chunks"] = [
                {
                    "chunk_id": chunk.id,
                    "page_number": chunk.page_number,
                    "section": chunk.section,
                    "score": chunk.metadata.get('score', None)
                }
                for chunk in chunks
            ]
        
        return extracted
    
    async def get_docling_json(self, opportunity_id: int, file_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve stored Docling JSON output for a file.
        
        Args:
            opportunity_id: The opportunity ID
            file_id: The stored file ID
            
        Returns:
            The Docling JSON dictionary or None
        """
        try:
            from fedops_core.db.models import DoclingDocument
            from sqlalchemy import select
            
            # This would need a DB session - placeholder for now
            logger.info(f"Retrieving Docling JSON for file {file_id}")
            return None  # Implement with actual DB query
            
        except Exception as e:
            logger.error(f"Error retrieving Docling JSON: {e}")
            return None
