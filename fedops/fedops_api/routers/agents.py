from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any

from fedops_core.db.engine import get_db
from fedops_agents.orchestrator import OrchestratorAgent
from fedops_core.db.models import OpportunityScore, AgentActivityLog

router = APIRouter(
    prefix="/agents",
    tags=["agents"],
    responses={404: {"description": "Not found"}},
)

@router.post("/opportunities/{opportunity_id}/analyze")
def trigger_analysis(opportunity_id: int, db: Session = Depends(get_db)):
    """
    Triggers the full agentic analysis workflow for a given opportunity.
    """
    orchestrator = OrchestratorAgent(db)
    try:
        result = orchestrator.execute(opportunity_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/opportunities/{opportunity_id}/score")
def get_opportunity_score(opportunity_id: int, db: Session = Depends(get_db)):
    """
    Retrieves the calculated score for an opportunity.
    """
    score = db.query(OpportunityScore).filter(OpportunityScore.opportunity_id == opportunity_id).first()
    if not score:
        raise HTTPException(status_code=404, detail="Score not found")
    return score

@router.get("/opportunities/{opportunity_id}/logs")
def get_agent_logs(opportunity_id: int, db: Session = Depends(get_db)):
    """
    Retrieves the activity logs for an opportunity.
    """
    logs = db.query(AgentActivityLog).filter(AgentActivityLog.opportunity_id == opportunity_id).all()
    return logs
