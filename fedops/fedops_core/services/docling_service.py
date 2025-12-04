"""
Docling Service - AI-powered document parsing and table extraction.

This service wraps IBM's Docling library for advanced PDF parsing,
table extraction, and OCR support. It provides a fallback to basic
pypdf parsing if Docling fails.
"""

import logging
from typing import Optional, List, Dict, Any
from pathlib import Path
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class TableData:
    """Extracted table data"""
    caption: Optional[str]
    headers: List[str]
    rows: List[List[str]]
    markdown: str
    page_number: Optional[int] = None


@dataclass
class DoclingResult:
    """Result from Docling document parsing"""
    success: bool
    markdown: Optional[str] = None
    tables: List[TableData] = None
    metadata: Dict[str, Any] = None
    error: Optional[str] = None
    
    def __post_init__(self):
        if self.tables is None:
            self.tables = []
        if self.metadata is None:
            self.metadata = {}


class DoclingService:
    """Service for advanced document parsing using Docling"""
    
    def __init__(self, cache_service=None, metrics_service=None):
        self.docling_available = self._check_docling_availability()
        self.cache_service = cache_service
        self.metrics_service = metrics_service
        
        if self.docling_available:
            logger.info("Docling library available - advanced parsing enabled")
        else:
            logger.warning("Docling library not available - using fallback parsing")
        
        if cache_service:
            logger.info("Cache service enabled for Docling")
        if metrics_service:
            logger.info("Metrics service enabled for Docling")
    
    def _check_docling_availability(self) -> bool:
        """Check if Docling is installed and available"""
        try:
            import docling
            return True
        except ImportError:
            return False
    
    def is_scanned_pdf(self, file_path: str) -> bool:
        """
        Detect if a PDF is scanned (image-based) and needs OCR.
        Uses cache if available to avoid redundant checks.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            True if PDF appears to be scanned, False otherwise
        """
        # Check cache first
        if self.cache_service:
            import asyncio
            cached_status = asyncio.run(self.cache_service.get_scanned_status(file_path))
            if cached_status is not None:
                if self.metrics_service:
                    self.metrics_service.record_cache_hit("scanned_status")
                logger.debug(f"Cache HIT for scanned status: {Path(file_path).name}")
                return cached_status
            if self.metrics_service:
                self.metrics_service.record_cache_miss("scanned_status")
        
        try:
            from pypdf import PdfReader
            
            reader = PdfReader(file_path)
            
            # Sample first few pages
            pages_to_check = min(3, len(reader.pages))
            total_text_length = 0
            
            for i in range(pages_to_check):
                text = reader.pages[i].extract_text()
                total_text_length += len(text.strip())
            
            # If very little text extracted, likely scanned
            avg_text_per_page = total_text_length / pages_to_check
            
            # Threshold: less than 100 characters per page suggests scanned
            is_scanned = avg_text_per_page < 100
            
            if is_scanned:
                logger.info(f"PDF appears to be scanned (avg {avg_text_per_page:.0f} chars/page)")
            
            # Cache the result
            if self.cache_service:
                import asyncio
                asyncio.run(self.cache_service.set_scanned_status(file_path, is_scanned))
            
            return is_scanned
            
        except Exception as e:
            logger.warning(f"Could not determine if PDF is scanned: {e}")
            return False  # Assume not scanned if we can't tell
    
    async def parse_document(
        self,
        file_path: str,
        extract_tables: bool = True,
        use_ocr: bool = False
    ) -> DoclingResult:
        """
        Parse a document using Docling.
        
        Args:
            file_path: Path to the document file
            extract_tables: Whether to extract tables
            use_ocr: Whether to use OCR for scanned documents
            
        Returns:
            DoclingResult with parsed content
        """
        if not self.docling_available:
            return DoclingResult(
                success=False,
                error="Docling library not available"
            )
        
        try:
            from docling.document_converter import DocumentConverter
            from docling.datamodel.base_models import InputFormat
            from docling.datamodel.pipeline_options import PdfPipelineOptions
            
            logger.info(f"Parsing document with Docling: {file_path}")
            
            # Configure pipeline options
            pipeline_options = PdfPipelineOptions()
            
            # Enable OCR if requested
            if use_ocr:
                logger.info("OCR enabled for document parsing")
                pipeline_options.do_ocr = True
                pipeline_options.ocr_options.force_full_page_ocr = True
            
            # Initialize converter with options
            converter = DocumentConverter(
                format_options={
                    InputFormat.PDF: pipeline_options
                }
            )
            
            # Convert document
            result = converter.convert(file_path)
            
            # Extract markdown
            markdown = result.document.export_to_markdown()
            
            # Extract tables if requested
            tables = []
            if extract_tables:
                tables = await self._extract_tables_from_result(result)
            
            # Get metadata
            metadata = {
                "num_pages": getattr(result.document, "num_pages", None),
                "title": getattr(result.document, "title", None),
                "ocr_used": use_ocr
            }
            
            logger.info(f"Successfully parsed document with {len(tables)} tables")
            
            return DoclingResult(
                success=True,
                markdown=markdown,
                tables=tables,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Error parsing document with Docling: {e}", exc_info=True)
            
            # If OCR was requested and failed, try without OCR
            if use_ocr:
                logger.info("OCR parsing failed, retrying without OCR")
                return await self.parse_document(file_path, extract_tables, use_ocr=False)
            
            return DoclingResult(
                success=False,
                error=str(e)
            )
    
    async def _extract_tables_from_result(self, result) -> List[TableData]:
        """Extract tables from Docling result"""
        tables = []
        
        try:
            # Access tables from the document
            doc_dict = result.document.export_to_dict()
            
            # Extract table data
            if "tables" in doc_dict:
                for idx, table in enumerate(doc_dict["tables"]):
                    table_data = self._parse_table_structure(table, idx)
                    if table_data:
                        tables.append(table_data)
            
        except Exception as e:
            logger.error(f"Error extracting tables: {e}", exc_info=True)
        
        return tables
    
    def _parse_table_structure(self, table: Dict[str, Any], index: int) -> Optional[TableData]:
        """Parse table structure into TableData"""
        try:
            # Extract table data based on Docling's structure
            # This may need adjustment based on actual Docling output format
            
            caption = table.get("caption")
            data = table.get("data", [])
            
            if not data:
                return None
            
            # First row is typically headers
            headers = data[0] if data else []
            rows = data[1:] if len(data) > 1 else []
            
            # Generate markdown representation
            markdown = self._table_to_markdown(headers, rows, caption)
            
            return TableData(
                caption=caption,
                headers=headers,
                rows=rows,
                markdown=markdown,
                page_number=table.get("page")
            )
            
        except Exception as e:
            logger.error(f"Error parsing table {index}: {e}")
            return None
    
    def _table_to_markdown(
        self,
        headers: List[str],
        rows: List[List[str]],
        caption: Optional[str] = None
    ) -> str:
        """Convert table to markdown format"""
        lines = []
        
        if caption:
            lines.append(f"**{caption}**\n")
        
        # Header row
        if headers:
            lines.append("| " + " | ".join(str(h) for h in headers) + " |")
            lines.append("|" + "|".join(["---" for _ in headers]) + "|")
        
        # Data rows
        for row in rows:
            lines.append("| " + " | ".join(str(cell) for cell in row) + " |")
        
        return "\n".join(lines)
    
    async def extract_tables(self, file_path: str) -> List[TableData]:
        """
        Extract only tables from a document.
        
        Args:
            file_path: Path to the document
            
        Returns:
            List of extracted tables
        """
        result = await self.parse_document(file_path, extract_tables=True)
        return result.tables if result.success else []
    
    async def get_structured_markdown(self, file_path: str) -> Optional[str]:
        """
        Get structured markdown from a document.
        
        Args:
            file_path: Path to the document
            
        Returns:
            Markdown string or None if parsing failed
        """
        result = await self.parse_document(file_path, extract_tables=False)
        return result.markdown if result.success else None
    
    async def parse_with_fallback(self, file_path: str) -> str:
        """
        Parse document with Docling, falling back to pypdf if needed.
        Automatically detects scanned PDFs and enables OCR.
        
        Args:
            file_path: Path to the document
            
        Returns:
            Extracted text content
        """
        # Check if PDF is scanned and needs OCR
        use_ocr = False
        if file_path.lower().endswith('.pdf'):
            use_ocr = self.is_scanned_pdf(file_path)
        
        # Try Docling first (with OCR if needed)
        result = await self.parse_document(file_path, use_ocr=use_ocr)
        
        if result.success and result.markdown:
            logger.info(f"Successfully parsed with Docling (OCR: {use_ocr})")
            return result.markdown
        
        # Fallback to pypdf
        logger.info("Falling back to pypdf parsing")
        return await self._fallback_parse_pdf(file_path)
    
    async def _fallback_parse_pdf(self, file_path: str) -> Optional[str]:
        """Fallback PDF parsing using pypdf"""
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
                logger.error("Neither pypdf nor PyPDF2 available")
                return None
        except Exception as e:
            logger.error(f"Error in fallback PDF parsing: {e}")
            return None
    
    def is_table_heavy_section(self, doc_type: str) -> bool:
        """
        Determine if a document type typically contains many tables.
        
        Args:
            doc_type: Document type (e.g., 'section_b', 'cdrl')
            
        Returns:
            True if document type is table-heavy
        """
        table_heavy_types = {
            "section_b",  # Pricing tables
            "cdrl",       # DD Form 1423
            "section_m",  # Evaluation matrices
        }
        return doc_type.lower() in table_heavy_types
