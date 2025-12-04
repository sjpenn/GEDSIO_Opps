import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from fedops_core.services.document_extractor import DocumentExtractor
from fedops_core.prompts import DocumentType

@pytest.fixture
def mock_genai():
    with patch('fedops_core.services.document_extractor.genai') as mock:
        mock_model = MagicMock()
        mock.GenerativeModel.return_value = mock_model
        yield mock_model

@pytest.fixture
def document_extractor(mock_genai):
    return DocumentExtractor()

@pytest.mark.asyncio
async def test_extract_all_documents(document_extractor, mock_genai):
    # Mock file reading
    with patch.object(document_extractor, '_read_file', new_callable=AsyncMock) as mock_read:
        mock_read.return_value = "Sample content for Section L"
        
        # Mock AI response
        mock_response = MagicMock()
        mock_response.text = '{"page_limits": 50, "format": "PDF"}'
        mock_genai.generate_content_async = AsyncMock(return_value=mock_response)
        
        files = [
            {"file_path": "/tmp/Section_L.pdf", "filename": "Section_L.pdf"}
        ]
        
        # Mock document type detection
        with patch('fedops_core.services.document_extractor.determine_document_type') as mock_type:
            mock_type.return_value = DocumentType.SECTION_L
            
            result = await document_extractor.extract_all_documents(files)
            
            assert "section_l" in result
            assert result["section_l"] == {"page_limits": 50, "format": "PDF"}
            assert len(result["source_documents"]) == 1
            assert result["source_documents"][0]["type"] == "section_l"

@pytest.mark.asyncio
async def test_read_text_file(document_extractor):
    with patch('builtins.open', new_callable=MagicMock) as mock_open:
        mock_file = MagicMock()
        mock_file.__enter__.return_value.read.return_value = "Text content"
        mock_open.return_value = mock_file
        
        content = await document_extractor._read_file("test.txt")
        assert content == "Text content"

@pytest.mark.asyncio
async def test_read_pdf_file(document_extractor):
    # Mock pypdf in sys.modules
    mock_pypdf = MagicMock()
    mock_reader = MagicMock()
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "PDF Page Content"
    mock_reader.pages = [mock_page]
    mock_pypdf.PdfReader.return_value = mock_reader
    
    with patch.dict('sys.modules', {'pypdf': mock_pypdf}):
        content = await document_extractor._parse_pdf("test.pdf")
        assert content == "PDF Page Content"

@pytest.mark.asyncio
async def test_ai_extract_json_parsing(document_extractor, mock_genai):
    mock_response = MagicMock()
    mock_response.text = 'Here is the JSON: {"key": "value"}'
    mock_genai.generate_content_async = AsyncMock(return_value=mock_response)
    
    result = await document_extractor._ai_extract("prompt", "Section Test")
    assert result == {"key": "value"}

@pytest.mark.asyncio
async def test_ai_extract_no_json(document_extractor, mock_genai):
    mock_response = MagicMock()
    mock_response.text = 'No JSON here'
    mock_genai.generate_content_async = AsyncMock(return_value=mock_response)
    
    result = await document_extractor._ai_extract("prompt", "Section Test")
    assert result is None
