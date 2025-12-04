"""
Gate Validation Service for Shipley Workflow
Enforces decision gates and validates workflow transitions
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from typing import Optional, Dict, Any

from fedops_core.db.models import Proposal, Opportunity, ShipleyPhase, OpportunityPipeline
from fedops_core.db.shipley_models import ReviewGate, BidNoGidCriteria


class GateValidationService:
    """Service to enforce Shipley decision gates and validate phase transitions"""
    
    @staticmethod
    async def validate_pursuit_decision(
        db: AsyncSession,
        opportunity_id: int,
        decision: str,  # "GO" or "NO_GO"
        decision_by: str,
        justification: str
    ) -> Dict[str, Any]:
        """
        Phase 1 → Phase 2: Pursuit Decision Gate
        Validates and records the pursuit decision
        """
        # Get or create proposal
        result = await db.execute(
            select(Proposal).where(Proposal.opportunity_id == opportunity_id)
        )
        proposal = result.scalar_one_or_none()
        
        if not proposal:
            # Create new proposal in Phase 1
            proposal = Proposal(
                opportunity_id=opportunity_id,
                shipley_phase=ShipleyPhase.PHASE_1_LONG_TERM_POSITIONING.value
            )
            db.add(proposal)
            await db.flush()
        
        # Create ReviewGate record
        review_gate = ReviewGate(
            proposal_id=proposal.id,
            gate_type="PURSUIT",
            outcome="PASS" if decision == "GO" else "FAIL",
            decision_by=decision_by,
            decision_date=datetime.utcnow(),
            justification=justification
        )
        db.add(review_gate)
        
        # Transition to Phase 2 if GO
        if decision == "GO":
            proposal.shipley_phase = ShipleyPhase.PHASE_2_OPPORTUNITY_ASSESSMENT.value
            proposal.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(proposal)
        
        return {
            "success": True,
            "proposal_id": proposal.id,
            "new_phase": proposal.shipley_phase,
            "gate_id": review_gate.id
        }
    
    @staticmethod
    async def validate_bid_decision(
        db: AsyncSession,
        opportunity_id: int,
        decision: str,  # "BID" or "NO_BID"
        decision_by: str,
        bid_score: Optional[float] = None,
        override_justification: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Phase 2 → Phase 3: Bid Decision Gate (CRITICAL)
        Enforces automation bias mitigation - requires justification for overrides
        """
        # Get proposal
        result = await db.execute(
            select(Proposal).where(Proposal.opportunity_id == opportunity_id)
        )
        proposal = result.scalar_one_or_none()
        
        if not proposal:
            raise ValueError(f"No proposal found for opportunity {opportunity_id}")
        
        # Get bid score criteria if available
        score_result = await db.execute(
            select(BidNoGidCriteria).where(BidNoGidCriteria.opportunity_id == opportunity_id)
        )
        bid_criteria = score_result.scalar_one_or_none()
        
        # Check for automation bias - if score suggests NO_BID but user overrides to BID
        requires_justification = False
        if bid_criteria and bid_criteria.recommendation == "NO_BID" and decision == "BID":
            requires_justification = True
            if not override_justification:
                return {
                    "success": False,
                    "error": "Override justification required when bidding against recommendation",
                    "automated_recommendation": "NO_BID",
                    "automated_score": bid_criteria.weighted_score
                }
        
        # Create ReviewGate record
        review_gate = ReviewGate(
            proposal_id=proposal.id,
            gate_type="BID",
            outcome="PASS" if decision == "BID" else "FAIL",
            score=bid_score or (bid_criteria.weighted_score if bid_criteria else None),
            decision_by=decision_by,
            decision_date=datetime.utcnow(),
            justification=override_justification if requires_justification else None,
            details={
                "automated_recommendation": bid_criteria.recommendation if bid_criteria else None,
                "automated_score": bid_criteria.weighted_score if bid_criteria else None,
                "override": requires_justification
            }
        )
        db.add(review_gate)
        
        # Update proposal
        proposal.bid_decision_score = bid_score or (bid_criteria.weighted_score if bid_criteria else None)
        proposal.bid_decision_justification = override_justification
        proposal.bid_decision_date = datetime.utcnow()
        proposal.bid_decision_by = decision_by
        
        # Transition to Phase 3 if BID
        if decision == "BID":
            proposal.shipley_phase = ShipleyPhase.PHASE_3_CAPTURE_PLANNING.value
            
            # Also update Pipeline Stage
            pipeline_result = await db.execute(
                select(OpportunityPipeline).where(OpportunityPipeline.opportunity_id == opportunity_id)
            )
            pipeline_item = pipeline_result.scalar_one_or_none()
            if pipeline_item:
                pipeline_item.stage = "PROPOSAL_DEV"
                pipeline_item.status = "GO"
        
        proposal.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(proposal)
        
        return {
            "success": True,
            "proposal_id": proposal.id,
            "new_phase": proposal.shipley_phase,
            "gate_id": review_gate.id,
            "override_logged": requires_justification
        }
    
    @staticmethod
    async def validate_bid_validation_decision(
        db: AsyncSession,
        proposal_id: int,
        red_team_passed: bool,
        decision_by: str,
        justification: str
    ) -> Dict[str, Any]:
        """
        Phase 5 → Submission: Bid Validation Gate
        Verifies Red Team review passed before allowing submission
        """
        # Get proposal
        result = await db.execute(
            select(Proposal).where(Proposal.id == proposal_id)
        )
        proposal = result.scalar_one_or_none()
        
        if not proposal:
            raise ValueError(f"No proposal found with id {proposal_id}")
        
        # Verify Red Team review exists and passed
        red_team_result = await db.execute(
            select(ReviewGate).where(
                ReviewGate.proposal_id == proposal_id,
                ReviewGate.review_type == "RED"
            ).order_by(ReviewGate.created_at.desc())
        )
        red_team_review = red_team_result.scalar_one_or_none()
        
        if not red_team_review:
            return {
                "success": False,
                "error": "Red Team review required before bid validation"
            }
        
        if red_team_review.outcome != "PASS" and not red_team_passed:
            return {
                "success": False,
                "error": "Red Team review must pass before submission"
            }
        
        # Create Bid Validation gate
        validation_gate = ReviewGate(
            proposal_id=proposal_id,
            gate_type="BID_VALIDATION",
            outcome="PASS" if red_team_passed else "FAIL",
            decision_by=decision_by,
            decision_date=datetime.utcnow(),
            justification=justification,
            details={
                "red_team_review_id": red_team_review.id,
                "red_team_outcome": red_team_review.outcome
            }
        )
        db.add(validation_gate)
        
        # Proposal remains in Phase 5 but is now approved for submission
        proposal.updated_at = datetime.utcnow()
        
        await db.commit()
        
        return {
            "success": True,
            "proposal_id": proposal_id,
            "gate_id": validation_gate.id,
            "approved_for_submission": red_team_passed
        }
    
    @staticmethod
    async def check_gate_prerequisites(
        db: AsyncSession,
        proposal_id: int,
        target_phase: str
    ) -> Dict[str, Any]:
        """
        Check if all prerequisites are met for transitioning to target phase
        """
        # Get proposal
        result = await db.execute(
            select(Proposal).where(Proposal.id == proposal_id)
        )
        proposal = result.scalar_one_or_none()
        
        if not proposal:
            raise ValueError(f"No proposal found with id {proposal_id}")
        
        prerequisites = {
            ShipleyPhase.PHASE_2_OPPORTUNITY_ASSESSMENT.value: {
                "required_gates": ["PURSUIT"],
                "description": "Pursuit decision required"
            },
            ShipleyPhase.PHASE_3_CAPTURE_PLANNING.value: {
                "required_gates": ["BID"],
                "description": "Bid decision required"
            },
            ShipleyPhase.PHASE_4_PROPOSAL_PLANNING.value: {
                "required_gates": ["BID"],
                "description": "Bid decision and capture plan required"
            },
            ShipleyPhase.PHASE_5_PROPOSAL_DEVELOPMENT.value: {
                "required_gates": ["BID"],
                "description": "Proposal Management Plan required"
            }
        }
        
        if target_phase not in prerequisites:
            return {"success": True, "prerequisites_met": True}
        
        required_gates = prerequisites[target_phase]["required_gates"]
        
        # Check if required gates exist
        for gate_type in required_gates:
            gate_result = await db.execute(
                select(ReviewGate).where(
                    ReviewGate.proposal_id == proposal_id,
                    ReviewGate.gate_type == gate_type,
                    ReviewGate.outcome == "PASS"
                )
            )
            gate = gate_result.scalar_one_or_none()
            
            if not gate:
                return {
                    "success": False,
                    "prerequisites_met": False,
                    "missing_gate": gate_type,
                    "description": prerequisites[target_phase]["description"]
                }
        
        return {"success": True, "prerequisites_met": True}
    
    @staticmethod
    async def enforce_phase_transition(
        db: AsyncSession,
        proposal_id: int,
        from_phase: str,
        to_phase: str
    ) -> Dict[str, Any]:
        """
        Enforce valid phase transitions in the Shipley workflow
        """
        # Define valid transitions
        valid_transitions = {
            ShipleyPhase.PHASE_0_MARKET_SEGMENTATION.value: [
                ShipleyPhase.PHASE_1_LONG_TERM_POSITIONING.value
            ],
            ShipleyPhase.PHASE_1_LONG_TERM_POSITIONING.value: [
                ShipleyPhase.PHASE_2_OPPORTUNITY_ASSESSMENT.value
            ],
            ShipleyPhase.PHASE_2_OPPORTUNITY_ASSESSMENT.value: [
                ShipleyPhase.PHASE_3_CAPTURE_PLANNING.value
            ],
            ShipleyPhase.PHASE_3_CAPTURE_PLANNING.value: [
                ShipleyPhase.PHASE_4_PROPOSAL_PLANNING.value
            ],
            ShipleyPhase.PHASE_4_PROPOSAL_PLANNING.value: [
                ShipleyPhase.PHASE_5_PROPOSAL_DEVELOPMENT.value
            ],
            ShipleyPhase.PHASE_5_PROPOSAL_DEVELOPMENT.value: [
                ShipleyPhase.PHASE_6_POST_SUBMITTAL.value
            ]
        }
        
        if from_phase not in valid_transitions:
            return {
                "success": False,
                "error": f"Invalid source phase: {from_phase}"
            }
        
        if to_phase not in valid_transitions[from_phase]:
            return {
                "success": False,
                "error": f"Invalid transition from {from_phase} to {to_phase}",
                "valid_transitions": valid_transitions[from_phase]
            }
        
        # Check prerequisites
        prereq_check = await GateValidationService.check_gate_prerequisites(
            db, proposal_id, to_phase
        )
        
        if not prereq_check.get("prerequisites_met"):
            return prereq_check
        
        # Update proposal phase
        result = await db.execute(
            select(Proposal).where(Proposal.id == proposal_id)
        )
        proposal = result.scalar_one_or_none()
        
        if not proposal:
            raise ValueError(f"No proposal found with id {proposal_id}")
        
        proposal.shipley_phase = to_phase
        proposal.updated_at = datetime.utcnow()
        
        # Sync with Pipeline Stage
        pipeline_result = await db.execute(
            select(OpportunityPipeline).where(OpportunityPipeline.opportunity_id == proposal.opportunity_id)
        )
        pipeline_item = pipeline_result.scalar_one_or_none()
        if pipeline_item:
            if to_phase in [ShipleyPhase.PHASE_3_CAPTURE_PLANNING.value, ShipleyPhase.PHASE_4_PROPOSAL_PLANNING.value, ShipleyPhase.PHASE_5_PROPOSAL_DEVELOPMENT.value]:
                pipeline_item.stage = "PROPOSAL_DEV"
            elif to_phase == ShipleyPhase.PHASE_6_POST_SUBMITTAL.value:
                pipeline_item.stage = "SUBMISSION"
                pipeline_item.status = "SUBMITTED"
        
        await db.commit()
        
        return {
            "success": True,
            "proposal_id": proposal_id,
            "new_phase": to_phase
        }
