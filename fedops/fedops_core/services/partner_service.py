from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fedops_core.db.models import Entity, EntityAward, ProposalRequirement
from fedops_core.db.team_models import OpportunityTeam, TeamMember
import logging

logger = logging.getLogger(__name__)

class PartnerService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def extract_entity_details(self, entity: Entity) -> Dict[str, Any]:
        """
        Extract comprehensive details from the entity's SAM.gov full_response.
        Updates the entity object with extracted data if fields are missing.
        """
        if not entity.full_response:
            return {}

        data = entity.full_response
        
        # Handle different response structures (wrapper vs direct)
        if "entityData" in data and isinstance(data["entityData"], list) and len(data["entityData"]) > 0:
            # Wrapper structure
            details = data["entityData"][0]
        elif "entityRegistration" in data:
            # Direct structure
            details = data
        else:
            # Unknown structure
            return {}

        extracted = {}
        
        # 1. Core Data & Revenue
        core_data = details.get("coreData", {})
        extracted["revenue"] = None # SAM often doesn't provide exact revenue, but we look for it
        
        # 2. Business Types & Capabilities
        assertions = details.get("assertions", {})
        goods_services = assertions.get("goodsAndServices", {})
        
        # NAICS
        naics_list = goods_services.get("naicsList", [])
        extracted["capabilities"] = [
            {
                "type": "NAICS",
                "code": n.get("naicsCode"),
                "description": n.get("naicsDescription")
            }
            for n in naics_list
        ]
        
        # PSC
        psc_list = goods_services.get("pscList", [])
        extracted["capabilities"].extend([
            {
                "type": "PSC",
                "code": p.get("pscCode"),
                "description": p.get("pscDescription")
            }
            for p in psc_list
        ])
        
        # Business Types
        biz_types = assertions.get("businessTypes", {}).get("businessTypeList", [])
        extracted["business_types"] = [
            {
                "code": b.get("businessTypeCode"),
                "description": b.get("businessTypeDescription")
            }
            for b in biz_types
        ]
        
        # 3. Locations
        extracted["locations"] = []
        phys_addr = core_data.get("physicalAddress", {})
        if phys_addr:
            extracted["locations"].append({
                "type": "Physical",
                "address": phys_addr
            })
        
        mail_addr = core_data.get("mailingAddress", {})
        if mail_addr:
            extracted["locations"].append({
                "type": "Mailing",
                "address": mail_addr
            })
            
        # 4. Web Addresses & Contacts
        points_of_contact = details.get("pointsOfContact", {})
        extracted["web_addresses"] = []
        # SAM doesn't always have a direct website field in standard sections, 
        # but sometimes it's in contact info or corporate URL if available.
        # We'll check points of contact for emails to infer domains or look for specific URL fields if they exist.
        
        # 5. Personnel
        # Not always available in public SAM data, but we can check assertions
        extracted["personnel_count"] = None
        
        return extracted

    async def update_entity_from_sam(self, entity: Entity):
        """Update entity fields from extracted SAM data"""
        details = await self.extract_entity_details(entity)
        
        if not details:
            return
            
        if details.get("revenue"):
            entity.revenue = details["revenue"]
            
        if details.get("capabilities"):
            entity.capabilities = details["capabilities"]
            
        if details.get("locations"):
            entity.locations = details["locations"]
            
        if details.get("web_addresses"):
            entity.web_addresses = details["web_addresses"]
            
        if details.get("personnel_count"):
            entity.personnel_count = details["personnel_count"]
            
        if details.get("business_types"):
            entity.business_types = details["business_types"]
            
        await self.db.commit()
        await self.db.refresh(entity)

    async def get_entity_profile(self, uei: str) -> Optional[Entity]:
        """Get comprehensive entity profile"""
        result = await self.db.execute(select(Entity).where(Entity.uei == uei))
        entity = result.scalars().first()
        
        if entity and (not entity.capabilities or not entity.business_types):
            # Try to extract if missing
            await self.update_entity_from_sam(entity)
            
        return entity

    async def analyze_capability_gaps(self, team_id: int, opportunity_id: int) -> Dict[str, Any]:
        """
        Compare team capabilities against opportunity requirements.
        Returns a gap analysis report.
        """
        # 1. Get Opportunity Requirements
        # Wait, ProposalRequirement links to Proposal, not Opportunity directly.
        # We need to find the proposal for this opportunity, or if we are in early stage, 
        # maybe we use extracted requirements from the opportunity directly (if stored elsewhere).
        # For now, let's assume we have a proposal or we fetch requirements associated with the opportunity.
        
        # Let's fetch the proposal first
        from fedops_core.db.models import Proposal
        prop_result = await self.db.execute(select(Proposal).where(Proposal.opportunity_id == opportunity_id))
        proposal = prop_result.scalars().first()
        
        requirements = []
        if proposal:
            req_result = await self.db.execute(
                select(ProposalRequirement).where(ProposalRequirement.proposal_id == proposal.id)
            )
            requirements = req_result.scalars().all()
        
        # 2. Get Team Capabilities
        team_result = await self.db.execute(
            select(TeamMember).where(TeamMember.team_id == team_id)
        )
        members = team_result.scalars().all()
        
        team_capabilities = []
        for member in members:
            # Fetch entity to get full capabilities
            entity = await self.get_entity_profile(member.entity_uei)
            if entity and entity.capabilities:
                for cap in entity.capabilities:
                    team_capabilities.append({
                        "source": member.entity_uei,
                        "role": member.role,
                        "capability": cap
                    })
        
        # 3. Match Requirements to Capabilities (Simple Keyword Matching for now)
        # In a real system, this would use embeddings/semantic search
        coverage = []
        uncovered = []
        
        for req in requirements:
            matches = []
            req_text = req.requirement_text.lower()
            
            for cap in team_capabilities:
                # Check NAICS or PSC description
                desc = cap["capability"].get("description", "").lower()
                code = cap["capability"].get("code", "")
                
                if desc and (desc in req_text or any(word in req_text for word in desc.split() if len(word) > 4)):
                    matches.append(cap)
                elif code and code in req_text:
                    matches.append(cap)
            
            if matches:
                coverage.append({
                    "requirement": req.requirement_text,
                    "matches": matches
                })
            else:
                uncovered.append(req.requirement_text)
                
        return {
            "total_requirements": len(requirements),
            "covered_count": len(coverage),
            "uncovered_count": len(uncovered),
            "coverage_percentage": (len(coverage) / len(requirements) * 100) if requirements else 0,
            "coverage_details": coverage,
            "gaps": uncovered
        }
