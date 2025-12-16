from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fedops_agents.base_agent import BaseAgent
from fedops_core.db.models import Opportunity, OpportunityScore

from fedops_agents.ingestion_agent import IngestionAgent
from fedops_agents.document_analysis_agent import DocumentAnalysisAgent
from fedops_agents.compliance_agent import ComplianceAgent
from fedops_agents.capability_agent import CapabilityMappingAgent
from fedops_agents.financial_agent import FinancialAnalysisAgent
from fedops_core.services.ai_service import AIService
from fedops_core.prompts import EXECUTIVE_OVERVIEW_PROMPT, QUICK_SCAN_SLIDEOUT_PROMPT, GOVCON_PROFILE

from fedops_core.services.extraction_progress import extraction_progress

class OrchestratorAgent(BaseAgent):
    def __init__(self, db: AsyncSession):
        super().__init__("OrchestratorAgent", db)

    async def execute(self, opportunity_id: int, mode: str = "full", **kwargs) -> Dict[str, Any]:
        await self.log_activity(opportunity_id, "START_WORKFLOW", "IN_PROGRESS", {"step": "init", "mode": mode})
        
        quick_scan = (mode == "quick")
        
        # Initialize progress (start with 0 files, will be updated by Doc Analysis)
        extraction_progress.start(opportunity_id, total_files=0, message=f"Initializing {mode} analysis workflow...")
        
        try:
            # 1. Ingestion (Placeholder)
            extraction_progress.update(opportunity_id, message="Step 1/5: Ingesting data...", percent=5)
            # ingestion_agent = IngestionAgent(self.db)
            # await ingestion_agent.execute(opportunity_id)

            # 2. Document Analysis (Sequential) - This now includes extraction
            await self.log_activity(opportunity_id, "DOCUMENT_ANALYSIS", "IN_PROGRESS")
            extraction_progress.update(opportunity_id, message="Step 2/5: Analyzing documents...", percent=10)
            
            doc_agent = DocumentAnalysisAgent(self.db)
            doc_results = await doc_agent.execute(
                opportunity_id, 
                update_progress=True,
                quick_scan=quick_scan
            )
            
            # Extract the extracted_data to pass to other agents
            extracted_data = doc_results.get("extracted_data", {})
            
            await self.log_activity(opportunity_id, "EXTRACTION_COMPLETE", "SUCCESS", {
                "sections_extracted": [k for k, v in extracted_data.items() if v and k != 'source_documents'] if extracted_data else []
            })

            # 3. Sequential Continual Analysis - Chain outputs
            await self.log_activity(opportunity_id, "CONTINUAL_ANALYSIS", "IN_PROGRESS")
            
            # Initialize default empty results
            comp_results = {"risk_score": 50.0, "details": None, "security_details": None}
            cap_results = {
                "internal_capacity_score": 50.0, 
                "strategic_alignment_score": 50.0, 
                "personnel_details": None,
                "strategic_details": None,
                "capacity_details": None,
                "past_performance_details": None
            }
            fin_results = {"financial_viability_score": 50.0, "details": None}
            
            # Initialize other result dictionaries to avoid UnboundLocalError in quick_scan mode
            comp_results = {}
            cap_results = {}
            executive_overview = {}

            if not quick_scan:
                extraction_progress.update(opportunity_id, message="Step 3/5: Running compliance and financial analysis...", percent=60)
                
                # Step 1: Compliance & Security (Base layer)
                # Extracts Facility/Personnel Clearance
                comp_agent = ComplianceAgent(self.db)
                comp_results = await comp_agent.execute(opportunity_id, extracted_data=extracted_data)
                security_details = comp_results.get("security_details", {})
                
                # Step 2: Capability & Personnel (Informed by Security)
                # Uses Clearance to filter/inform Personnel requirements
                cap_agent = CapabilityMappingAgent(self.db)
                cap_results = await cap_agent.execute(
                    opportunity_id, 
                    extracted_data=extracted_data,
                    security_context=security_details
                )
                personnel_details = cap_results.get("personnel_details", {})
                
                # Step 3: Financial (Informed by Personnel & Security)
                # Uses Personnel LCATs/FTEs to build PTW model
                fin_agent = FinancialAnalysisAgent(self.db)
                fin_results = await fin_agent.execute(
                    opportunity_id, 
                    extracted_data=extracted_data,
                    security_context=security_details,
                    personnel_context=personnel_details
                )
            else:
                 extraction_progress.update(opportunity_id, message="Step 3/5: Running Quick Scan Analysis...", percent=70)
                 # Quick Scan Custom Workflow
                 # We want to run the specific QUICK_SCAN_SLIDEOUT_PROMPT
                 
                 # Prepare Context
                 result = await self.db.execute(select(Opportunity).where(Opportunity.id == opportunity_id))
                 opp = result.scalar_one_or_none()
                 
                 # Extract core data from document analysis
                 solicitation_text = ""
                 if extracted_data:
                     # Attempt to construct a text representation of the extracted data
                     # Or stick to the requirement "Extract from provided text" - but we only have extracted JSON here.
                     # However, the prompt asks to "Extract from provided text". 
                     # Ideally we pass the raw text, but that might be huge.
                     # Let's pass the structured data as JSON string, LLM can parse it.
                     import json
                     solicitation_text = json.dumps(extracted_data, default=str)

                 opportunity_data = f"""
                 Title: {opp.title}
                 Department: {opp.department}
                 Sub-Tier Agency: {opp.sub_tier or 'Not Specified'}
                 Office: {opp.office or 'Not Specified'}
                 Description: {opp.description}
                 
                 NAICS Code: {opp.naics_code or 'Not Specified'}
                 PSC/Classification Code: {opp.classification_code or 'Not Specified'}
                 Set-Aside Type: {opp.type_of_set_aside_description or opp.type_of_set_aside or 'Full & Open'}
                 Response Deadline: {opp.response_deadline.strftime('%B %d, %Y') if opp.response_deadline else 'Not Specified'}
                 Posted Date: {opp.posted_date.strftime('%B %d, %Y') if opp.posted_date else 'Not Specified'}
                 Place of Performance: {opp.place_of_performance if opp.place_of_performance else 'Not Specified'}
                 Solicitation Number: {opp.solicitation_number or 'Not Specified'}
                 Notice ID: {opp.notice_id or 'Not Specified'}
                 
                 Extracted Solicitation Data:
                 {solicitation_text}
                 """
                 
                 print(f"DEBUG: Quick Scan Opportunity Data Length: {len(opportunity_data)}")
                 
                 ai_service = AIService()
                 formatted_prompt = QUICK_SCAN_SLIDEOUT_PROMPT.format(
                    govcon_profile=GOVCON_PROFILE,
                    opportunity_data=opportunity_data
                 )
                 
                 print(f"DEBUG: Formatted Prompt Length: {len(formatted_prompt)}")
                 
                 try:
                    # Use generate_content directly because we expect raw HTML, not JSON
                    quick_scan_html = await ai_service.generate_content(formatted_prompt)
                 except Exception as e:
                    print(f"ERROR: Quick Scan AI Call Failed: {e}")
                    quick_scan_html = f"<p style='color:red'>Error generating Quick Scan: {str(e)}</p>"
                 
                 # Store in a temporary dict to merge into score later
                 # We'll use 'executive_overview' or a custom field. 
                 # Let's put it in 'executive_overview' -> 'quick_scan_html'
                 
                 executive_overview = {"quick_scan_html": quick_scan_html}


            # 4. Executive Overview Generation (Only if NOT quick scan, or we use the quick scan result)
            extraction_progress.update(opportunity_id, message="Step 4/5: Finalizing report...", percent=80)
            
            if not quick_scan:
                result = await self.db.execute(select(Opportunity).where(Opportunity.id == opportunity_id))
                opp = result.scalar_one_or_none()
                
                ai_service = AIService()
                overview_prompt = EXECUTIVE_OVERVIEW_PROMPT.format(
                    title=opp.title or "N/A",
                    department=opp.department or "N/A",
                    description=opp.description or "No description available",
                    financial_score=fin_results.get("financial_viability_score", 0.0),
                    strategic_score=cap_results.get("strategic_alignment_score", 0.0),
                    risk_score=comp_results.get("risk_score", 0.0),
                    capacity_score=cap_results.get("internal_capacity_score", 0.0)
                )
                
                executive_overview = await ai_service.analyze_opportunity(overview_prompt)

            # 5. Score Calculation & Data Aggregation
            extraction_progress.update(opportunity_id, message="Step 5/5: Calculating final scores...", percent=90)
            score_data = {
                "contract_risk_score": comp_results.get("risk_score", 0.0),
                "internal_capacity_score": cap_results.get("internal_capacity_score", 0.0),
                "financial_viability_score": fin_results.get("financial_viability_score", 0.0),
                "strategic_alignment_score": cap_results.get("strategic_alignment_score", 50.0),
                "data_integrity_score": 100.0,  # Placeholder
                # AI-generated details (now includes extracted_data)
                "financial_details": fin_results.get("details"),
                "strategic_details": cap_results.get("strategic_details"),
                "risk_details": comp_results.get("details"),
                "capacity_details": cap_results.get("capacity_details"),
                "personnel_details": cap_results.get("personnel_details"),
                "past_performance_details": cap_results.get("past_performance_details"),
                # New Analysis Details
                "solicitation_details": doc_results.get("solicitation_details"),
                "security_details": comp_results.get("security_details"),
                "executive_overview": executive_overview,
                # Store extracted data for reference
                "extracted_data": extracted_data
            }
            
            final_score = await self.calculate_score(opportunity_id, score_data)
            
            await self.log_activity(opportunity_id, "END_WORKFLOW", "SUCCESS", {"final_score": final_score})
            extraction_progress.complete(opportunity_id, requirements_count=0, artifacts_count=0)
            return {"status": "success", "score": final_score}

        except Exception as e:
            await self.log_activity(opportunity_id, "WORKFLOW_ERROR", "FAILURE", {"error": str(e)})
            extraction_progress.fail(opportunity_id, error=str(e))
            raise e

    async def calculate_score(self, opportunity_id: int, scores: Dict[str, float]) -> float:
        result = await self.db.execute(select(OpportunityScore).where(OpportunityScore.opportunity_id == opportunity_id))
        score_entry = result.scalar_one_or_none()
        
        if not score_entry:
            score_entry = OpportunityScore(opportunity_id=opportunity_id)
            self.db.add(score_entry)
        
        # Weights
        w_strategic = 0.30
        w_financial = 0.25
        w_risk = 0.20
        w_capacity = 0.15
        w_data = 0.10
        
        risk_contribution = (100.0 - scores["contract_risk_score"]) * w_risk
        
        weighted_score = (
            (scores["strategic_alignment_score"] * w_strategic) +
            (scores["financial_viability_score"] * w_financial) +
            risk_contribution +
            (scores["internal_capacity_score"] * w_capacity) +
            (scores["data_integrity_score"] * w_data)
        )
        
        score_entry.strategic_alignment_score = scores["strategic_alignment_score"]
        score_entry.financial_viability_score = scores["financial_viability_score"]
        score_entry.contract_risk_score = scores["contract_risk_score"]
        score_entry.internal_capacity_score = scores["internal_capacity_score"]
        score_entry.data_integrity_score = scores["data_integrity_score"]
        
        score_entry.weighted_score = weighted_score
        
        if weighted_score >= 70.0:
            score_entry.go_no_go_decision = "GO"
        elif weighted_score >= 50.0:
            score_entry.go_no_go_decision = "REVIEW"
        else:
            score_entry.go_no_go_decision = "NO_GO"
        
        # Store AI-generated details and extracted data
        from datetime import datetime
        score_entry.details = {
            "financial": scores.get("financial_details"),
            "strategic": scores.get("strategic_details"),
            "risk": scores.get("risk_details"),
            "capacity": scores.get("capacity_details"),
            "personnel": scores.get("personnel_details"),
            "past_performance": scores.get("past_performance_details"),
            "solicitation": scores.get("solicitation_details"),
            "security": scores.get("security_details"),
            "executive_overview": scores.get("executive_overview"),
            "extracted_data": scores.get("extracted_data"),  # NEW: Store extracted document data
            "generated_at": datetime.utcnow().isoformat()
        }
            
        await self.db.commit()
        
        return weighted_score
