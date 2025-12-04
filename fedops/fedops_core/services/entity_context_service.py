"""
Entity Context Service
Extracts and formats entity and team data for AI analysis
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Dict, Any, List, Optional

from fedops_core.db.models import Entity, CompanyProfile
from fedops_core.db.team_models import OpportunityTeam, TeamMember


class EntityContextService:
    """Service to extract entity and team context for AI analysis"""
    
    @staticmethod
    async def get_primary_entity_context(db: AsyncSession) -> Dict[str, Any]:
        """
        Extract primary entity data from SAM.gov for AI analysis
        Returns formatted context including PSCs, capabilities, business types, awards
        """
        # Get primary entity
        result = await db.execute(
            select(Entity).where(Entity.is_primary == True)
        )
        entity = result.scalar_one_or_none()
        
        if not entity:
            return {
                "exists": False,
                "message": "No primary entity configured",
                "formatted_context": "No primary entity has been set up in the system."
            }
        
        # Extract data from SAM.gov response
        context = {
            "exists": True,
            "uei": entity.uei,
            "legal_name": entity.legal_business_name,
            "cage_code": entity.cage_code,
            "business_types": [],
            "certifications": [],
            "naics_codes": [],
            "psc_codes": [],
            "awards_summary": {},
            "formatted_context": ""
        }
        
        if entity.full_response and isinstance(entity.full_response, dict):
            sam_data = entity.full_response
            core_data = sam_data.get("coreData", {})
            
            # Extract business types
            business_types_data = core_data.get("businessTypes", {})
            business_type_list = business_types_data.get("businessTypeList", [])
            sba_business_type_list = business_types_data.get("sbaBusinessTypeList", [])
            
            for bt in business_type_list:
                code = bt.get("businessTypeCode")
                desc = bt.get("businessTypeDesc", "")
                if code:
                    context["business_types"].append({
                        "code": code,
                        "description": desc or code
                    })
            
            for sba in sba_business_type_list:
                cert_type = sba.get("certificationEntryTypeCode")
                cert_desc = sba.get("certificationEntryTypeDesc", "")
                if cert_type:
                    context["certifications"].append({
                        "code": cert_type,
                        "description": cert_desc or cert_type
                    })
            
            # Extract NAICS codes
            naics_data = core_data.get("naicsInformation", {})
            if isinstance(naics_data, dict):
                naics_list = naics_data.get("naicsList", [])
                for naics in naics_list:
                    code = naics.get("naicsCode")
                    desc = naics.get("naicsDescription", "")
                    if code:
                        context["naics_codes"].append({
                            "code": code,
                            "description": desc
                        })
            
            # Extract PSC codes (Product Service Codes)
            # PSCs can be in multiple locations in SAM.gov data
            psc_codes = set()
            
            # Location 1: entityRegistration.goodsAndServices
            entity_reg = sam_data.get("entityRegistration", {})
            goods_services = entity_reg.get("goodsAndServices", {})
            if isinstance(goods_services, dict):
                psc_list = goods_services.get("primaryPSC", [])
                if isinstance(psc_list, list):
                    for psc in psc_list:
                        if isinstance(psc, dict):
                            psc_code = psc.get("pscCode")
                            if psc_code:
                                psc_codes.add(psc_code)
            
            # Location 2: coreData.productServiceCodes
            psc_data = core_data.get("productServiceCodes", {})
            if isinstance(psc_data, dict):
                psc_list = psc_data.get("pscList", [])
                for psc in psc_list:
                    code = psc.get("pscCode")
                    if code:
                        psc_codes.add(code)
            
            # Location 3: assertions (sometimes PSCs are here)
            assertions = sam_data.get("assertions", {})
            if isinstance(assertions, dict):
                goods_services_assertions = assertions.get("goodsAndServices", {})
                if isinstance(goods_services_assertions, dict):
                    psc_list = goods_services_assertions.get("pscList", [])
                    for psc in psc_list:
                        code = psc.get("pscCode")
                        if code:
                            psc_codes.add(code)
            
            context["psc_codes"] = sorted(list(psc_codes))
            
            # Extract awards/past performance summary
            # Note: Full awards data would come from USASpending API
            # For now, we'll note if entity has awards data
            context["awards_summary"] = {
                "note": "Awards data available via USASpending API integration",
                "entity_registered_since": core_data.get("registrationDate", "Unknown")
            }
        
        # Format context for AI prompt
        context["formatted_context"] = EntityContextService._format_entity_context(context)
        
        return context
    
    @staticmethod
    async def get_team_context(db: AsyncSession, opportunity_id: int) -> Dict[str, Any]:
        """
        Extract team member data for an opportunity
        Returns formatted context including all team members and their capabilities
        """
        # Get team for this opportunity
        result = await db.execute(
            select(OpportunityTeam).where(OpportunityTeam.opportunity_id == opportunity_id)
        )
        team = result.scalar_one_or_none()
        
        if not team:
            return {
                "exists": False,
                "message": "No team configured for this opportunity",
                "formatted_context": "No team has been assembled for this opportunity yet."
            }
        
        # Get all team members
        members_result = await db.execute(
            select(TeamMember).where(TeamMember.team_id == team.id)
        )
        members = members_result.scalars().all()
        
        team_context = {
            "exists": True,
            "team_name": team.name,
            "team_description": team.description,
            "members": [],
            "formatted_context": ""
        }
        
        # Fetch entity data for each member
        for member in members:
            entity_result = await db.execute(
                select(Entity).where(Entity.uei == member.entity_uei)
            )
            entity = entity_result.scalar_one_or_none()
            
            member_data = {
                "uei": member.entity_uei,
                "role": member.role,
                "legal_name": entity.legal_business_name if entity else "Unknown",
                "capabilities": member.capabilities_contribution or {},
                "notes": member.notes,
                "business_types": [],
                "naics_codes": [],
                "psc_codes": []
            }
            
            # Extract SAM.gov data for this member
            if entity and entity.full_response and isinstance(entity.full_response, dict):
                sam_data = entity.full_response
                core_data = sam_data.get("coreData", {})
                
                # Business types
                business_types_data = core_data.get("businessTypes", {})
                business_type_list = business_types_data.get("businessTypeList", [])
                for bt in business_type_list:
                    code = bt.get("businessTypeCode")
                    desc = bt.get("businessTypeDesc", "")
                    if code:
                        member_data["business_types"].append(f"{desc or code} ({code})")
                
                # NAICS
                naics_data = core_data.get("naicsInformation", {})
                if isinstance(naics_data, dict):
                    naics_list = naics_data.get("naicsList", [])
                    for naics in naics_list[:5]:  # Limit to top 5
                        code = naics.get("naicsCode")
                        if code:
                            member_data["naics_codes"].append(code)
                
                # PSCs
                psc_data = core_data.get("productServiceCodes", {})
                if isinstance(psc_data, dict):
                    psc_list = psc_data.get("pscList", [])
                    for psc in psc_list[:5]:  # Limit to top 5
                        code = psc.get("pscCode")
                        if code:
                            member_data["psc_codes"].append(code)
            
            team_context["members"].append(member_data)
        
        # Format context for AI prompt
        team_context["formatted_context"] = EntityContextService._format_team_context(team_context)
        
        return team_context
    
    @staticmethod
    def _format_entity_context(context: Dict[str, Any]) -> str:
        """Format entity context for AI prompt injection"""
        if not context.get("exists"):
            return context.get("message", "No entity data available")
        
        formatted = f"**Primary Entity: {context['legal_name']}**\n\n"
        formatted += f"- **UEI:** {context['uei']}\n"
        formatted += f"- **CAGE Code:** {context.get('cage_code', 'N/A')}\n\n"
        
        if context["business_types"]:
            formatted += "**Business Types & Certifications:**\n"
            for bt in context["business_types"]:
                formatted += f"- {bt['description']} ({bt['code']})\n"
            formatted += "\n"
        
        if context["certifications"]:
            formatted += "**SBA Certifications:**\n"
            for cert in context["certifications"]:
                formatted += f"- {cert['description']} ({cert['code']})\n"
            formatted += "\n"
        
        if context["naics_codes"]:
            formatted += "**NAICS Codes:**\n"
            for naics in context["naics_codes"][:10]:  # Top 10
                formatted += f"- {naics['code']}: {naics['description']}\n"
            formatted += "\n"
        
        if context["psc_codes"]:
            formatted += "**Product/Service Codes (PSCs):**\n"
            psc_list = ", ".join(context["psc_codes"][:20])  # Top 20
            formatted += f"{psc_list}\n\n"
        
        return formatted
    
    @staticmethod
    def _format_team_context(context: Dict[str, Any]) -> str:
        """Format team context for AI prompt injection"""
        if not context.get("exists"):
            return context.get("message", "No team data available")
        
        formatted = f"**Team: {context['team_name']}**\n\n"
        if context.get("team_description"):
            formatted += f"{context['team_description']}\n\n"
        
        formatted += "**Team Members:**\n\n"
        
        for i, member in enumerate(context["members"], 1):
            formatted += f"{i}. **{member['legal_name']}** ({member['role']})\n"
            formatted += f"   - UEI: {member['uei']}\n"
            
            if member["business_types"]:
                formatted += f"   - Business Types: {', '.join(member['business_types'][:3])}\n"
            
            if member["naics_codes"]:
                formatted += f"   - NAICS Codes: {', '.join(member['naics_codes'])}\n"
            
            if member["psc_codes"]:
                formatted += f"   - PSC Codes: {', '.join(member['psc_codes'])}\n"
            
            if member["capabilities"]:
                formatted += f"   - Capabilities: {member['capabilities']}\n"
            
            if member["notes"]:
                formatted += f"   - Notes: {member['notes']}\n"
            
            formatted += "\n"
        
        return formatted
    
    @staticmethod
    async def get_combined_context(db: AsyncSession, opportunity_id: int) -> Dict[str, Any]:
        """
        Get both primary entity and team context in one call
        """
        entity_context = await EntityContextService.get_primary_entity_context(db)
        team_context = await EntityContextService.get_team_context(db, opportunity_id)
        
        return {
            "entity": entity_context,
            "team": team_context,
            "combined_formatted": f"{entity_context['formatted_context']}\n\n{team_context['formatted_context']}"
        }
