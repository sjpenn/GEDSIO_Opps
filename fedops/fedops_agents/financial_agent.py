from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fedops_agents.base_agent import BaseAgent
from fedops_core.db.models import Opportunity
from fedops_core.services.ai_service import AIService
from fedops_core.prompts import FINANCIAL_ANALYSIS_PROMPT

class FinancialAnalysisAgent(BaseAgent):
    def __init__(self, db: AsyncSession):
        super().__init__("FinancialAnalysisAgent", db)

    async def execute(self, opportunity_id: int, **kwargs) -> Dict[str, Any]:
        await self.log_activity(opportunity_id, "START_FINANCIAL_ANALYSIS", "IN_PROGRESS")
        
        try:
            # Fetch opportunity data
            result = await self.db.execute(select(Opportunity).where(Opportunity.id == opportunity_id))
            opp = result.scalar_one_or_none()
            
            if not opp:
                raise ValueError(f"Opportunity {opportunity_id} not found")
            
            # Call AI service for financial analysis
            ai_service = AIService()
            prompt = FINANCIAL_ANALYSIS_PROMPT.format(
                title=opp.title or "N/A",
                department=opp.department or "N/A",
                naics_code=opp.naics_code or "N/A",
                set_aside=opp.type_of_set_aside or "None",
                description=opp.description or "No description available"
            )
            
            analysis = await ai_service.analyze_opportunity(prompt)
            
            # Extract score from AI analysis
            score = analysis.get("score", 50.0)
            
            await self.log_activity(opportunity_id, "END_FINANCIAL_ANALYSIS", "SUCCESS", {
                "score": score,
                "summary": analysis.get("summary", "")
            })
            
            return {
                "status": "success",
                "financial_viability_score": score,
                "details": analysis  # Full AI response for storage
            }

        except Exception as e:
            await self.log_activity(opportunity_id, "FINANCIAL_ERROR", "FAILURE", {"error": str(e)})
            # Return fallback score on error
            return {
                "status": "error",
                "financial_viability_score": 50.0,
                "details": {"error": str(e), "summary": "AI analysis failed"}
            }
