import asyncio
import sys
import os
from unittest.mock import MagicMock, AsyncMock, patch

# Add project root to path
sys.path.append(os.path.join(os.getcwd(), 'fedops'))

from fedops_agents.capability_agent import CapabilityMappingAgent
from fedops_core.db.models import Opportunity, CompanyProfile, StoredFile
from fedops_core.prompts import DocumentType

async def test_capability_agent():
    print("Starting CapabilityMappingAgent verification...")
    
    # Mock DB Session
    mock_db = AsyncMock()
    
    # Mock Opportunity
    mock_opp = Opportunity(
        id=1, 
        title="Test Opp", 
        department="Test Dept", 
        description="Test Description",
        naics_code="541511",
        type_of_set_aside="Small Business"
    )
    
    # Mock Company Profile
    mock_company = CompanyProfile(
        target_naics=["541511"],
        target_keywords=["AI", "Cloud"]
    )
    
    # Mock Stored Files
    mock_file_l = StoredFile(
        filename="Section_L.pdf",
        file_path="/tmp/Section_L.pdf",
        parsed_content="Instructions to Offerors: Submit 3 past performance examples."
    )
    mock_file_m = StoredFile(
        filename="Section_M.pdf",
        file_path="/tmp/Section_M.pdf",
        parsed_content="Evaluation Criteria: Past Performance is significantly more important than Price."
    )
    mock_file_sow = StoredFile(
        filename="SOW.pdf",
        file_path="/tmp/SOW.pdf",
        parsed_content="Scope of Work: The contractor shall provide Key Personnel including a Project Manager."
    )
    
    # Setup DB execute results
    # We need to handle multiple calls to execute()
    # 1. Opportunity
    # 2. CompanyProfile
    # 3. EntityContext (complex, maybe mock the service instead)
    # 4. StoredFiles (for CapabilityAgent)
    # 5. Opportunity (for PersonnelAgent)
    # 6. StoredFiles (for PersonnelAgent)
    # 7. Opportunity (for PastPerfAgent)
    # 8. StoredFiles (for PastPerfAgent)
    
    # It's easier to mock the EntityContextService and the DB results for scalars/all
    
    async def mock_execute(stmt):
        mock_result = MagicMock()
        # Simple heuristic to return different things based on the query
        # This is brittle but sufficient for a quick verification script
        s = str(stmt)
        if "opportunities" in s:
            mock_result.scalar_one_or_none.return_value = mock_opp
        elif "company_profiles" in s:
            mock_result.scalar_one_or_none.return_value = mock_company
        elif "stored_files" in s:
            mock_result.scalars.return_value.all.return_value = [mock_file_l, mock_file_m, mock_file_sow]
        return mock_result

    mock_db.execute = AsyncMock(side_effect=mock_execute)
    
    # Mock EntityContextService
    with patch('fedops_core.services.entity_context_service.EntityContextService') as MockEntityService:
        mock_entity_service = MockEntityService.return_value
        mock_entity_service.get_combined_context = AsyncMock(return_value={
            "entity": {"formatted_context": "Entity Context", "exists": True},
            "team": {"formatted_context": "Team Context", "exists": False}
        })
        
        # Mock AIService
        with patch('fedops_core.services.ai_service.AIService') as MockAIService:
            mock_ai_service = MockAIService.return_value
            mock_ai_service.analyze_opportunity = AsyncMock(return_value={
                "summary": "Mock AI Analysis",
                "score": 85.0
            })
            
            # Initialize Agent
            agent = CapabilityMappingAgent(mock_db)
            # Inject mocked AI service (since it's instantiated in __init__)
            agent.ai_service = mock_ai_service
            
            # Also patch the AI service instantiation inside the sub-agents?
            # The sub-agents are instantiated inside execute().
            # We can patch the class itself.
            
            # Execute
            result = await agent.execute(1)
            
            print("\nExecution Result:")
            print(result)
            
            # Verify AI Service calls
            print("\nVerifying AI Service calls...")
            print(f"Call count: {mock_ai_service.analyze_opportunity.call_count}")
            
            # We expect 4 calls: Strategic, Capacity, Personnel, PastPerf
            # Note: Personnel and PastPerf agents instantiate their own AIService.
            # Since we patched the class 'fedops_core.services.ai_service.AIService', 
            # new instances should also be mocks.
            
            if mock_ai_service.analyze_opportunity.call_count >= 1:
                print("SUCCESS: AI Service was called.")
                
                # Check if prompts contained document content
                calls = mock_ai_service.analyze_opportunity.call_args_list
                for i, call in enumerate(calls):
                    prompt = call[0][0]
                    print(f"\nCall {i+1} Prompt snippet:")
                    print(prompt[:200] + "...")
                    if "Solicitation Documents" in prompt:
                        print("  -> Contains 'Solicitation Documents' section: YES")
                    else:
                        print("  -> Contains 'Solicitation Documents' section: NO")
            else:
                print("FAILURE: AI Service was not called.")

if __name__ == "__main__":
    asyncio.run(test_capability_agent())
