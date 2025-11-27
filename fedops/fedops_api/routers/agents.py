from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Dict, Any

from fedops_core.db.engine import get_db
from fedops_agents.orchestrator import OrchestratorAgent
from fedops_core.db.models import OpportunityScore, AgentActivityLog, Opportunity

router = APIRouter(
    tags=["agents"],
    responses={404: {"description": "Not found"}},
)

@router.post("/opportunities/{opportunity_id}/analyze")
async def trigger_analysis(opportunity_id: int, db: AsyncSession = Depends(get_db)):
    """
    Triggers the full agentic analysis workflow for a given opportunity.
    """
    orchestrator = OrchestratorAgent(db)
    try:
        result = await orchestrator.execute(opportunity_id)
        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

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
