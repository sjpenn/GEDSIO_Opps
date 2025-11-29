"""
API Router for Shipley Decision Gates
Handles Pursuit, Bid, and Bid Validation decisions
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional

from fedops_core.db.engine import get_db
from fedops_core.services.gate_validation_service import GateValidationService
from fedops_core.services.qualification_service import QualificationService


router = APIRouter(
    prefix="/gates",
    tags=["gates"]
)


# Pydantic models for requests
class PursuitDecisionRequest(BaseModel):
    decision: str  # "GO" or "NO_GO"
    decision_by: str
    justification: str


class BidDecisionRequest(BaseModel):
    decision: str  # "BID" or "NO_BID"
    decision_by: str
    override_justification: Optional[str] = None


class BidValidationRequest(BaseModel):
    red_team_passed: bool
    decision_by: str
    justification: str


class CustomWeightsRequest(BaseModel):
    position_weight: float
    capability_weight: float
    attractiveness_weight: float


@router.post("/opportunities/{opportunity_id}/pursuit")
async def execute_pursuit_decision(
    opportunity_id: int,
    request: PursuitDecisionRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Phase 1 → Phase 2: Pursuit Decision Gate
    Initiates opportunity assessment
    """
    try:
        result = await GateValidationService.validate_pursuit_decision(
            db=db,
            opportunity_id=opportunity_id,
            decision=request.decision,
            decision_by=request.decision_by,
            justification=request.justification
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/opportunities/{opportunity_id}/bid")
async def execute_bid_decision(
    opportunity_id: int,
    request: BidDecisionRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Phase 2 → Phase 3: Bid Decision Gate (CRITICAL)
    Enforces automation bias mitigation - requires justification for overrides
    """
    try:
        # First, calculate bid score
        bid_score_result = await QualificationService.calculate_bid_score(
            db=db,
            opportunity_id=opportunity_id
        )
        
        # Then validate decision
        result = await GateValidationService.validate_bid_decision(
            db=db,
            opportunity_id=opportunity_id,
            decision=request.decision,
            decision_by=request.decision_by,
            bid_score=bid_score_result["weighted_score"],
            override_justification=request.override_justification
        )
        
        # Include bid score details in response
        result["bid_score_details"] = bid_score_result
        
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/proposals/{proposal_id}/bid_validation")
async def execute_bid_validation(
    proposal_id: int,
    request: BidValidationRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Phase 5 → Submission: Bid Validation Gate
    Verifies Red Team review passed before allowing submission
    """
    try:
        result = await GateValidationService.validate_bid_validation_decision(
            db=db,
            proposal_id=proposal_id,
            red_team_passed=request.red_team_passed,
            decision_by=request.decision_by,
            justification=request.justification
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/opportunities/{opportunity_id}/bid_score")
async def get_bid_score(
    opportunity_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get calculated Bid/No-Bid score and detailed breakdown
    Shows Position to Win, Capability/Capacity, and Attractiveness scores
    """
    try:
        result = await QualificationService.calculate_bid_score(
            db=db,
            opportunity_id=opportunity_id
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/opportunities/{opportunity_id}/bid_score/customize_weights")
async def customize_bid_weights(
    opportunity_id: int,
    request: CustomWeightsRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Customize scoring weights for Bid/No-Bid calculation
    Allows user to adjust importance of Position, Capability, and Attractiveness
    """
    try:
        result = await QualificationService.customize_weights(
            db=db,
            opportunity_id=opportunity_id,
            position_weight=request.position_weight,
            capability_weight=request.capability_weight,
            attractiveness_weight=request.attractiveness_weight
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/proposals/{proposal_id}/prerequisites/{target_phase}")
async def check_phase_prerequisites(
    proposal_id: int,
    target_phase: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Check if all prerequisites are met for transitioning to target phase
    """
    try:
        result = await GateValidationService.check_gate_prerequisites(
            db=db,
            proposal_id=proposal_id,
            target_phase=target_phase
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
