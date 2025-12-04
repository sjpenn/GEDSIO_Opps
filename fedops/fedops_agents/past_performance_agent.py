from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fedops_agents.base_agent import BaseAgent
from fedops_core.db.models import Opportunity, StoredFile
from fedops_core.services.ai_service import AIService
from fedops_core.services.entity_context_service import EntityContextService
from fedops_core.prompts import PAST_PERFORMANCE_PROMPT, determine_document_type, DocumentType

class PastPerformanceAgent(BaseAgent):
    def __init__(self, db: AsyncSession):
        super().__init__("PastPerformanceAgent", db)
        self.ai_service = AIService()

    async def execute(self, opportunity_id: int, **kwargs) -> Dict[str, Any]:
        await self.log_activity(opportunity_id, "START_PAST_PERFORMANCE_ANALYSIS", "IN_PROGRESS")
        
        try:
            # 1. Fetch Opportunity
            result = await self.db.execute(select(Opportunity).where(Opportunity.id == opportunity_id))
            opp = result.scalar_one_or_none()
            if not opp:
                raise ValueError(f"Opportunity {opportunity_id} not found")

            # 2. Fetch Entity Context
            entity_context_service = EntityContextService()
            combined_context = await entity_context_service.get_combined_context(self.db, opportunity_id)
            entity_context = combined_context["entity"]["formatted_context"]
            team_context = combined_context["team"]["formatted_context"]

            # 3. Get extracted data from kwargs
            extracted_data = kwargs.get('extracted_data') or {}
            section_l = extracted_data.get('section_l') or {}
            section_m = extracted_data.get('section_m') or {}
            
            # Build past performance details from extracted data
            pp_details = {
                "requirements": section_l.get("past_performance_requirements", []),  # EXTRACTED
                "relevance_criteria": section_m.get("past_performance_criteria", []),  # EXTRACTED
                "evaluation_factors": section_m.get("evaluation_factors", []),  # EXTRACTED
                "extracted_from": []
            }
            
            # Track which sections had data
            if section_l:
                pp_details["extracted_from"].append("Section L")
            if section_m:
                pp_details["extracted_from"].append("Section M")
            
            # Build context for AI analysis
            context_parts = []
            if section_l:
                context_parts.append(f"## Section L (Past Performance Requirements):\n{str(section_l)[:5000]}")
            if section_m:
                context_parts.append(f"## Section M (Evaluation Criteria):\n{str(section_m)[:5000]}")
            
            extracted_context = "\n\n".join(context_parts) if context_parts else "No past performance documents extracted."

            # 4. Generate AI Analysis for entity/team past performance and gap analysis
            prompt = PAST_PERFORMANCE_PROMPT.format(
                title=opp.title or "N/A",
                department=opp.department or "N/A",
                description=opp.description or "No description available",
                entity_context=entity_context,
                team_context=team_context
            )
            
            # Append extracted context
            prompt += f"\n\n## Extracted Past Performance Requirements:\n{extracted_context[:50000]}"
            prompt += "\n\n**Note**: Past performance requirements have been extracted above. Focus on analyzing the entity's and team's past performance against these requirements and identifying gaps."

            ai_analysis = await self.ai_service.analyze_opportunity(prompt)
            
            # Safely handle AI response with None checks
            if not ai_analysis or not isinstance(ai_analysis, dict):
                ai_analysis = {}
            
            # Combine extracted data with AI analysis
            combined_analysis = {
                **pp_details,  # Extracted facts
                "entity_past_performance": ai_analysis.get("entity_past_performance", "No analysis available"),  # AI-GENERATED
                "team_past_performance": ai_analysis.get("team_past_performance", "No analysis available"),  # AI-GENERATED
                "combined_strength": ai_analysis.get("combined_strength", "Unable to determine"),  # AI-GENERATED
                "gaps": ai_analysis.get("gaps", []),  # AI-GENERATED
                "recommendation": ai_analysis.get("recommendation", "Unable to provide recommendation"),  # AI-GENERATED
                "summary": ai_analysis.get("summary", "Analysis incomplete"),  # AI-GENERATED
                "ai_analysis": ai_analysis
            }
            
            # Add source document references
            source_docs = extracted_data.get('source_documents', []) if extracted_data else []
            if "source_documents" not in combined_analysis:
                combined_analysis["source_documents"] = source_docs
            
            await self.log_activity(opportunity_id, "END_PAST_PERFORMANCE_ANALYSIS", "SUCCESS", {
                "summary": combined_analysis.get("summary"),
                "requirements_found": len(combined_analysis.get("requirements", [])),
                "sections_used": pp_details.get("extracted_from", [])
            })
            
            return combined_analysis

        except Exception as e:
            await self.log_activity(opportunity_id, "PAST_PERFORMANCE_ERROR", "FAILURE", {"error": str(e)})
            # Return proper fallback structure matching the expected schema
            return {
                "summary": f"Past Performance analysis failed: {str(e)}",
                "requirements": [],
                "relevance_criteria": [],
                "evaluation_factors": [],
                "entity_past_performance": "Unable to analyze",
                "team_past_performance": "Unable to analyze",
                "combined_strength": "Unable to analyze",
                "gaps": ["Analysis failed - please check logs"],
                "recommendation": "Unable to provide recommendation due to error"
            }
