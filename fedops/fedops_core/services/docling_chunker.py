"""
Docling Chunker Service - Intelligent document chunking using Docling's HierarchicalChunker.

This service provides:
- Full document ingestion with structural parsing
- Hierarchical chunking that preserves document structure
- Source location tracking (page, section, position)
- Integration with vector store for semantic search
"""

import logging
import asyncio
from typing import List, Optional, Dict, Any, Iterator
from dataclasses import dataclass
from pathlib import Path
from functools import partial

logger = logging.getLogger(__name__)


@dataclass
class ChunkData:
    """Represents a document chunk with metadata."""
    id: Optional[int]
    content: str
    chunk_index: int
    chunk_type: str  # paragraph, table, list, heading
    page_number: Optional[int]
    section: Optional[str]
    start_position: Optional[int]
    end_position: Optional[int]
    heading_context: Optional[List[str]]  # Parent headings hierarchy
    metadata: Dict[str, Any]


@dataclass
class IngestResult:
    """Result from document ingestion."""
    success: bool
    file_id: int
    filename: str
    num_chunks: int
    num_pages: Optional[int]
    num_tables: Optional[int]
    docling_json: Optional[Dict[str, Any]]
    error: Optional[str] = None


class DoclingChunker:
    """
    Intelligent document chunking using Docling's HierarchicalChunker.
    
    This service handles:
    1. Document parsing with full structure extraction
    2. Hierarchical chunking that preserves paragraphs, tables, lists
    3. Source location tracking for each chunk
    4. Vector embedding storage for semantic search
    """
    
    def __init__(self, vector_store=None, db_session=None):
        """
        Initialize the chunker.
        
        Args:
            vector_store: Optional VectorStore instance for embeddings
            db_session: Optional database session for chunk storage
        """
        self.vector_store = vector_store
        self.db_session = db_session
        self._docling_available = None
        self._chunker = None
    
    def _check_docling_availability(self) -> bool:
        """Check if Docling and chunking dependencies are available."""
        if self._docling_available is not None:
            return self._docling_available
            
        try:
            from docling.document_converter import DocumentConverter
            from docling.chunking import HierarchicalChunker
            self._docling_available = True
            logger.info("Docling HierarchicalChunker available")
        except ImportError as e:
            self._docling_available = False
            logger.warning(f"Docling chunking not available: {e}")
        
        return self._docling_available
    
    def _get_chunker(self):
        """Get or create the HierarchicalChunker instance."""
        if self._chunker is not None:
            return self._chunker
            
        if not self._check_docling_availability():
            return None
            
        try:
            from docling.chunking import HierarchicalChunker
            self._chunker = HierarchicalChunker()
            return self._chunker
        except Exception as e:
            logger.error(f"Failed to create HierarchicalChunker: {e}")
            return None
    
    async def ingest_document(
        self,
        file_path: str,
        opportunity_id: int,
        stored_file_id: int,
        store_vectors: bool = True
    ) -> IngestResult:
        """
        Full document ingestion with chunking and storage.
        
        Args:
            file_path: Path to the document file
            opportunity_id: ID of the opportunity
            stored_file_id: ID of the stored file record
            store_vectors: Whether to store embeddings in vector store
            
        Returns:
            IngestResult with ingestion statistics
        """
        filename = Path(file_path).name
        
        if not self._check_docling_availability():
            return IngestResult(
                success=False,
                file_id=stored_file_id,
                filename=filename,
                num_chunks=0,
                num_pages=None,
                num_tables=None,
                docling_json=None,
                error="Docling not available"
            )
        
        try:
            from docling.document_converter import DocumentConverter, PdfFormatOption
            from docling.datamodel.base_models import InputFormat
            from docling.datamodel.pipeline_options import PdfPipelineOptions
            
            logger.info(f"Starting ingestion of {filename}")
            
            # Configure pipeline for full extraction
            pipeline_options = PdfPipelineOptions()
            pipeline_options.do_ocr = False  # Enable OCR if needed later
            pipeline_options.do_table_structure = True
            
            converter = DocumentConverter(
                format_options={
                    InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
                }
            )
            
            # Convert document in thread pool
            loop = asyncio.get_running_loop()
            convert_func = partial(converter.convert, file_path)
            result = await loop.run_in_executor(None, convert_func)
            
            # Get the DoclingDocument
            doc = result.document
            docling_dict = doc.export_to_dict()
            
            # Extract metadata
            num_pages = getattr(doc, 'num_pages', None)
            num_tables = len(docling_dict.get('tables', []))
            
            # Perform hierarchical chunking
            chunks = await self._chunk_document(doc, stored_file_id, opportunity_id)
            
            logger.info(f"Created {len(chunks)} chunks from {filename}")
            
            # Store chunks in database if session provided
            if self.db_session and chunks:
                await self._store_chunks_in_db(chunks, stored_file_id, opportunity_id)
            
            # Store embeddings in vector store if enabled
            if store_vectors and self.vector_store and chunks:
                chunk_dicts = [
                    {
                        'id': chunk.id or idx,
                        'content': chunk.content,
                        'metadata': {
                            'chunk_type': chunk.chunk_type,
                            'page_number': chunk.page_number,
                            'section': chunk.section,
                            'file_id': stored_file_id
                        }
                    }
                    for idx, chunk in enumerate(chunks)
                ]
                await self.vector_store.add_chunks(opportunity_id, chunk_dicts)
            
            return IngestResult(
                success=True,
                file_id=stored_file_id,
                filename=filename,
                num_chunks=len(chunks),
                num_pages=num_pages,
                num_tables=num_tables,
                docling_json=docling_dict
            )
            
        except Exception as e:
            logger.error(f"Error ingesting {filename}: {e}", exc_info=True)
            return IngestResult(
                success=False,
                file_id=stored_file_id,
                filename=filename,
                num_chunks=0,
                num_pages=None,
                num_tables=None,
                docling_json=None,
                error=str(e)
            )
    
    async def _chunk_document(
        self,
        doc,
        stored_file_id: int,
        opportunity_id: int
    ) -> List[ChunkData]:
        """
        Chunk a DoclingDocument using HierarchicalChunker.
        
        Args:
            doc: The DoclingDocument object
            stored_file_id: ID of the stored file
            opportunity_id: ID of the opportunity
            
        Returns:
            List of ChunkData objects
        """
        chunker = self._get_chunker()
        if not chunker:
            return await self._fallback_chunk(doc)
        
        try:
            chunks = []
            chunk_iter = chunker.chunk(doc)
            
            for idx, chunk in enumerate(chunk_iter):
                # Extract chunk metadata
                meta = chunk.meta if hasattr(chunk, 'meta') else {}
                
                # Get heading context (parent headings)
                heading_context = []
                if hasattr(chunk, 'headings'):
                    heading_context = [h.text for h in chunk.headings if hasattr(h, 'text')]
                
                # Determine chunk type
                chunk_type = "paragraph"
                if hasattr(chunk, 'chunk_type'):
                    chunk_type = str(chunk.chunk_type)
                elif hasattr(meta, 'doc_items') and meta.doc_items:
                    first_item = meta.doc_items[0]
                    if hasattr(first_item, 'label'):
                        chunk_type = str(first_item.label).lower()
                
                # Get page number
                page_number = None
                if hasattr(meta, 'doc_items') and meta.doc_items:
                    first_item = meta.doc_items[0]
                    if hasattr(first_item, 'prov') and first_item.prov:
                        prov = first_item.prov[0] if isinstance(first_item.prov, list) else first_item.prov
                        page_number = getattr(prov, 'page_no', None)
                
                # Get text content
                content = chunk.text if hasattr(chunk, 'text') else str(chunk)
                
                chunks.append(ChunkData(
                    id=None,  # Will be assigned by DB
                    content=content,
                    chunk_index=idx,
                    chunk_type=chunk_type,
                    page_number=page_number,
                    section=self._detect_section(content, heading_context),
                    start_position=None,  # Could be extracted from meta if needed
                    end_position=None,
                    heading_context=heading_context,
                    metadata={
                        'stored_file_id': stored_file_id,
                        'opportunity_id': opportunity_id
                    }
                ))
            
            return chunks
            
        except Exception as e:
            logger.error(f"Error in hierarchical chunking: {e}", exc_info=True)
            return await self._fallback_chunk(doc)
    
    async def _fallback_chunk(self, doc) -> List[ChunkData]:
        """Fallback chunking when HierarchicalChunker fails."""
        try:
            markdown = doc.export_to_markdown()
            # Simple paragraph-based chunking
            paragraphs = [p.strip() for p in markdown.split('\n\n') if p.strip()]
            
            return [
                ChunkData(
                    id=None,
                    content=para,
                    chunk_index=idx,
                    chunk_type="paragraph",
                    page_number=None,
                    section=None,
                    start_position=None,
                    end_position=None,
                    heading_context=None,
                    metadata={}
                )
                for idx, para in enumerate(paragraphs)
            ]
        except Exception as e:
            logger.error(f"Fallback chunking failed: {e}")
            return []
    
    def _detect_section(self, content: str, headings: Optional[List[str]]) -> Optional[str]:
        """Detect which solicitation section this chunk belongs to."""
        import re
        
        # Check headings first
        if headings:
            for heading in headings:
                section_match = re.search(r'SECTION\s+([A-M])\b', heading.upper())
                if section_match:
                    return section_match.group(1)
        
        # Check content
        section_match = re.search(r'SECTION\s+([A-M])\b', content.upper()[:500])
        if section_match:
            return section_match.group(1)
        
        return None
    
    async def _store_chunks_in_db(
        self,
        chunks: List[ChunkData],
        stored_file_id: int,
        opportunity_id: int
    ) -> None:
        """Store chunks in the database."""
        try:
            from fedops_core.db.models import DocumentChunk
            
            for chunk in chunks:
                db_chunk = DocumentChunk(
                    stored_file_id=stored_file_id,
                    chunk_index=chunk.chunk_index,
                    content=chunk.content,
                    page_number=chunk.page_number,
                    section=chunk.section,
                    metadata_={
                        'chunk_type': chunk.chunk_type,
                        'heading_context': chunk.heading_context,
                        'opportunity_id': opportunity_id
                    }
                )
                self.db_session.add(db_chunk)
            
            await self.db_session.commit() if hasattr(self.db_session, 'commit') else self.db_session.commit()
            logger.info(f"Stored {len(chunks)} chunks in database")
            
        except Exception as e:
            logger.error(f"Error storing chunks in database: {e}")
    
    async def get_chunks_for_section(
        self,
        opportunity_id: int,
        section_type: str,
        top_k: int = 20
    ) -> List[ChunkData]:
        """
        Retrieve chunks relevant to a specific section type.
        
        Uses vector search with section-specific queries.
        """
        if not self.vector_store:
            logger.warning("Vector store not configured")
            return []
        
        # Section-specific search queries
        section_queries = {
            'L': "instructions to offerors proposal submission requirements format page limits",
            'M': "evaluation criteria factors scoring methodology technical approach past performance",
            'H': "special contract requirements key personnel security clearance phase-in transition",
            'C': "statement of work performance requirements tasks deliverables objectives scope",
            'B': "pricing schedule contract line items CLIN labor categories rates",
            'I': "contract clauses FAR DFARS terms conditions",
            'K': "representations certifications small business compliance"
        }
        
        query = section_queries.get(section_type.upper(), f"section {section_type}")
        
        results = await self.vector_store.search(
            opportunity_id=opportunity_id,
            query=query,
            top_k=top_k,
            filter_metadata={"section": section_type.upper()} if section_type else None
        )
        
        return [
            ChunkData(
                id=r.chunk_id,
                content=r.content,
                chunk_index=0,
                chunk_type=r.metadata.get('chunk_type', 'unknown'),
                page_number=r.metadata.get('page_number'),
                section=r.metadata.get('section'),
                start_position=None,
                end_position=None,
                heading_context=None,
                metadata=r.metadata
            )
            for r in results
        ]
    
    async def semantic_search(
        self,
        query: str,
        opportunity_id: int,
        top_k: int = 10
    ) -> List[ChunkData]:
        """
        Perform semantic search for relevant chunks.
        
        Args:
            query: Natural language query
            opportunity_id: The opportunity ID
            top_k: Number of results to return
            
        Returns:
            List of relevant ChunkData objects
        """
        if not self.vector_store:
            return []
        
        results = await self.vector_store.search(
            opportunity_id=opportunity_id,
            query=query,
            top_k=top_k
        )
        
        return [
            ChunkData(
                id=r.chunk_id,
                content=r.content,
                chunk_index=0,
                chunk_type=r.metadata.get('chunk_type', 'unknown'),
                page_number=r.metadata.get('page_number'),
                section=r.metadata.get('section'),
                start_position=None,
                end_position=None,
                heading_context=None,
                metadata={**r.metadata, 'score': r.score}
            )
            for r in results
        ]
