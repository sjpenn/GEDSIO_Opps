import pytest
from unittest.mock import MagicMock, AsyncMock
from fedops_core.services.shredding_service import ShreddingService
from fedops_core.services.advanced_parser import ParsedElement
from fedops_core.db.models import DocumentChunk

@pytest.fixture
def mock_db():
    mock = AsyncMock()
    mock.add = MagicMock()
    mock.commit = AsyncMock()
    mock.refresh = AsyncMock()
    mock.execute = AsyncMock()
    return mock

@pytest.mark.asyncio
async def test_advanced_shredding_with_page_numbers(mock_db):
    """Test that page numbers are correctly assigned to chunks"""
    service = ShreddingService(mock_db)
    
    # Create mock parsed elements from multiple pages
    elements = [
        ParsedElement("This is content on page 1.", "NarrativeText", page_number=1),
        ParsedElement("More content on page 1.", "NarrativeText", page_number=1),
        ParsedElement("Content on page 2.", "NarrativeText", page_number=2),
        ParsedElement("Additional content on page 2.", "NarrativeText", page_number=2),
    ]
    
    count = await service.shred_document(1, elements)
    
    # Should have created at least 2 chunks (one per page)
    assert count >= 2
    
    # Inspect chunks
    added_chunks = [call.args[0] for call in mock_db.add.call_args_list]
    
    # First chunk should be from page 1
    assert added_chunks[0].page_number == 1
    assert "page 1" in added_chunks[0].content
    
    # Last chunk should be from page 2
    assert added_chunks[-1].page_number == 2
    assert "page 2" in added_chunks[-1].content

@pytest.mark.asyncio
async def test_section_detection(mock_db):
    """Test that sections L and M are correctly detected"""
    service = ShreddingService(mock_db)
    
    # Create elements with section headers
    elements = [
        ParsedElement("SECTION L", "Title", page_number=5),
        ParsedElement("Instructions for proposal preparation.", "NarrativeText", page_number=5),
        ParsedElement("SECTION M", "Title", page_number=8),
        ParsedElement("Evaluation criteria for this proposal.", "NarrativeText", page_number=8),
    ]
    
    count = await service.shred_document(1, elements)
    
    added_chunks = [call.args[0] for call in mock_db.add.call_args_list]
    
    # DEBUG
    print(f"\nTotal chunks created: {count}")
    for i, chunk in enumerate(added_chunks):
        print(f"Chunk {i}: section={chunk.section}, page={chunk.page_number}, content={chunk.content[:50]}...")
    
    # Find chunks with sections
    section_l_chunks = [c for c in added_chunks if c.section == "L"]
    section_m_chunks = [c for c in added_chunks if c.section == "M"]
    
    print(f"Section L chunks: {len(section_l_chunks)}")
    print(f"Section M chunks: {len(section_m_chunks)}")
    
    assert len(section_l_chunks) > 0
    assert len(section_m_chunks) > 0
    
    # Verify content
    assert "Instructions" in section_l_chunks[0].content or "SECTION L" in section_l_chunks[0].content
    assert "Evaluation" in section_m_chunks[0].content or "SECTION M" in section_m_chunks[0].content

@pytest.mark.asyncio
async def test_legacy_string_shredding_still_works(mock_db):
    """Test that legacy string-based shredding still works"""
    service = ShreddingService(mock_db)
    
    content = "A" * 1200  # Simple content over chunk size
    
    count = await service.shred_document(1, content)
    
    assert count > 1
    
    added_chunks = [call.args[0] for call in mock_db.add.call_args_list]
    
    # Legacy chunks should have None for page_number and section
    assert added_chunks[0].page_number is None
    assert added_chunks[0].section is None

@pytest.mark.asyncio
async def test_chunk_size_limit(mock_db):
    """Test that chunks respect the size limit"""
    service = ShreddingService(mock_db)
    
    # Create a very long piece of text as a single element
    long_text = "word " * 300  # ~1500 chars
    elements = [
        ParsedElement(long_text, "NarrativeText", page_number=1),
    ]
    
    count = await service.shred_document(1, elements)
    
    added_chunks = [call.args[0] for call in mock_db.add.call_args_list]
    
    # Should have split into multiple chunks
    assert count > 1
    
    # Each chunk should be under the limit (1000) or close to it
    for chunk in added_chunks:
        assert len(chunk.content) <= 1200  # Allow some buffer

@pytest.mark.asyncio
async def test_mixed_section_detection(mock_db):
    """Test detection of various section formats"""
    service = ShreddingService(mock_db)
    
    elements = [
        ParsedElement("Section A - General Information", "Title", page_number=1),
        ParsedElement("SECTION B", "Title", page_number=2),
        ParsedElement("section l: Instructions", "Title", page_number=10),
        ParsedElement("Content under section L", "NarrativeText", page_number=10),
    ]
    
    count = await service.shred_document(1, elements)
    
    added_chunks = [call.args[0] for call in mock_db.add.call_args_list]
    
    # Should detect sections A, B, and L
    sections_found = set(c.section for c in added_chunks if c.section)
    
    assert "A" in sections_found
    assert "B" in sections_found
    assert "L" in sections_found
