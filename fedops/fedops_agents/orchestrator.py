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
        turbo_mode = (mode == "turbo")
        
        # Initialize progress with enhanced tracking
        extraction_progress.start(opportunity_id, total_files=0, message=f"🚀 Initializing {mode} analysis...")
        extraction_progress.set_stage(opportunity_id, "initialization", percent=0)
        
        try:
            # 1. Ingestion Stage
            extraction_progress.set_stage(opportunity_id, "ingestion", message="📥 Loading opportunity files...", percent=5)
            # ingestion_agent = IngestionAgent(self.db)
            # await ingestion_agent.execute(opportunity_id)

            # 2. Document Analysis (Sequential) - This now includes extraction
            await self.log_activity(opportunity_id, "DOCUMENT_ANALYSIS", "IN_PROGRESS")
            extraction_progress.set_stage(opportunity_id, "extraction", message="📄 Extracting document contents...", percent=10)
            
            doc_agent = DocumentAnalysisAgent(self.db)
            doc_results = await doc_agent.execute(
                opportunity_id, 
                update_progress=True,
                quick_scan=quick_scan or turbo_mode,  # turbo mode implies quick_scan
                turbo=turbo_mode  # NEW: pass turbo mode
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
                extraction_progress.set_stage(opportunity_id, "analysis", message="🔍 Running deep analysis agents...", percent=55)
                
                extraction_progress.set_operation(opportunity_id, "analyzing", "Compliance & Risk", percent=60)
                
                # Step 1: Compliance & Security (Base layer)
                extraction_progress.set_operation(opportunity_id, "analyzing", "Compliance & Security")
                comp_agent = ComplianceAgent(self.db)
                comp_results = await comp_agent.execute(opportunity_id, extracted_data=extracted_data)
                security_details = comp_results.get("security_details", {})
                
                # Step 2: Capability & Personnel (Informed by Security)
                extraction_progress.set_operation(opportunity_id, "analyzing", "Capability & Personnel", percent=70)
                cap_agent = CapabilityMappingAgent(self.db)
                cap_results = await cap_agent.execute(
                    opportunity_id, 
                    extracted_data=extracted_data,
                    security_context=security_details
                )
                personnel_details = cap_results.get("personnel_details", {})
                
                # Step 3: Financial (Informed by Personnel & Security)
                extraction_progress.set_operation(opportunity_id, "analyzing", "Financial Viability", percent=75)
                fin_agent = FinancialAnalysisAgent(self.db)
                fin_results = await fin_agent.execute(
                    opportunity_id, 
                    extracted_data=extracted_data,
                    security_context=security_details,
                    personnel_context=personnel_details
                )
            else:
                 extraction_progress.set_stage(opportunity_id, "analysis", message="⚡ Running Quick Scan...", percent=60)
                 extraction_progress.set_operation(opportunity_id, "summarizing", "Quick Scan Summary", percent=70)
                 # Quick Scan Custom Workflow
                 # We want to run the specific QUICK_SCAN_SLIDEOUT_PROMPT
                 
                 # Prepare Context
                 result = await self.db.execute(select(Opportunity).where(Opportunity.id == opportunity_id))
                 opp = result.scalar_one_or_none()
                 
                 # Extract core data from document analysis
                 solicitation_text = ""
                 section_l_text = ""
                 section_m_text = ""
                 sow_text = ""
                 
                 if extracted_data:
                     import json
                     
                     # Extract key sections for better AI parsing
                     section_l = extracted_data.get("section_l", {})
                     section_m = extracted_data.get("section_m", {})
                     sow_data = extracted_data.get("sow", {}) or extracted_data.get("pws", {})
                     
                     if section_l:
                         section_l_text = f"""
=== SECTION L - INSTRUCTIONS TO OFFERORS ===
{json.dumps(section_l, indent=2, default=str)}
"""
                     
                     if section_m:
                         section_m_text = f"""
=== SECTION M - EVALUATION CRITERIA ===
{json.dumps(section_m, indent=2, default=str)}
"""
                     
                     if sow_data:
                         sow_text = f"""
=== STATEMENT OF WORK / PERFORMANCE WORK STATEMENT ===
{json.dumps(sow_data, indent=2, default=str)}
"""
                     
                     # Full extracted data as fallback
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
                 Response Deadline: {opp.response_deadline.strftime('%B %d, %Y at %I:%M %p') if opp.response_deadline else 'Not Specified'}
                 Posted Date: {opp.posted_date.strftime('%B %d, %Y') if opp.posted_date else 'Not Specified'}
                 Place of Performance: {opp.place_of_performance if opp.place_of_performance else 'Not Specified'}
                 Solicitation Number: {opp.solicitation_number or 'Not Specified'}
                 Notice ID: {opp.notice_id or 'Not Specified'}
                 
                 {section_l_text}
                 
                 {section_m_text}
                 
                 {sow_text}
                 
                 === FULL EXTRACTED SOLICITATION DATA ===
                 {solicitation_text}
                 """
                 
                 print(f"DEBUG: Quick Scan Opportunity Data Length: {len(opportunity_data)}")
                 
                 ai_service = AIService()
                 formatted_prompt = QUICK_SCAN_SLIDEOUT_PROMPT.format(
                    govcon_profile=GOVCON_PROFILE,
                    opportunity_data=opportunity_data
                 )
                 
                 print(f"DEBUG: Formatted Prompt Length: {len(formatted_prompt)}")
                 
                 # Override to use Qwen3 for Quick Scan (faster than DeepSeek R1)
                 ai_service.set_provider("openrouter", "qwen/qwen-3-235b-instruct")
                 
                 try:
                    # Use generate_content directly because we expect raw HTML, not JSON
                    # Increase timeout for Quick Scan since it processes large documents
                    quick_scan_html = await ai_service.generate_content(formatted_prompt, timeout=180)
                    print(f"DEBUG: Quick Scan AI call succeeded, response length: {len(quick_scan_html)}")
                 except TimeoutError as e:
                    logger.error(f"Quick Scan AI Call Timed Out: {e}")
                    print(f"ERROR: Quick Scan AI Call Timed Out: {e}")
                    quick_scan_html = f"""
                    <div style='padding: 20px; background-color: #fff3cd; border: 1px solid #ffc107; border-radius: 4px;'>
                        <h3 style='color: #856404; margin-top: 0;'>⚠️ Quick Scan Timeout</h3>
                        <p>The AI analysis took too long to complete. This can happen with:</p>
                        <ul>
                            <li>Very large or complex solicitation documents</li>
                            <li>High server load on the AI provider</li>
                            <li>Network connectivity issues</li>
                        </ul>
                        <p><strong>Recommendation:</strong> Try running a <strong>Full Analysis</strong> instead, which processes documents in smaller chunks.</p>
                    </div>
                    """
                 except Exception as e:
                    logger.error(f"Quick Scan AI Call Failed: {e}", exc_info=True)
                    print(f"ERROR: Quick Scan AI Call Failed: {e}")
                    quick_scan_html = f"""
                    <div style='padding: 20px; background-color: #f8d7da; border: 1px solid #f5c6cb; border-radius: 4px;'>
                        <h3 style='color: #721c24; margin-top: 0;'>❌ Quick Scan Error</h3>
                        <p>An error occurred while generating the Quick Scan analysis:</p>
                        <pre style='background-color: #fff; padding: 10px; border-radius: 4px; overflow-x: auto;'>{str(e)}</pre>
                        <p><strong>Recommendation:</strong> Try running a <strong>Full Analysis</strong> instead.</p>
                    </div>
                    """
                 
                 # Store in a temporary dict to merge into score later
                 # We'll use 'executive_overview' or a custom field. 
                 # Let's put it in 'executive_overview' -> 'quick_scan_html'
                 
                 executive_overview = {"quick_scan_html": quick_scan_html}


            # 4. Executive Overview Generation
            extraction_progress.set_stage(opportunity_id, "finalization", message="📝 Generating executive overview...", percent=80)
            
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
            extraction_progress.set_operation(opportunity_id, "storing", "Final scores to database", percent=90)
            extraction_progress.track_db_operation(opportunity_id, "write")
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
