import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session
from fedops_agents.orchestrator import OrchestratorAgent
from fedops_agents.ingestion_agent import IngestionAgent
from fedops_agents.document_analysis_agent import DocumentAnalysisAgent
from fedops_agents.compliance_agent import ComplianceAgent
from fedops_core.db.models import Opportunity, OpportunityScore, AgentActivityLog

from fedops_agents.capability_agent import CapabilityMappingAgent
from fedops_agents.financial_agent import FinancialAnalysisAgent
from fedops_core.db.models import Opportunity, OpportunityScore, AgentActivityLog, CompanyProfile

@pytest.fixture
def mock_db():
    return MagicMock(spec=Session)

def test_ingestion_agent(mock_db):
    agent = IngestionAgent(mock_db)
    result = agent.execute(opportunity_id=1)
    assert result["status"] == "success"
    assert result["data_updated"] is True
    mock_db.add.assert_called()

def test_document_analysis_agent(mock_db):
    agent = DocumentAnalysisAgent(mock_db)
    result = agent.execute(opportunity_id=1)
    assert result["status"] == "success"
    assert "requirements" in result
    mock_db.add.assert_called()

def test_compliance_agent(mock_db):
    agent = ComplianceAgent(mock_db)
    mock_opp = Opportunity(id=1)
    mock_db.query.return_value.filter.return_value.first.return_value = mock_opp
    
    result = agent.execute(opportunity_id=1)
    assert result["status"] == "success"
    assert result["compliance_status"] == "COMPLIANT"
    mock_db.add.assert_called()

def test_capability_agent(mock_db):
    agent = CapabilityMappingAgent(mock_db)
    mock_opp = Opportunity(id=1, naics_code="541511", description="Software development")
    mock_company = CompanyProfile(target_naics=["541511"], target_keywords=["software"])
    
    # Mock query side effects: first call returns opp, second returns company
    mock_db.query.return_value.filter.return_value.first.return_value = mock_opp
    mock_db.query.return_value.first.return_value = mock_company
    
    result = agent.execute(opportunity_id=1)
    assert result["status"] == "success"
    assert result["internal_capacity_score"] >= 60.0 # 50 for NAICS + 10 for keyword
    mock_db.add.assert_called()

def test_financial_agent(mock_db):
    agent = FinancialAnalysisAgent(mock_db)
    mock_opp = Opportunity(id=1, type_of_set_aside="SBA")
    mock_db.query.return_value.filter.return_value.first.return_value = mock_opp
    
    result = agent.execute(opportunity_id=1)
    assert result["status"] == "success"
    assert result["financial_viability_score"] >= 70.0 # 50 base + 20 boost
    mock_db.add.assert_called()

def test_orchestrator_agent(mock_db):
    agent = OrchestratorAgent(mock_db)
    
    # Mock all sub-agents execution
    with patch('fedops_agents.orchestrator.DocumentAnalysisAgent') as MockDoc, \
         patch('fedops_agents.orchestrator.ComplianceAgent') as MockComp, \
         patch('fedops_agents.orchestrator.CapabilityMappingAgent') as MockCap, \
         patch('fedops_agents.orchestrator.FinancialAnalysisAgent') as MockFin:
        
        MockDoc.return_value.execute.return_value = {"status": "success"}
        MockComp.return_value.execute.return_value = {"status": "success", "risk_score": 10.0}
        MockCap.return_value.execute.return_value = {"status": "success", "internal_capacity_score": 80.0}
        MockFin.return_value.execute.return_value = {"status": "success", "financial_viability_score": 90.0}
        
        # Mock score entry creation
        mock_score = OpportunityScore()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_score
        
        result = agent.execute(opportunity_id=1)
        
        assert result["status"] == "success"
        assert result["score"] > 0
        # Verify weighted score calculation logic roughly
        # Risk (10) -> Contribution (100-10)*0.2 = 18
        # Cap (80) -> 80*0.15 = 12
        # Fin (90) -> 90*0.25 = 22.5
        # Strat (50) -> 50*0.3 = 15
        # Data (100) -> 100*0.1 = 10
        # Total = 18 + 12 + 22.5 + 15 + 10 = 77.5
        assert abs(result["score"] - 77.5) < 0.1
        assert mock_score.go_no_go_decision == "GO"

