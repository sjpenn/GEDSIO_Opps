from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fedops_agents.base_agent import BaseAgent
from fedops_core.db.models import Opportunity
from fedops_core.services.ai_service import AIService
from fedops_core.prompts import SOLICITATION_SUMMARY_PROMPT

class DocumentAnalysisAgent(BaseAgent):
    def __init__(self, db: AsyncSession):
        super().__init__("DocumentAnalysisAgent", db)

    async def execute(self, opportunity_id: int, **kwargs) -> Dict[str, Any]:
        await self.log_activity(opportunity_id, "START_DOC_ANALYSIS", "IN_PROGRESS")
        
        try:
            # Fetch opportunity data
            result = await self.db.execute(select(Opportunity).where(Opportunity.id == opportunity_id))
            opp = result.scalar_one_or_none()
            
            if not opp:
                raise ValueError(f"Opportunity {opportunity_id} not found")
            
            # Call AI service for solicitation summary
            ai_service = AIService()
            prompt = SOLICITATION_SUMMARY_PROMPT.format(
                title=opp.title or "N/A",
                department=opp.department or "N/A",
                naics_code=opp.naics_code or "N/A",
                set_aside=opp.type_of_set_aside or "None",
                description=opp.description or "No description available",
                response_deadline=str(opp.response_deadline) if opp.response_deadline else "Not specified"
            )
            
            analysis = await ai_service.analyze_opportunity(prompt)
            
            # Extract key information
            requirements_count = len(analysis.get("key_dates", [])) + len(analysis.get("key_personnel", []))
            
            await self.log_activity(opportunity_id, "END_DOC_ANALYSIS", "SUCCESS", {
                "requirements_count": requirements_count,
                "summary_length": len(analysis.get("summary", ""))
            })
            
            return {
                "status": "success",
                "solicitation_details": analysis,
                "requirements_count": requirements_count
            }

        except Exception as e:
            await self.log_activity(opportunity_id, "DOC_ANALYSIS_ERROR", "FAILURE", {"error": str(e)})
            # Return fallback structure
            return {
                "status": "error",
                "solicitation_details": {
                    "summary": "Analysis failed", 
                    "key_dates": [], 
                    "key_personnel": [],
                    "error": str(e)
                }
            }
