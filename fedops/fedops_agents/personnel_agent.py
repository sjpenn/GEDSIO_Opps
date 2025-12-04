from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fedops_agents.base_agent import BaseAgent
from fedops_core.db.models import Opportunity, StoredFile
from fedops_core.services.ai_service import AIService
from fedops_core.prompts import PERSONNEL_ANALYSIS_PROMPT, determine_document_type, DocumentType

class PersonnelAgent(BaseAgent):
    def __init__(self, db: AsyncSession):
        super().__init__("PersonnelAgent", db)
        self.ai_service = AIService()

    async def execute(self, opportunity_id: int, **kwargs) -> Dict[str, Any]:
        await self.log_activity(opportunity_id, "START_PERSONNEL_ANALYSIS", "IN_PROGRESS")
        
        try:
            # 1. Fetch Opportunity
            result = await self.db.execute(select(Opportunity).where(Opportunity.id == opportunity_id))
            opp = result.scalar_one_or_none()
            if not opp:
                raise ValueError(f"Opportunity {opportunity_id} not found")

            # 2. Get extracted data from kwargs
            extracted_data = kwargs.get('extracted_data') or {}
            
            # Extract personnel data from documents
            section_h = extracted_data.get('section_h') or {}
            sow = extracted_data.get('sow') or {}
            
            # Build personnel details from extracted data
            personnel_details = {
                "key_personnel": section_h.get("key_personnel", []),  # EXTRACTED
                "labor_categories": section_h.get("labor_categories", []),  # EXTRACTED
                "staffing_requirements": sow.get("staffing_requirements", []),  # EXTRACTED
                "fte_estimate": None,  # AI-GENERATED
                "summary": None,  # AI-GENERATED
                "extracted_from": []
            }
            
            # Track which sections had data
            if section_h:
                personnel_details["extracted_from"].append("Section H")
            if sow:
                personnel_details["extracted_from"].append("SOW")
            
            # Build context for AI analysis
            context_parts = []
            
            if section_h:
                context_parts.append(f"## Section H (Key Personnel):\n{str(section_h)[:5000]}")
            if sow:
                context_parts.append(f"## SOW (Staffing Requirements):\n{str(sow)[:5000]}")
            
            extracted_context = "\n\n".join(context_parts) if context_parts else "No personnel documents extracted."

            # 3. Generate AI Analysis for estimates and recommendations
            prompt = PERSONNEL_ANALYSIS_PROMPT.format(
                title=opp.title or "N/A",
                department=opp.department or "N/A",
                description=opp.description or "No description available"
            )
            
            # Append extracted context
            prompt += f"\n\n## Extracted Personnel Data:\n{extracted_context[:50000]}"
            prompt += "\n\n**Note**: Key personnel and labor categories have been extracted above. Focus on estimating FTEs and providing staffing recommendations based on this data."

            ai_analysis = await self.ai_service.analyze_opportunity(prompt)
            
            # Safely handle AI response with None checks
            if not ai_analysis or not isinstance(ai_analysis, dict):
                ai_analysis = {}
            
            # Combine extracted data with AI analysis
            combined_analysis = {
                **personnel_details,  # Extracted facts
                "summary": ai_analysis.get("summary", "Analysis incomplete"),  # AI-generated summary
                "fte_estimate": ai_analysis.get("fte_estimate", 0),  # AI-generated estimate
                "ai_analysis": ai_analysis  # Full AI analysis
            }
            
            # Merge any additional AI-extracted personnel (if extraction missed some)
            if ai_analysis.get("key_personnel"):
                for person in ai_analysis["key_personnel"]:
                    if person not in combined_analysis["key_personnel"]:
                        combined_analysis["key_personnel"].append(person)
            
            if ai_analysis.get("labor_categories"):
                for lcat in ai_analysis["labor_categories"]:
                    if lcat not in combined_analysis["labor_categories"]:
                        combined_analysis["labor_categories"].append(lcat)
            
            # Add source document references
            source_docs = extracted_data.get('source_documents', []) if extracted_data else []
            if "source_documents" not in combined_analysis:
                combined_analysis["source_documents"] = source_docs
            
            await self.log_activity(opportunity_id, "END_PERSONNEL_ANALYSIS", "SUCCESS", {
                "summary": combined_analysis.get("summary"),
                "lcats_found": len(combined_analysis.get("labor_categories", [])),
                "key_personnel_found": len(combined_analysis.get("key_personnel", [])),
                "sections_used": personnel_details.get("extracted_from", [])
            })
            
            return combined_analysis

        except Exception as e:
            await self.log_activity(opportunity_id, "PERSONNEL_ERROR", "FAILURE", {"error": str(e)})
            # Return proper fallback structure matching the expected schema
            return {
                "summary": f"Personnel analysis failed: {str(e)}",
                "key_personnel": [],
                "labor_categories": [],
                "staffing_requirements": [],
                "fte_estimate": 0,
                "extracted_from": []
            }
