from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Dict, Any

from fedops_core.db.engine import get_db, AsyncSessionLocal
from fedops_agents.orchestrator import OrchestratorAgent
from fedops_core.db.models import OpportunityScore, AgentActivityLog, Opportunity
from fedops_core.services.extraction_progress import extraction_progress

router = APIRouter(
    tags=["agents"],
    responses={404: {"description": "Not found"}},
)

@router.get("/opportunities/{opportunity_id}/analysis/status")
async def get_analysis_status(opportunity_id: int):
    """Get real-time status of analysis"""
    status = extraction_progress.get(opportunity_id)
    if not status:
        return {"status": "idle", "percent": 0, "message": "Not running"}
    return status

async def run_analysis_background(opportunity_id: int, mode: str):
    """Background task wrapper for analysis execution"""
    async with AsyncSessionLocal() as db:
        orchestrator = OrchestratorAgent(db)
        try:
            await orchestrator.execute(opportunity_id, mode=mode)
        except Exception as e:
            import traceback
            traceback.print_exc()
            # We can't return to client, but logs are captured in orchestrator.execute usually

@router.post("/opportunities/{opportunity_id}/analyze", status_code=202)
async def trigger_analysis(
    opportunity_id: int, 
    background_tasks: BackgroundTasks,
    mode: str = "full", 
    db: AsyncSession = Depends(get_db)
):
    """
    Triggers the full agentic analysis workflow for a given opportunity in the background.
    """
    background_tasks.add_task(run_analysis_background, opportunity_id, mode)
    return {"status": "accepted", "message": "Analysis started in background"}

@router.get("/opportunities/{opportunity_id}/score")
async def get_opportunity_score(opportunity_id: int, db: AsyncSession = Depends(get_db)):
    """
    Retrieves the calculated score for an opportunity.
    """
    try:
        result = await db.execute(select(OpportunityScore).where(OpportunityScore.opportunity_id == opportunity_id))
        score = result.scalar_one_or_none()
        if not score:
            raise HTTPException(status_code=404, detail="Score not found. Run analysis first.")
        
        # Return as dict for safe serialization
        return {
            "id": score.id,
            "opportunity_id": score.opportunity_id,
            "strategic_alignment_score": score.strategic_alignment_score,
            "financial_viability_score": score.financial_viability_score,
            "contract_risk_score": score.contract_risk_score,
            "internal_capacity_score": score.internal_capacity_score,
            "data_integrity_score": score.data_integrity_score,
            "weighted_score": score.weighted_score,
            "go_no_go_decision": score.go_no_go_decision,
            "details": score.details,
            "created_at": score.created_at.isoformat() if score.created_at else None,
            "updated_at": score.updated_at.isoformat() if score.updated_at else None
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error fetching score: {str(e)}")

@router.get("/opportunities/{opportunity_id}/logs")
async def get_agent_logs(opportunity_id: int, db: AsyncSession = Depends(get_db)):
    """
    Retrieves the activity logs for an opportunity.
    """
    try:
        result = await db.execute(select(AgentActivityLog).where(AgentActivityLog.opportunity_id == opportunity_id))
        logs = result.scalars().all()
        
        # Convert to list of dicts for safe serialization
        return [
            {
                "id": log.id,
                "opportunity_id": log.opportunity_id,
                "agent_name": log.agent_name,
                "action": log.action,
                "details": log.details,
                "status": log.status,
                "timestamp": log.timestamp.isoformat() if log.timestamp else None
            }
            for log in logs
        ]
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error fetching logs: {str(e)}")

@router.get("/opportunities/{opportunity_id}/analysis")
async def get_full_analysis(opportunity_id: int, db: AsyncSession = Depends(get_db)):
    """
    Retrieves complete analysis data for the standalone analysis viewer.
    Includes opportunity details, scores, and activity logs.
    """
    try:
        # Fetch opportunity details
        opp_result = await db.execute(select(Opportunity).where(Opportunity.id == opportunity_id))
        opportunity = opp_result.scalar_one_or_none()
        if not opportunity:
            raise HTTPException(status_code=404, detail="Opportunity not found")
        
        # Fetch score data
        score_result = await db.execute(select(OpportunityScore).where(OpportunityScore.opportunity_id == opportunity_id))
        score = score_result.scalar_one_or_none()
        
        # Fetch activity logs
        logs_result = await db.execute(select(AgentActivityLog).where(AgentActivityLog.opportunity_id == opportunity_id))
        logs = logs_result.scalars().all()
        
        # Build comprehensive response
        return {
            "opportunity": {
                "id": opportunity.id,
                "title": opportunity.title,
                "description": opportunity.description,
                "notice_id": opportunity.notice_id,
                "department": opportunity.department,
                "sub_tier": opportunity.sub_tier,
                "office": opportunity.office,
                "posted_date": opportunity.posted_date.isoformat() if opportunity.posted_date else None,
                "response_deadline": opportunity.response_deadline.isoformat() if opportunity.response_deadline else None,
                "archive_date": opportunity.archive_date.isoformat() if opportunity.archive_date else None,
                "naics_code": opportunity.naics_code,
                "classification_code": opportunity.classification_code,
                "type_of_set_aside": opportunity.type_of_set_aside,
                "place_of_performance": opportunity.place_of_performance,
                "active": opportunity.active,
                "compliance_status": opportunity.compliance_status,
                "risk_score": opportunity.risk_score,
                "full_parent_path_name": opportunity.full_response.get("fullParentPathName") if opportunity.full_response else None,
            },
            "score": {
                "id": score.id,
                "opportunity_id": score.opportunity_id,
                "strategic_alignment_score": score.strategic_alignment_score,
                "financial_viability_score": score.financial_viability_score,
                "contract_risk_score": score.contract_risk_score,
                "internal_capacity_score": score.internal_capacity_score,
                "data_integrity_score": score.data_integrity_score,
                "weighted_score": score.weighted_score,
                "go_no_go_decision": score.go_no_go_decision,
                "details": score.details,
                "created_at": score.created_at.isoformat() if score.created_at else None,
                "updated_at": score.updated_at.isoformat() if score.updated_at else None
            } if score else None,
            "logs": [
                {
                    "id": log.id,
                    "opportunity_id": log.opportunity_id,
                    "agent_name": log.agent_name,
                    "action": log.action,
                    "details": log.details,
                    "status": log.status,
                    "timestamp": log.timestamp.isoformat() if log.timestamp else None
                }
                for log in logs
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error fetching analysis data: {str(e)}")

@router.get("/opportunities/{opportunity_id}/eligibility")
async def check_opportunity_eligibility(
    opportunity_id: int, 
    db: AsyncSession = Depends(get_db)
):
    """
    Check if primary entity qualifies for this opportunity.
    Returns detailed eligibility status with disqualification reasons.
    """
    from fedops_core.services.qualification_service import QualificationService
    
    try:
        result = await QualificationService.check_eligibility(db, opportunity_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error checking eligibility: {str(e)}")


# =============================================================================
# RFI RESPONSE ENGINE ENDPOINTS
# =============================================================================

@router.post("/opportunities/{opportunity_id}/rfi/extract-requirements")
async def extract_rfi_requirements(
    opportunity_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Extract all requirements/questions from an RFI document.
    Returns structured list of requirements that need responses.
    """
    from fedops_core.services.rfi_response_service import RFIResponseService
    
    try:
        service = RFIResponseService(db)
        result = await service.extract_requirements(opportunity_id)
        
        # Return the full result including debug info on error
        # This helps diagnose AI response parsing issues
        return result
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error extracting requirements: {str(e)}")


@router.post("/opportunities/{opportunity_id}/rfi/generate-responses")
async def generate_rfi_responses(
    opportunity_id: int,
    requirements: list = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Generate responses for all RFI requirements.
    Optionally accepts a list of requirements, otherwise extracts them first.
    """
    from fedops_core.services.rfi_response_service import RFIResponseService
    
    try:
        service = RFIResponseService(db)
        result = await service.generate_all_responses(opportunity_id, requirements)
        
        if result.get("error"):
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error generating responses: {str(e)}")


@router.post("/opportunities/{opportunity_id}/rfi/generate-block-response")
async def generate_single_block_response(
    opportunity_id: int,
    requirement: dict,
    db: AsyncSession = Depends(get_db)
):
    """
    Generate a response for a single requirement block.
    Used for regenerating individual responses.
    """
    from fedops_core.services.rfi_response_service import RFIResponseService
    
    try:
        service = RFIResponseService(db)
        result = await service.generate_block_response(opportunity_id, requirement)
        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error generating block response: {str(e)}")


@router.post("/opportunities/{opportunity_id}/rfi/compile-document")
async def compile_rfi_document(
    opportunity_id: int,
    block_responses: list,
    db: AsyncSession = Depends(get_db)
):
    """
    Compile all block responses into a complete RFI response document.
    Returns Markdown-formatted document ready for export.
    """
    from fedops_core.services.rfi_response_service import RFIResponseService
    
    try:
        service = RFIResponseService(db)
        result = await service.compile_full_response(opportunity_id, block_responses)
        
        if result.get("error"):
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error compiling document: {str(e)}")
