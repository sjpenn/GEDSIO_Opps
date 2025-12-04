import pytest
from unittest.mock import AsyncMock, MagicMock
from fedops_core.services.partner_service import PartnerService
from fedops_core.db.models import Entity, Proposal, ProposalRequirement
from fedops_core.db.team_models import TeamMember

@pytest.fixture
def mock_db():
    return AsyncMock()

@pytest.fixture
def partner_service(mock_db):
    return PartnerService(mock_db)

@pytest.mark.asyncio
async def test_extract_entity_details(partner_service):
    # Mock Entity with SAM response
    entity = Entity(
        uei="TESTUEI123",
        full_response={
            "entityData": [{
                "coreData": {
                    "physicalAddress": {"city": "Test City", "state": "TS"},
                    "mailingAddress": {"city": "Mail City", "state": "MS"}
                },
                "assertions": {
                    "goodsAndServices": {
                        "naicsList": [{"naicsCode": "541511", "naicsDescription": "Custom Computer Programming"}],
                        "pscList": [{"pscCode": "D302", "pscDescription": "IT Systems Development"}]
                    },
                    "businessTypes": {
                        "businessTypeList": [{"businessTypeCode": "2X", "businessTypeDescription": "For Profit"}]
                    }
                }
            }]
        }
    )
    
    details = await partner_service.extract_entity_details(entity)
    
    assert len(details["locations"]) == 2
    assert details["locations"][0]["type"] == "Physical"
    assert len(details["capabilities"]) == 2
    assert details["capabilities"][0]["code"] == "541511"
    assert details["business_types"][0]["code"] == "2X"

@pytest.mark.asyncio
async def test_analyze_capability_gaps(partner_service, mock_db):
    # Mock data
    opp_id = 1
    team_id = 1
    
    # Mock Proposal and Requirements
    mock_proposal = Proposal(id=100, opportunity_id=opp_id)
    mock_reqs = [
        ProposalRequirement(id=1, proposal_id=100, requirement_text="Must have experience with Custom Computer Programming"),
        ProposalRequirement(id=2, proposal_id=100, requirement_text="Requires Cloud Computing expertise")
    ]
    
    # Mock Team Members
    mock_members = [
        TeamMember(id=1, team_id=team_id, entity_uei="UEI1", role="PRIME"),
        TeamMember(id=2, team_id=team_id, entity_uei="UEI2", role="SUB")
    ]
    
    # Mock Entities
    entity1 = Entity(uei="UEI1", capabilities=[{"code": "541511", "description": "Custom Computer Programming"}])
    entity2 = Entity(uei="UEI2", capabilities=[{"code": "541512", "description": "Computer Systems Design"}])
    
    # Setup mock returns
    # 1. Get Proposal
    mock_db.execute.side_effect = [
        MagicMock(scalars=lambda: MagicMock(first=lambda: mock_proposal)), # Proposal
        MagicMock(scalars=lambda: MagicMock(all=lambda: mock_reqs)),      # Requirements
        MagicMock(scalars=lambda: MagicMock(all=lambda: mock_members)),    # Team Members
        MagicMock(scalars=lambda: MagicMock(first=lambda: entity1)),       # Entity 1
        MagicMock(scalars=lambda: MagicMock(first=lambda: entity2)),       # Entity 2
    ]
    
    # Run analysis
    result = await partner_service.analyze_capability_gaps(team_id, opp_id)
    
    # Verify
    assert result["total_requirements"] == 2
    assert result["covered_count"] == 1 # Only "Custom Computer Programming" matches
    assert result["uncovered_count"] == 1
    assert result["coverage_percentage"] == 50.0
    assert result["gaps"][0] == "Requires Cloud Computing expertise"
