"""
Tests for VectorStore service (ChromaDB integration).
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from fedops_core.services.vector_store import VectorStore, SearchResult


@pytest.fixture
def vector_store():
    """Create VectorStore instance"""
    return VectorStore(persist_dir="./test_chroma_db")


class TestVectorStore:
    """Test VectorStore functionality"""
    
    def test_initialization(self, vector_store):
        """Test that store initializes correctly"""
        assert vector_store is not None
        assert vector_store.persist_dir == "./test_chroma_db"
        assert vector_store._initialized is False  # Lazy initialization
    
    def test_collection_name(self, vector_store):
        """Test collection name generation"""
        name = vector_store._get_collection_name(123)
        assert name == "opportunity_123"
        
        name = vector_store._get_collection_name(999)
        assert name == "opportunity_999"
    
    @pytest.mark.asyncio
    async def test_add_chunks_without_chromadb(self, vector_store):
        """Test graceful handling when ChromaDB unavailable"""
        # Mock _ensure_initialized to return False (ChromaDB not available)
        vector_store._ensure_initialized = MagicMock(return_value=False)
        
        chunks = [
            {"id": 1, "content": "Test chunk", "metadata": {"page": 1}}
        ]
        
        result = await vector_store.add_chunks(123, chunks)
        assert result == []
    
    @pytest.mark.asyncio
    async def test_search_without_chromadb(self, vector_store):
        """Test search returns empty when ChromaDB unavailable"""
        vector_store._ensure_initialized = MagicMock(return_value=False)
        
        results = await vector_store.search(123, "test query")
        assert results == []


class TestSearchResult:
    """Test SearchResult dataclass"""
    
    def test_search_result_creation(self):
        """Test creating search result"""
        result = SearchResult(
            chunk_id=1,
            content="This is matching content",
            score=0.85,
            metadata={"page_number": 5, "section": "L"}
        )
        
        assert result.chunk_id == 1
        assert result.content == "This is matching content"
        assert result.score == 0.85
        assert result.metadata["page_number"] == 5
        assert result.metadata["section"] == "L"
    
    def test_search_result_score_range(self):
        """Test score is within expected range"""
        result = SearchResult(
            chunk_id=1,
            content="Test",
            score=0.95,
            metadata={}
        )
        
        assert 0.0 <= result.score <= 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
