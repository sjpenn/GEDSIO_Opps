from typing import Dict, Any
from sqlalchemy.orm import Session
from fedops_agents.base_agent import BaseAgent
from fedops_core.db.models import Opportunity, OpportunityScore

from fedops_agents.ingestion_agent import IngestionAgent
from fedops_agents.document_analysis_agent import DocumentAnalysisAgent
from fedops_agents.compliance_agent import ComplianceAgent
from fedops_agents.capability_agent import CapabilityMappingAgent
from fedops_agents.financial_agent import FinancialAnalysisAgent

class OrchestratorAgent(BaseAgent):
    def __init__(self, db: Session):
        super().__init__("OrchestratorAgent", db)

    def execute(self, opportunity_id: int, **kwargs) -> Dict[str, Any]:
        self.log_activity(opportunity_id, "START_WORKFLOW", "IN_PROGRESS", {"step": "init"})
        
        try:
            # 1. Ingestion (Placeholder)
            # ingestion_agent = IngestionAgent(self.db)
            # ingestion_agent.execute(opportunity_id)

            # 2. Document Analysis (Sequential)
            doc_agent = DocumentAnalysisAgent(self.db)
            doc_agent.execute(opportunity_id)

            # 3. Concurrent Analysis
            self.log_activity(opportunity_id, "CONCURRENT_ANALYSIS", "IN_PROGRESS")
            
            # Compliance
            comp_agent = ComplianceAgent(self.db)
            comp_results = comp_agent.execute(opportunity_id)
            
            # Capability
            cap_agent = CapabilityMappingAgent(self.db)
            cap_results = cap_agent.execute(opportunity_id)
            
            # Financial
            fin_agent = FinancialAnalysisAgent(self.db)
            fin_results = fin_agent.execute(opportunity_id)

            # 4. Score Calculation
            score_data = {
                "contract_risk_score": comp_results.get("risk_score", 0.0),
                "internal_capacity_score": cap_results.get("internal_capacity_score", 0.0),
                "financial_viability_score": fin_results.get("financial_viability_score", 0.0),
                # Strategic alignment and data integrity are placeholders for now
                "strategic_alignment_score": 50.0, 
                "data_integrity_score": 100.0
            }
            
            final_score = self.calculate_score(opportunity_id, score_data)
            
            self.log_activity(opportunity_id, "END_WORKFLOW", "SUCCESS", {"final_score": final_score})
            return {"status": "success", "score": final_score}

        except Exception as e:
            self.log_activity(opportunity_id, "WORKFLOW_ERROR", "FAILURE", {"error": str(e)})
            raise e

    def calculate_score(self, opportunity_id: int, scores: Dict[str, float]) -> float:
        score_entry = self.db.query(OpportunityScore).filter(OpportunityScore.opportunity_id == opportunity_id).first()
        if not score_entry:
            score_entry = OpportunityScore(opportunity_id=opportunity_id)
            self.db.add(score_entry)
        
        # Weights
        # Strategic Alignment: 30%
        # Financial Viability: 25%
        # Contract Risk: 20%
        # Internal Capacity: 15%
        # Data Integrity: 10%
        
        w_strategic = 0.30
        w_financial = 0.25
        w_risk = 0.20
        w_capacity = 0.15
        w_data = 0.10
        
        # Normalize risk: Lower risk is better. If risk score is 0-100 where 100 is high risk, 
        # we need to invert it for the weighted score (where higher is better).
        # Assuming risk_score is 0 (low) to 100 (high).
        risk_contribution = (100.0 - scores["contract_risk_score"]) * w_risk
        
        weighted_score = (
            (scores["strategic_alignment_score"] * w_strategic) +
            (scores["financial_viability_score"] * w_financial) +
            risk_contribution +
            (scores["internal_capacity_score"] * w_capacity) +
            (scores["data_integrity_score"] * w_data)
        )
        
        score_entry.strategic_alignment_score = scores["strategic_alignment_score"]
        score_entry.financial_viability_score = scores["financial_viability_score"]
        score_entry.contract_risk_score = scores["contract_risk_score"]
        score_entry.internal_capacity_score = scores["internal_capacity_score"]
        score_entry.data_integrity_score = scores["data_integrity_score"]
        
        score_entry.weighted_score = weighted_score
        
        if weighted_score >= 70.0:
            score_entry.go_no_go_decision = "GO"
        elif weighted_score >= 50.0:
            score_entry.go_no_go_decision = "REVIEW"
        else:
            score_entry.go_no_go_decision = "NO_GO"
            
        self.db.commit()
        
        return weighted_score
