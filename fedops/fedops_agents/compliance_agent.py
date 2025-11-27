from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fedops_agents.base_agent import BaseAgent
from fedops_core.db.models import Opportunity
from fedops_core.services.ai_service import AIService
from fedops_core.prompts import RISK_ANALYSIS_PROMPT, SECURITY_ANALYSIS_PROMPT

class ComplianceAgent(BaseAgent):
    def __init__(self, db: AsyncSession):
        super().__init__("ComplianceAgent", db)

    async def execute(self, opportunity_id: int, **kwargs) -> Dict[str, Any]:
        await self.log_activity(opportunity_id, "START_COMPLIANCE_CHECK", "IN_PROGRESS")
        
        try:
            # Fetch opportunity data
            result = await self.db.execute(select(Opportunity).where(Opportunity.id == opportunity_id))
            opp = result.scalar_one_or_none()
            
            if not opp:
                raise ValueError(f"Opportunity {opportunity_id} not found")
            
            ai_service = AIService()
            
            # 1. Risk Analysis
            risk_prompt = RISK_ANALYSIS_PROMPT.format(
                title=opp.title or "N/A",
                department=opp.department or "N/A",
                naics_code=opp.naics_code or "N/A",
                set_aside=opp.type_of_set_aside or "None",
                description=opp.description or "No description available",
                place_of_performance=opp.place_of_performance or "Not specified"
            )
            
            risk_analysis = await ai_service.analyze_opportunity(risk_prompt)
            
            # 2. Security Analysis
            security_prompt = SECURITY_ANALYSIS_PROMPT.format(
                title=opp.title or "N/A",
                department=opp.department or "N/A",
                description=opp.description or "No description available",
                place_of_performance=opp.place_of_performance or "Not specified"
            )
            
            security_analysis = await ai_service.analyze_opportunity(security_prompt)
            
            # Extract risk score from AI analysis
            risk_score = risk_analysis.get("risk_score", 10.0)
            compliance_status = "COMPLIANT" if risk_score < 50 else "REVIEW_REQUIRED"
            
            # Update Opportunity model
            opp.compliance_status = compliance_status
            opp.risk_score = risk_score
            await self.db.commit()
            
            await self.log_activity(opportunity_id, "END_COMPLIANCE_CHECK", "SUCCESS", {
                "compliance_status": compliance_status,
                "risk_score": risk_score,
                "security_summary": security_analysis.get("summary", "")
            })
            
            return {
                "status": "success",
                "compliance_status": compliance_status,
                "risk_score": risk_score,
                "details": risk_analysis,  # Risk details
                "security_details": security_analysis # Security details
            }

        except Exception as e:
            await self.log_activity(opportunity_id, "COMPLIANCE_ERROR", "FAILURE", {"error": str(e)})
            # Return fallback values on error
            return {
                "status": "error",
                "compliance_status": "UNKNOWN",
                "risk_score": 50.0,
                "details": {"error": str(e), "summary": "AI analysis failed"},
                "security_details": {"error": str(e), "summary": "AI analysis failed"}
            }
