from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fedops_agents.base_agent import BaseAgent
from fedops_core.db.models import Opportunity, CompanyProfile

class CapabilityMappingAgent(BaseAgent):
    def __init__(self, db: AsyncSession):
        super().__init__("CapabilityMappingAgent", db)

    async def execute(self, opportunity_id: int, **kwargs) -> Dict[str, Any]:
        await self.log_activity(opportunity_id, "START_CAPABILITY_MAPPING", "IN_PROGRESS")
        
        try:
            result = await self.db.execute(select(Opportunity).where(Opportunity.id == opportunity_id))
            opp = result.scalar_one_or_none()
            
            result = await self.db.execute(select(CompanyProfile))
            company = result.scalars().first()
            
            if not opp or not company:
                raise ValueError("Opportunity or Company Profile not found")

            score = 0.0
            matches = []

            # 1. NAICS Match
            if opp.naics_code and company.target_naics:
                if opp.naics_code in company.target_naics:
                    score += 50.0
                    matches.append(f"NAICS Match: {opp.naics_code}")

            # 2. Keyword Match (Simple containment)
            # In real world, use vector search/embeddings
            if opp.description and company.target_keywords:
                desc_lower = opp.description.lower()
                for kw in company.target_keywords:
                    if kw.lower() in desc_lower:
                        score += 10.0
                        matches.append(f"Keyword Match: {kw}")
            
            # Cap score at 100
            final_score = min(score, 100.0)
            
            await self.log_activity(opportunity_id, "END_CAPABILITY_MAPPING", "SUCCESS", {
                "score": final_score,
                "matches": matches
            })
            return {"status": "success", "internal_capacity_score": final_score, "matches": matches}

        except Exception as e:
            await self.log_activity(opportunity_id, "CAPABILITY_ERROR", "FAILURE", {"error": str(e)})
            raise e
