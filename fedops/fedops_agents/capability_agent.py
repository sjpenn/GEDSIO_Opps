from typing import Dict, Any
from sqlalchemy.orm import Session
from fedops_agents.base_agent import BaseAgent
from fedops_core.db.models import Opportunity, CompanyProfile

class CapabilityMappingAgent(BaseAgent):
    def __init__(self, db: Session):
        super().__init__("CapabilityMappingAgent", db)

    def execute(self, opportunity_id: int, **kwargs) -> Dict[str, Any]:
        self.log_activity(opportunity_id, "START_CAPABILITY_MAPPING", "IN_PROGRESS")
        
        try:
            opp = self.db.query(Opportunity).filter(Opportunity.id == opportunity_id).first()
            # Assuming single company profile for now, or pick primary
            company = self.db.query(CompanyProfile).first()
            
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
            
            self.log_activity(opportunity_id, "END_CAPABILITY_MAPPING", "SUCCESS", {
                "score": final_score,
                "matches": matches
            })
            return {"status": "success", "internal_capacity_score": final_score, "matches": matches}

        except Exception as e:
            self.log_activity(opportunity_id, "CAPABILITY_ERROR", "FAILURE", {"error": str(e)})
            raise e
