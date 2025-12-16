"""
Tests for DoclingChunker service.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from fedops_core.services.docling_chunker import DoclingChunker, ChunkData, IngestResult


@pytest.fixture
def chunker():
    """Create DoclingChunker instance without dependencies"""
    return DoclingChunker()


class TestDoclingChunker:
    """Test DoclingChunker functionality"""
    
    def test_initialization(self, chunker):
        """Test that chunker initializes correctly"""
        assert chunker is not None
        assert chunker.vector_store is None
        assert chunker.db_session is None
    
    def test_docling_availability_check(self, chunker):
        """Test Docling availability detection"""
        result = chunker._check_docling_availability()
        assert isinstance(result, bool)
    
    def test_section_detection(self, chunker):
        """Test section letter detection from content"""
        # Test explicit section header
        content = "SECTION L: INSTRUCTIONS TO OFFERORS"
        section = chunker._detect_section(content, None)
        assert section == "L"
        
        # Test from headings
        headings = ["Section M - Evaluation Criteria"]
        section = chunker._detect_section("", headings)
        assert section == "M"
        
        # Test no section found
        content = "This is regular content without section markers"
        section = chunker._detect_section(content, None)
        assert section is None
    
    @pytest.mark.asyncio
    async def test_fallback_chunk(self, chunker):
        """Test fallback chunking when HierarchicalChunker unavailable"""
        # Create mock document
        mock_doc = MagicMock()
        mock_doc.export_to_markdown.return_value = "Paragraph 1\n\nParagraph 2\n\nParagraph 3"
        
        chunks = await chunker._fallback_chunk(mock_doc)
        
        assert len(chunks) == 3
        assert chunks[0].content == "Paragraph 1"
        assert chunks[1].content == "Paragraph 2"
        assert chunks[2].content == "Paragraph 3"
        assert all(c.chunk_type == "paragraph" for c in chunks)


class TestChunkData:
    """Test ChunkData dataclass"""
    
    def test_chunk_data_creation(self):
        """Test creating chunk data"""
        chunk = ChunkData(
            id=1,
            content="Test content",
            chunk_index=0,
            chunk_type="paragraph",
            page_number=5,
            section="L",
            start_position=100,
            end_position=200,
            heading_context=["Section L", "Instructions"],
            metadata={"test": True}
        )
        
        assert chunk.id == 1
        assert chunk.content == "Test content"
        assert chunk.chunk_index == 0
        assert chunk.chunk_type == "paragraph"
        assert chunk.page_number == 5
        assert chunk.section == "L"
        assert chunk.start_position == 100
        assert chunk.end_position == 200
        assert chunk.heading_context == ["Section L", "Instructions"]
        assert chunk.metadata == {"test": True}


class TestIngestResult:
    """Test IngestResult dataclass"""
    
    def test_successful_result(self):
        """Test successful ingestion result"""
        result = IngestResult(
            success=True,
            file_id=123,
            filename="test.pdf",
            num_chunks=50,
            num_pages=10,
            num_tables=3,
            docling_json={"test": "data"}
        )
        
        assert result.success is True
        assert result.file_id == 123
        assert result.filename == "test.pdf"
        assert result.num_chunks == 50
        assert result.num_pages == 10
        assert result.num_tables == 3
        assert result.error is None
    
    def test_failed_result(self):
        """Test failed ingestion result"""
        result = IngestResult(
            success=False,
            file_id=456,
            filename="bad.pdf",
            num_chunks=0,
            num_pages=None,
            num_tables=None,
            docling_json=None,
            error="File not found"
        )
        
        assert result.success is False
        assert result.error == "File not found"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
