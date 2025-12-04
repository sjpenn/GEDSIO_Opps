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
            
            # Build financial details from extracted data
            financial_details = {
                "contract_value": section_b.get("total_value"),  # EXTRACTED
                "clins": section_b.get("clins", []),  # EXTRACTED
                "pricing_structure": section_b.get("pricing_structure"),  # EXTRACTED
                "extracted_from": ["Section B"] if section_b else []
            }
            
            # Build context for AI analysis
            context = f"## Section B (Pricing):\n{str(section_b)[:5000]}" if section_b else "No pricing data extracted."
            
            # Call AI service for financial analysis
            ai_service = AIService()
            prompt = FINANCIAL_ANALYSIS_PROMPT.format(
                title=opp.title or "N/A",
                department=opp.department or "N/A",
                naics_code=opp.naics_code or "N/A",
                set_aside=opp.type_of_set_aside or "None",
                description=opp.description or "No description available"
            )
            prompt += f"\n\n## Extracted Financial Data:\n{context[:50000]}"
            
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
                "details": combined_analysis,  # Combined extracted + AI data
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
