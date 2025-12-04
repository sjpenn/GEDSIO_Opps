import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock
from fedops_core.services.shredding_service import ShreddingService
from fedops_core.db.models import StoredFile, DocumentChunk

@pytest.fixture
def mock_db():
    mock = AsyncMock()
    # Mock add/commit/refresh to do nothing but be awaitable
    mock.add = MagicMock() # add is usually synchronous in SQLAlchemy, but let's check. 
    # In AsyncSession, add is synchronous (it just adds to session state).
    # commit and refresh are async.
    mock.commit = AsyncMock()
    mock.refresh = AsyncMock()
    mock.execute = AsyncMock()
    return mock

@pytest.mark.asyncio
async def test_shredding_service(mock_db):
    # Setup
    service = ShreddingService(mock_db)
    
    # Create a mock file
    file = StoredFile(id=1, filename="test.txt", file_path="/tmp/test.txt", file_type="txt")
    # We don't need to actually add it to the mock_db since it's a mock
    
    # Create content larger than chunk size (1000)
    # 1200 chars
    content = "A" * 900 + ". " + "B" * 298
    
    # Mock the execute result for verification
    # When we query for chunks, we want to return the chunks that were added.
    # But since we are mocking, we can just inspect the calls to mock_db.add
    
    # Execute
    count = await service.shred_document(file.id, content)
    
    # Verify
    assert count > 1
    
    # Verify calls to db.add
    assert mock_db.add.call_count == count
    
    # Inspect the chunks passed to add
    added_chunks = [call.args[0] for call in mock_db.add.call_args_list]
    assert len(added_chunks) == count
    
    first_chunk = added_chunks[0]
    assert isinstance(first_chunk, DocumentChunk)
    assert first_chunk.chunk_index == 0
    assert len(first_chunk.content) <= 1000
    
    # Test overlap/splitting
    assert first_chunk.content == "A" * 900 + ". "
    
    second_chunk = added_chunks[1]
    assert second_chunk.content.startswith("A")
    assert "B" in second_chunk.content

