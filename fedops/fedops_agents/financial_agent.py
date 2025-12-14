from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fedops_agents.base_agent import BaseAgent
from fedops_core.db.models import Opportunity, StoredFile
from fedops_core.services.ai_service import AIService
from fedops_core.prompts import FINANCIAL_ANALYSIS_PROMPT, determine_document_type, DocumentType

class FinancialAnalysisAgent(BaseAgent):
    def __init__(self, db: AsyncSession):
        super().__init__("FinancialAnalysisAgent", db)

    async def execute(self, opportunity_id: int, **kwargs) -> Dict[str, Any]:
        await self.log_activity(opportunity_id, "START_FINANCIAL_ANALYSIS", "IN_PROGRESS")
        
        try:
            # Fetch opportunity data
            result = await self.db.execute(select(Opportunity).where(Opportunity.id == opportunity_id))
            opp = result.scalar_one_or_none()
            
            if not opp:
                raise ValueError(f"Opportunity {opportunity_id} not found")
            
            # Get extracted data from kwargs
            extracted_data = kwargs.get('extracted_data') or {}
            section_b = extracted_data.get('section_b') or {}
            
            sow = extracted_data.get('sow') or {}
            section_l = extracted_data.get('section_l') or {}

            # Build financial details from extracted data
            financial_details = {
                "contract_value": section_b.get("total_value"),  # EXTRACTED
                "clins": section_b.get("clins", []),  # EXTRACTED
                "pricing_structure": section_b.get("pricing_structure"),  # EXTRACTED
                "extracted_from": ["Section B"] if section_b else []
            }
            
            # Build context for AI analysis
            context = f"## Section B (Pricing):\n{str(section_b)[:20000]}\n" if section_b else "No pricing data extracted.\n"
            context += f"## Section L (Instructions):\n{str(section_l)[:10000]}\n" if section_l else ""
            context += f"## SOW (Scope):\n{str(sow)[:20000]}\n" if sow else ""
            
            # --- Price to Win (PTW) Context Gathering ---
            
            # 1. Incumbent Data (from current opportunity)
            incumbent_context = ""
            if opp.incumbent_vendor:
                 incumbent_context += f"**Incumbent:** {opp.incumbent_vendor}\n"
                 if opp.incumbent_contract_number:
                     incumbent_context += f"**Contract #:** {opp.incumbent_contract_number}\n"
                 if opp.incumbent_value:
                     incumbent_context += f"**Previous Value:** {opp.incumbent_value}\n"
                 if opp.incumbent_expiration_date:
                     incumbent_context += f"**Expires:** {opp.incumbent_expiration_date}\n"
            else:
                incumbent_context += "No specific incumbent identified in opportunity data.\n"

            # 2. Similar Awards (Same Agency + NAICS)
            similar_awards_context = "\n**Similar Recent Awards:**\n"
            try:
                # Query for awarded opportunities with same NAICS and Department, excluding current one
                stmt = select(Opportunity).where(
                    Opportunity.department == opp.department,
                    Opportunity.naics_code == opp.naics_code,
                    Opportunity.id != opportunity_id,
                    Opportunity.award.isnot(None) # Check if award data exists (JSONB not null)
                ).limit(5)
                
                similar_res = await self.db.execute(stmt)
                similar_opps = similar_res.scalars().all()
                
                if similar_opps:
                    for sim in similar_opps:
                        # Extract award details safely from JSONB
                        award_data = sim.award if isinstance(sim.award, dict) else {}
                        amount = award_data.get('amount') or "Unknown"
                        awardee = award_data.get('awardee') or "Unknown"
                        date = award_data.get('date') or "Unknown"
                        
                        similar_awards_context += f"- **{sim.title}**: Awarded to {awardee} for {amount} on {date}\n"
                else:
                    similar_awards_context += "No direct similar awards found in local database.\n"
                    
            except Exception as ex:
                similar_awards_context += f"Error fetching similar awards: {str(ex)}\n"

            full_incumbent_context = incumbent_context + "\n" + similar_awards_context
            # ---------------------------------------------
            
            # --- Shared Context for Unified Analysis ---
            personnel_context = kwargs.get('personnel_context', {})
            security_context = kwargs.get('security_context', {})
            
            # Format Personnel Data for Pricing
            fte_data = ""
            if personnel_context.get('labor_categories'):
                fte_data += "**Identified Labor Categories:**\n"
                for lcat in personnel_context['labor_categories']:
                    fte_data += f"- {lcat}\n"
            
            if personnel_context.get('fte_estimate'):
                fte_data += f"**Total FTE Estimate:** {personnel_context['fte_estimate']}\n"
                
            if personnel_context.get('key_personnel'):
                fte_data += "**Key Personnel Requirements:**\n"
                for person in personnel_context['key_personnel']:
                    fte_data += f"- {person}\n"
            
            # Append Shared Context to Prompt Inputs
            pricing_context_input = context[:40000] # Pricing/SOW data
            
            if fte_data:
                pricing_context_input += f"\n\n## Validated Personnel Requirements (Use as Ground Truth):\n{fte_data}"
                
            if security_context.get('personnel_clearance'):
                pricing_context_input += f"\n**Security Clearance Impact:** Rates must account for {security_context['personnel_clearance']} clearance premiums."

            # Call AI service for financial analysis
            ai_service = AIService()
            prompt = FINANCIAL_ANALYSIS_PROMPT.format(
                title=opp.title or "N/A",
                department=opp.department or "N/A",
                naics_code=opp.naics_code or "N/A",
                set_aside=opp.type_of_set_aside or "None",
                description=opp.description or "No description available",
                incumbent_context=full_incumbent_context,
                financial_data_context=pricing_context_input
            )
            
            ai_analysis = await ai_service.analyze_opportunity(prompt)
            
            # Safely handle AI response with None checks
            if not ai_analysis or not isinstance(ai_analysis, dict):
                ai_analysis = {}
            
            # Combine extracted data with AI analysis
            combined_analysis = {
                **financial_details,  # Extracted facts
                **ai_analysis,  # AI-generated analysis
                "ai_analysis": ai_analysis
            }
            
            # Extract score from AI analysis
            score = ai_analysis.get("score", 50.0)
            
            source_docs = extracted_data.get('source_documents', []) if extracted_data else []
            
            await self.log_activity(opportunity_id, "END_FINANCIAL_ANALYSIS", "SUCCESS", {
                "score": score,
                "summary": ai_analysis.get("summary", ""),
                "sections_used": financial_details.get("extracted_from", [])
            })
            
            return {
                "status": "success",
                "financial_viability_score": score,
                "details": { "financial": combined_analysis },  # Nested for frontend compatibility
                "source_documents": source_docs
            }

        except Exception as e:
            await self.log_activity(opportunity_id, "FINANCIAL_ERROR", "FAILURE", {"error": str(e)})
            # Return fallback score on error
            return {
                "status": "error",
                "financial_viability_score": 50.0,
                "details": {
                    "summary": f"Financial analysis failed: {str(e)}",
                    "score": 50.0,
                    "estimated_value_range": {"low": 0, "high": 0, "confidence": "Low"},
                    "margin_potential": "Unknown",
                    "insights": [],
                    "risks": [],
                    "opportunities": [],
                    "recommendation": "Unable to provide recommendation due to error"
                }
            }
