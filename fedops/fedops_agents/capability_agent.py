from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fedops_agents.base_agent import BaseAgent
from fedops_core.db.models import Opportunity, CompanyProfile
from fedops_core.services.ai_service import AIService
from fedops_core.prompts import STRATEGIC_ANALYSIS_PROMPT, CAPACITY_ANALYSIS_PROMPT, PERSONNEL_ANALYSIS_PROMPT

class CapabilityMappingAgent(BaseAgent):
    def __init__(self, db: AsyncSession):
        super().__init__("CapabilityMappingAgent", db)

    async def execute(self, opportunity_id: int, **kwargs) -> Dict[str, Any]:
        await self.log_activity(opportunity_id, "START_CAPABILITY_MAPPING", "IN_PROGRESS")
        
        try:
            # Fetch opportunity data
            result = await self.db.execute(select(Opportunity).where(Opportunity.id == opportunity_id))
            opp = result.scalar_one_or_none()
            
            if not opp:
                raise ValueError(f"Opportunity {opportunity_id} not found")
            
            # Fetch company profile (assuming single profile for now)
            result = await self.db.execute(select(CompanyProfile).limit(1))
            company = result.scalar_one_or_none()
            
            # Prepare company data
            company_naics = ", ".join(company.target_naics) if company and company.target_naics else "None"
            company_keywords = ", ".join(company.target_keywords) if company and company.target_keywords else "None"
            
            # Construct capabilities string from keywords since 'capabilities' field doesn't exist
            company_capabilities = f"Specialized in: {company_keywords}" if company_keywords != "None" else "General federal contracting"

            # Call AI service for strategic, capacity, and personnel analysis
            ai_service = AIService()
            
            # 1. Strategic Analysis
            strategic_prompt = STRATEGIC_ANALYSIS_PROMPT.format(
                title=opp.title or "N/A",
                department=opp.department or "N/A",
                naics_code=opp.naics_code or "N/A",
                set_aside=opp.type_of_set_aside or "None",
                description=opp.description or "No description available",
                company_capabilities=company_capabilities,
                company_naics=company_naics,
                company_keywords=company_keywords
            )
            strategic_analysis = await ai_service.analyze_opportunity(strategic_prompt)
            
            # 2. Capacity Analysis
            capacity_prompt = CAPACITY_ANALYSIS_PROMPT.format(
                title=opp.title or "N/A",
                department=opp.department or "N/A",
                naics_code=opp.naics_code or "N/A",
                description=opp.description or "No description available",
                company_naics=company_naics,
                company_keywords=company_keywords,
                company_capabilities=company_capabilities
            )
            capacity_analysis = await ai_service.analyze_opportunity(capacity_prompt)
            
            # 3. Personnel Analysis
            personnel_prompt = PERSONNEL_ANALYSIS_PROMPT.format(
                title=opp.title or "N/A",
                department=opp.department or "N/A",
                description=opp.description or "No description available"
            )
            personnel_analysis = await ai_service.analyze_opportunity(personnel_prompt)
            
            # 4. Past Performance Analysis
            from fedops_core.prompts import PAST_PERFORMANCE_PROMPT
            past_perf_prompt = PAST_PERFORMANCE_PROMPT.format(
                title=opp.title or "N/A",
                department=opp.department or "N/A",
                description=opp.description or "No description available"
            )
            past_perf_analysis = await ai_service.analyze_opportunity(past_perf_prompt)
            
            # Extract scores
            strategic_score = strategic_analysis.get("score", 50.0)
            capacity_score = capacity_analysis.get("score", 50.0)
            
            await self.log_activity(opportunity_id, "END_CAPABILITY_MAPPING", "SUCCESS", {
                "strategic_score": strategic_score,
                "capacity_score": capacity_score,
                "personnel_summary": personnel_analysis.get("summary", ""),
                "past_perf_summary": past_perf_analysis.get("summary", "")
            })
            
            return {
                "status": "success",
                "strategic_alignment_score": strategic_score,
                "internal_capacity_score": capacity_score,
                "strategic_details": strategic_analysis,
                "capacity_details": capacity_analysis,
                "personnel_details": personnel_analysis,
                "past_performance_details": past_perf_analysis
            }

        except Exception as e:
            await self.log_activity(opportunity_id, "CAPABILITY_ERROR", "FAILURE", {"error": str(e)})
            # Return fallback scores on error
            return {
                "status": "error",
                "strategic_alignment_score": 50.0,
                "internal_capacity_score": 50.0,
                "strategic_details": {"error": str(e), "summary": "AI analysis failed"},
                "capacity_details": {"error": str(e), "summary": "AI analysis failed"},
                "matches": []
            }
