from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fedops_agents.base_agent import BaseAgent
from fedops_core.db.models import Opportunity, OpportunityScore

from fedops_agents.ingestion_agent import IngestionAgent
from fedops_agents.document_analysis_agent import DocumentAnalysisAgent
from fedops_agents.compliance_agent import ComplianceAgent
from fedops_agents.capability_agent import CapabilityMappingAgent
from fedops_agents.financial_agent import FinancialAnalysisAgent
from fedops_core.services.ai_service import AIService
from fedops_core.prompts import EXECUTIVE_OVERVIEW_PROMPT

class OrchestratorAgent(BaseAgent):
    def __init__(self, db: AsyncSession):
        super().__init__("OrchestratorAgent", db)

    async def execute(self, opportunity_id: int, **kwargs) -> Dict[str, Any]:
        await self.log_activity(opportunity_id, "START_WORKFLOW", "IN_PROGRESS", {"step": "init"})
        
        try:
            # 1. Ingestion (Placeholder)
            # ingestion_agent = IngestionAgent(self.db)
            # await ingestion_agent.execute(opportunity_id)

            # 2. Document Analysis (Sequential)
            doc_agent = DocumentAnalysisAgent(self.db)
            doc_results = await doc_agent.execute(opportunity_id)

            # 3. Concurrent Analysis
            await self.log_activity(opportunity_id, "CONCURRENT_ANALYSIS", "IN_PROGRESS")
            
            # Compliance & Security
            comp_agent = ComplianceAgent(self.db)
            comp_results = await comp_agent.execute(opportunity_id)
            
            # Capability
            cap_agent = CapabilityMappingAgent(self.db)
            cap_results = await cap_agent.execute(opportunity_id)
            
            # Financial
            fin_agent = FinancialAnalysisAgent(self.db)
            fin_results = await fin_agent.execute(opportunity_id)

            # 4. Executive Overview Generation
            result = await self.db.execute(select(Opportunity).where(Opportunity.id == opportunity_id))
            opp = result.scalar_one_or_none()
            
            ai_service = AIService()
            overview_prompt = EXECUTIVE_OVERVIEW_PROMPT.format(
                title=opp.title or "N/A",
                department=opp.department or "N/A",
                description=opp.description or "No description available",
                financial_score=fin_results.get("financial_viability_score", 0.0),
                strategic_score=cap_results.get("strategic_alignment_score", 0.0),
                risk_score=comp_results.get("risk_score", 0.0),
                capacity_score=cap_results.get("internal_capacity_score", 0.0)
            )
            
            executive_overview = await ai_service.analyze_opportunity(overview_prompt)

            # 5. Score Calculation & Data Aggregation
            score_data = {
                "contract_risk_score": comp_results.get("risk_score", 0.0),
                "internal_capacity_score": cap_results.get("internal_capacity_score", 0.0),
                "financial_viability_score": fin_results.get("financial_viability_score", 0.0),
                "strategic_alignment_score": cap_results.get("strategic_alignment_score", 50.0),
                "data_integrity_score": 100.0,  # Placeholder
                # AI-generated details
                "financial_details": fin_results.get("details"),
                "strategic_details": cap_results.get("strategic_details"),
                "risk_details": comp_results.get("details"),
                "capacity_details": cap_results.get("capacity_details"),
                "capacity_details": cap_results.get("capacity_details"),
                "personnel_details": cap_results.get("personnel_details"),
                "past_performance_details": cap_results.get("past_performance_details"),
                # New Analysis Details
                "solicitation_details": doc_results.get("solicitation_details"),
                "security_details": comp_results.get("security_details"),
                "executive_overview": executive_overview
            }
            
            final_score = await self.calculate_score(opportunity_id, score_data)
            
            await self.log_activity(opportunity_id, "END_WORKFLOW", "SUCCESS", {"final_score": final_score})
            return {"status": "success", "score": final_score}

        except Exception as e:
            await self.log_activity(opportunity_id, "WORKFLOW_ERROR", "FAILURE", {"error": str(e)})
            raise e

    async def calculate_score(self, opportunity_id: int, scores: Dict[str, float]) -> float:
        result = await self.db.execute(select(OpportunityScore).where(OpportunityScore.opportunity_id == opportunity_id))
        score_entry = result.scalar_one_or_none()
        
        if not score_entry:
            score_entry = OpportunityScore(opportunity_id=opportunity_id)
            self.db.add(score_entry)
        
        # Weights
        w_strategic = 0.30
        w_financial = 0.25
        w_risk = 0.20
        w_capacity = 0.15
        w_data = 0.10
        
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
        
        # Store AI-generated details
        from datetime import datetime
        score_entry.details = {
            "financial": scores.get("financial_details"),
            "strategic": scores.get("strategic_details"),
            "risk": scores.get("risk_details"),
            "capacity": scores.get("capacity_details"),
            "personnel": scores.get("personnel_details"),
            "past_performance": scores.get("past_performance_details"),
            "solicitation": scores.get("solicitation_details"),
            "security": scores.get("security_details"),
            "executive_overview": scores.get("executive_overview"),
            "generated_at": datetime.utcnow().isoformat()
        }
            
        await self.db.commit()
        
        return weighted_score
