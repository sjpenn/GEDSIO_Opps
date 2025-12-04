import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from sqlalchemy.orm import Session
from fedops_agents.document_analysis_agent import DocumentAnalysisAgent
from fedops_core.db.models import Opportunity, StoredFile

@pytest.fixture
def mock_db():
    db = MagicMock(spec=Session)
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db.execute = AsyncMock()
    return db

@pytest.mark.asyncio
async def test_document_analysis_agent_with_extracted_data(mock_db):
    # Setup
    agent = DocumentAnalysisAgent(mock_db)
    opportunity_id = 1
    
    # Mock DB response
    mock_opp = Opportunity(id=opportunity_id, title="Test Opp")
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_opp
    mock_db.execute.return_value = mock_result
    
    # Mock AIService
    with patch('fedops_agents.document_analysis_agent.AIService') as MockAI:
        mock_ai_instance = MockAI.return_value
        mock_ai_instance.analyze_opportunity = AsyncMock(return_value={"summary": "AI Summary"})
        
        # Input extracted data
        extracted_data = {
            "section_l": {"requirements": "Test Req"},
            "source_documents": [{"filename": "doc.pdf", "type": "section_l"}]
        }
        
        # Execute
        result = await agent.execute(opportunity_id, extracted_data=extracted_data)
        
        # Verify
        assert result["status"] == "success"
        assert result["solicitation_details"]["extracted_data"]["section_l"] == {"requirements": "Test Req"}
        assert result["solicitation_details"]["ai_analysis"] == {"summary": "AI Summary"}
        assert len(result["source_documents"]) == 1

@pytest.mark.asyncio
async def test_document_analysis_agent_without_extracted_data(mock_db):
    # Setup
    agent = DocumentAnalysisAgent(mock_db)
    opportunity_id = 1
    
    # Mock DB responses
    mock_opp = Opportunity(id=opportunity_id, title="Test Opp")
    
    # Mock files
    mock_file = StoredFile(file_path="/tmp/test.pdf", filename="test.pdf", opportunity_id=opportunity_id)
    
    # Configure mock_db.execute side effects
    # First call for Opportunity, second call for StoredFile
    mock_result_opp = MagicMock()
    mock_result_opp.scalar_one_or_none.return_value = mock_opp
    
    mock_result_files = MagicMock()
    mock_result_files.scalars.return_value.all.return_value = [mock_file]
    
    mock_db.execute.side_effect = [mock_result_opp, mock_result_files]
    
    # Mock DocumentExtractor
    with patch('fedops_agents.document_analysis_agent.DocumentExtractor') as MockExtractor:
        mock_extractor_instance = MockExtractor.return_value
        mock_extractor_instance.extract_all_documents = AsyncMock(return_value={
            "section_l": {"requirements": "Extracted Req"},
            "source_documents": [{"filename": "test.pdf", "type": "section_l"}]
        })
        
        # Mock AIService
        with patch('fedops_agents.document_analysis_agent.AIService') as MockAI:
            mock_ai_instance = MockAI.return_value
            mock_ai_instance.analyze_opportunity = AsyncMock(return_value={"summary": "AI Summary"})
            
            # Execute
            result = await agent.execute(opportunity_id)
            
            # Verify
            assert result["status"] == "success"
            assert result["solicitation_details"]["extracted_data"]["section_l"] == {"requirements": "Extracted Req"}
            assert len(result["source_documents"]) == 1
            mock_extractor_instance.extract_all_documents.assert_called_once()
