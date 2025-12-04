from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fedops_agents.base_agent import BaseAgent
from fedops_agents.past_performance_agent import PastPerformanceAgent
from fedops_agents.personnel_agent import PersonnelAgent
from fedops_core.db.models import Opportunity, CompanyProfile, StoredFile
from fedops_core.services.ai_service import AIService
from fedops_core.services.entity_context_service import EntityContextService
from fedops_core.prompts import STRATEGIC_ANALYSIS_PROMPT, CAPACITY_ANALYSIS_PROMPT, determine_document_type, DocumentType


class CapabilityMappingAgent(BaseAgent):
    def __init__(self, db: AsyncSession):
        super().__init__("CapabilityMappingAgent", db)
        self.ai_service = AIService()

    async def execute(self, opportunity_id: int, **kwargs) -> Dict[str, Any]:
        await self.log_activity(opportunity_id, "START_CAPABILITY_MAPPING", "IN_PROGRESS")
        
        try:
            # Fetch opportunity data
            result = await self.db.execute(select(Opportunity).where(Opportunity.id == opportunity_id))
            opp = result.scalar_one_or_none()
            
            if not opp:
                raise ValueError(f"Opportunity {opportunity_id} not found")
            
            # Fetch company profile
            result = await self.db.execute(select(CompanyProfile).limit(1))
            company = result.scalar_one_or_none()
            
            # Prepare company data
            company_naics = ", ".join(company.target_naics) if company and company.target_naics else "None"
            company_keywords = ", ".join(company.target_keywords) if company and company.target_keywords else "None"
            company_capabilities = f"Specialized in: {company_keywords}" if company_keywords != "None" else "General federal contracting"

            # Fetch entity and team context
            entity_context_service = EntityContextService()
            combined_context = await entity_context_service.get_combined_context(self.db, opportunity_id)
            
            entity_context = combined_context["entity"]["formatted_context"]
            team_context = combined_context["team"]["formatted_context"]

            # Get extracted data from kwargs
            extracted_data = kwargs.get('extracted_data') or {}
            sow = extracted_data.get('sow') or {}
            section_m = extracted_data.get('section_m') or {}
            
            # Build context from extracted data
            context_parts = []
            if sow:
                context_parts.append(f"## SOW (Required Capabilities):\n{str(sow)[:5000]}")
            if section_m:
                context_parts.append(f"## Section M (Evaluation Criteria):\n{str(section_m)[:5000]}")
            
            extracted_context = "\n\n".join(context_parts) if context_parts else "No capability documents extracted."
            source_docs = extracted_data.get('source_documents', []) if extracted_data else []

            # 1. Strategic Analysis with extracted data
            strategic_prompt = STRATEGIC_ANALYSIS_PROMPT.format(
                title=opp.title or "N/A",
                department=opp.department or "N/A",
                naics_code=opp.naics_code or "N/A",
                set_aside=opp.type_of_set_aside or "None",
                description=opp.description or "No description available",
                company_capabilities=company_capabilities,
                company_naics=company_naics,
                company_keywords=company_keywords,
                entity_context=entity_context,
                team_context=team_context
            )
            strategic_prompt += f"\n\n## Extracted Capability Data:\n{extracted_context[:50000]}"
            strategic_analysis = await self.ai_service.analyze_opportunity(strategic_prompt)
            
            # 2. Capacity Analysis with extracted data
            capacity_prompt = CAPACITY_ANALYSIS_PROMPT.format(
                title=opp.title or "N/A",
                department=opp.department or "N/A",
                naics_code=opp.naics_code or "N/A",
                description=opp.description or "No description available",
                company_naics=company_naics,
                company_keywords=company_keywords,
                company_capabilities=company_capabilities,
                entity_context=entity_context,
                team_context=team_context
            )
            capacity_prompt += f"\n\n## Extracted Capability Data:\n{extracted_context[:50000]}"
            capacity_analysis = await self.ai_service.analyze_opportunity(capacity_prompt)
            
            # 3. Personnel Analysis (Delegate to Agent with extracted_data)
            personnel_agent = PersonnelAgent(self.db)
            personnel_analysis = await personnel_agent.execute(opportunity_id, extracted_data=extracted_data)
            
            # Safely handle personnel analysis response
            if not personnel_analysis or not isinstance(personnel_analysis, dict):
                personnel_analysis = {
                    "summary": "Personnel analysis failed",
                    "key_personnel": [],
                    "labor_categories": [],
                    "staffing_requirements": [],
                    "fte_estimate": 0
                }
            
            # 4. Past Performance Analysis (Delegate to Agent with extracted_data)
            past_perf_agent = PastPerformanceAgent(self.db)
            past_perf_analysis = await past_perf_agent.execute(opportunity_id, extracted_data=extracted_data)
            
            # Safely handle past performance analysis response
            if not past_perf_analysis or not isinstance(past_perf_analysis, dict):
                past_perf_analysis = {
                    "summary": "Past performance analysis failed",
                    "requirements": [],
                    "gaps": [],
                    "recommendation": "Unable to provide recommendation"
                }
            
            # Safely handle strategic and capacity analysis responses
            if not strategic_analysis or not isinstance(strategic_analysis, dict):
                strategic_analysis = {"summary": "Strategic analysis failed", "score": 50.0}
            if not capacity_analysis or not isinstance(capacity_analysis, dict):
                capacity_analysis = {"summary": "Capacity analysis failed", "score": 50.0}
            
            # Extract scores
            strategic_score = strategic_analysis.get("score", 50.0)
            capacity_score = capacity_analysis.get("score", 50.0)
            
            # Add source document references to all analyses
            if "source_documents" not in strategic_analysis:
                strategic_analysis["source_documents"] = source_docs
            if "source_documents" not in capacity_analysis:
                capacity_analysis["source_documents"] = source_docs
            
            await self.log_activity(opportunity_id, "END_CAPABILITY_MAPPING", "SUCCESS", {
                "strategic_score": strategic_score,
                "capacity_score": capacity_score,
                "personnel_summary": personnel_analysis.get("summary", ""),
                "past_perf_summary": past_perf_analysis.get("summary", ""),
                "entity_exists": combined_context["entity"]["exists"],
                "team_exists": combined_context["team"]["exists"],
                "source_docs": len(source_docs)
            })
            
            return {
                "status": "success",
                "strategic_alignment_score": strategic_score,
                "internal_capacity_score": capacity_score,
                "strategic_details": strategic_analysis,
                "capacity_details": capacity_analysis,
                "personnel_details": personnel_analysis,
                "past_performance_details": past_perf_analysis,
                "entity_context": combined_context["entity"],
                "team_context": combined_context["team"],
                "source_documents": source_docs
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
