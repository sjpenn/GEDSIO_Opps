from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# BASIC TYPES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TableCell(BaseModel):
    """Single cell in extracted table"""
    content: str = Field(..., description="Cell content/text")
    row: int = Field(..., description="Row index (0-based)")
    col: int = Field(..., description="Column index (0-based)")
    is_header: bool = Field(False, description="Is this a header cell?")
    confidence: float = Field(0.95, ge=0.0, le=1.0, description="Extraction confidence (0-1)")

class ExtractedTable(BaseModel):
    """Structured table extracted from document"""
    title: Optional[str] = Field(None, description="Table title/caption")
    headers: List[str] = Field(..., description="Column headers")
    rows: List[List[str]] = Field(..., description="Table rows (2D array)")
    row_count: int = Field(..., description="Number of data rows")
    col_count: int = Field(..., description="Number of columns")
    context: Optional[str] = Field(None, description="Text before/after table explaining context")
    confidence: float = Field(0.95, ge=0.0, le=1.0, description="Overall table quality (0-1)")

class DocumentSection(BaseModel):
    """Logical section/heading in document"""
    heading: str = Field(..., description="Section heading/title")
    heading_level: int = Field(1, ge=1, le=6, description="Heading level (1=h1, 6=h6)")
    content: str = Field(..., description="Section body text")
    subsections: Optional[List['DocumentSection']] = Field(None, description="Nested subsections")
    page_number: int = Field(..., description="Starting page number")

DocumentSection.model_rebuild()

class ExtractionMetadata(BaseModel):
    """Metadata about extraction process"""
    source_file: str = Field(..., description="Original file name/path")
    extraction_tool: str = Field(..., description="Tool used (docling, pypdfium2, vision)")
    extraction_timestamp: datetime = Field(default_factory=datetime.utcnow)
    total_pages: int = Field(..., description="Total pages in document")
    text_confidence: float = Field(0.95, ge=0.0, le=1.0, description="Text extraction confidence")
    table_confidence: float = Field(0.95, ge=0.0, le=1.0, description="Table extraction confidence")
    processing_time_seconds: float = Field(..., description="Time spent extracting")
    fallback_used: bool = Field(False, description="Did we fallback to secondary tool?")

class ExtractedDocument(BaseModel):
    """Complete extracted document (output from EXTRACTION LAYER)"""
    document_id: str = Field(..., description="Unique document identifier")
    title: Optional[str] = Field(None, description="Document title")
    full_text: str = Field(..., description="Complete document text (markdown)")
    sections: List[DocumentSection] = Field(..., description="Structured sections with hierarchy")
    tables: List[ExtractedTable] = Field(default_factory=list, description="All extracted tables")
    text_chunks: List[str] = Field(..., description="Text split into 4000-token chunks for analysis")
    language: str = Field("en", description="Detected language")
    metadata: ExtractionMetadata = Field(..., description="Extraction metadata")
    extraction_quality_score: float = Field(0.85, ge=0.0, le=1.0, description="Overall quality (0-1)")
