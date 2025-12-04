from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fedops_agents.base_agent import BaseAgent
from fedops_core.db.models import Opportunity, StoredFile
from fedops_core.services.ai_service import AIService
from fedops_core.prompts import RISK_ANALYSIS_PROMPT, SECURITY_ANALYSIS_PROMPT, determine_document_type, DocumentType

class ComplianceAgent(BaseAgent):
    def __init__(self, db: AsyncSession):
        super().__init__("ComplianceAgent", db)

    async def execute(self, opportunity_id: int, **kwargs) -> Dict[str, Any]:
        await self.log_activity(opportunity_id, "START_COMPLIANCE_CHECK", "IN_PROGRESS")
        
        try:
            # Fetch opportunity data
            result = await self.db.execute(select(Opportunity).where(Opportunity.id == opportunity_id))
            opp = result.scalar_one_or_none()
            
            if not opp:
                raise ValueError(f"Opportunity {opportunity_id} not found")
            
            # Get extracted data from kwargs (passed from orchestrator or DocumentAnalysisAgent)
            extracted_data = kwargs.get('extracted_data') or {}
            
            # Extract security and compliance data from documents
            section_h = extracted_data.get('section_h') or {}
            section_i = extracted_data.get('section_i') or {}
            section_k = extracted_data.get('section_k') or {}
            
            # Build security details from extracted data
            security_details = {
                "facility_clearance": section_h.get("facility_clearance", "Not specified"),
                "personnel_clearance": section_h.get("personnel_clearance", "Not specified"),
                "cybersecurity_requirements": section_i.get("cybersecurity", {}).get("requirements", []) if section_i.get("cybersecurity") else [],
                "other_requirements": section_h.get("other_requirements", []),
                "extracted_from": []
            }
            
            # Track which sections had data
            if section_h:
                security_details["extracted_from"].append("Section H")
            if section_i:
                security_details["extracted_from"].append("Section I")
            if section_k:
                security_details["extracted_from"].append("Section K")
            
            # Build context for AI risk analysis
            context_parts = []
            
            if section_h:
                context_parts.append(f"## Section H (Special Requirements):\n{str(section_h)[:5000]}")
            if section_i:
                context_parts.append(f"## Section I (Contract Clauses):\n{str(section_i)[:5000]}")
            if section_k:
                context_parts.append(f"## Section K (Certifications):\n{str(section_k)[:5000]}")
            
            extracted_context = "\n\n".join(context_parts) if context_parts else "No compliance documents extracted."
            
            ai_service = AIService()
            
            # 1. Risk Analysis with extracted context
            risk_prompt = RISK_ANALYSIS_PROMPT.format(
                title=opp.title or "N/A",
                department=opp.department or "N/A",
                naics_code=opp.naics_code or "N/A",
                set_aside=opp.type_of_set_aside or "None",
                description=opp.description or "No description available",
                place_of_performance=str(opp.place_of_performance) if opp.place_of_performance else "Not specified"
            )
            risk_prompt += f"\n\n## Extracted Compliance Data:\n{extracted_context[:50000]}"
            risk_prompt += "\n\n**Note**: Use the extracted data above to inform your risk analysis. Focus on identifying risks based on the actual requirements found in the documents."
            
            risk_analysis = await ai_service.analyze_opportunity(risk_prompt)
            
            # Safely handle AI response with None checks
            if not risk_analysis or not isinstance(risk_analysis, dict):
                risk_analysis = {}
            
            # 2. Security Analysis with extracted context
            security_prompt = SECURITY_ANALYSIS_PROMPT.format(
                title=opp.title or "N/A",
                department=opp.department or "N/A",
                description=opp.description or "No description available",
                place_of_performance=str(opp.place_of_performance) if opp.place_of_performance else "Not specified"
            )
            security_prompt += f"\n\n## Extracted Security Data:\n{extracted_context[:50000]}"
            security_prompt += "\n\n**Note**: The facility and personnel clearance requirements have been extracted. Validate and enhance this analysis."
            
            ai_security_analysis = await ai_service.analyze_opportunity(security_prompt)
            
            # Safely handle AI response with None checks
            if not ai_security_analysis or not isinstance(ai_security_analysis, dict):
                ai_security_analysis = {}
            
            # Merge extracted security data with AI analysis
            combined_security = {
                **security_details,  # Extracted facts
                "summary": ai_security_analysis.get("summary", "Analysis incomplete"),  # AI-generated summary
                "ai_analysis": ai_security_analysis  # Full AI analysis
            }
            
            # Update with any additional AI-extracted requirements
            if ai_security_analysis.get("cybersecurity_requirements"):
                combined_security["cybersecurity_requirements"].extend(
                    [req for req in ai_security_analysis["cybersecurity_requirements"] 
                     if req not in combined_security["cybersecurity_requirements"]]
                )
            
            # Extract risk score from AI analysis
            risk_score = risk_analysis.get("risk_score", 10.0)
            compliance_status = "COMPLIANT" if risk_score < 50 else "REVIEW_REQUIRED"
            
            # Update Opportunity model
            opp.compliance_status = compliance_status
            opp.risk_score = risk_score
            await self.db.commit()
            
            await self.log_activity(opportunity_id, "END_COMPLIANCE_CHECK", "SUCCESS", {
                "compliance_status": compliance_status,
                "risk_score": risk_score,
                "security_summary": combined_security.get("summary", ""),
                "sections_used": security_details.get("extracted_from", [])
            })
            
            # Add source document references
            source_docs = extracted_data.get('source_documents', []) if extracted_data else []
            if "source_documents" not in risk_analysis:
                risk_analysis["source_documents"] = source_docs
            
            # Combine extracted and AI-generated data
            combined_risk = {
                **risk_analysis,  # AI-generated risk analysis
                "extracted_data": {
                    "section_h": section_h,
                    "section_i": section_i,
                    "section_k": section_k
                }
            }
            
            return {
                "status": "success",
                "compliance_status": compliance_status,
                "risk_score": risk_score,
                "details": combined_risk,  # Risk details with extracted data
                "security_details": combined_security,  # Security details with extracted data
                "source_documents": source_docs
            }

        except Exception as e:
            await self.log_activity(opportunity_id, "COMPLIANCE_ERROR", "FAILURE", {"error": str(e)})
            # Return fallback values on error
            return {
                "status": "error",
                "compliance_status": "UNKNOWN",
                "risk_score": 50.0,
                "details": {
                    "summary": f"Risk analysis failed: {str(e)}",
                    "risk_score": 50.0,
                    "high_risks": [],
                    "medium_risks": [],
                    "compliance_requirements": [],
                    "recommendation": "Unable to provide recommendation due to error",
                    "extracted_data": None
                },
                "security_details": {
                    "summary": f"Security analysis failed: {str(e)}",
                    "facility_clearance": "Unknown",
                    "personnel_clearance": "Unknown",
                    "cybersecurity_requirements": [],
                    "other_requirements": [],
                    "extracted_from": []
                }
            }

