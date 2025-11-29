"""
Qualification Service for Bid/No-Bid Decision
Calculates weighted scores using multi-factor analysis
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from typing import Dict, Any, Optional

from fedops_core.db.models import Opportunity, OpportunityScore, Entity, CompanyProfile
from fedops_core.db.shipley_models import BidNoGidCriteria, CompetitiveIntelligence


class QualificationService:
    """Service to calculate weighted Bid/No-Bid scores"""
    
    @staticmethod
    async def calculate_bid_score(
        db: AsyncSession,
        opportunity_id: int,
        custom_weights: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Main scoring engine - calculates weighted Bid/No-Bid score
        Returns comprehensive scoring breakdown
        """
        # Get opportunity
        result = await db.execute(
            select(Opportunity).where(Opportunity.id == opportunity_id)
        )
        opportunity = result.scalar_one_or_none()
        
        if not opportunity:
            raise ValueError(f"Opportunity {opportunity_id} not found")
        
        # Calculate component scores
        position_score = await QualificationService._assess_position_to_win(db, opportunity)
        capability_score = await QualificationService._assess_capability_capacity(db, opportunity)
        attractiveness_score = await QualificationService._assess_attractiveness(db, opportunity)
        
        # Apply weights (default or custom)
        weights = custom_weights or {
            "position": 0.35,
            "capability": 0.35,
            "attractiveness": 0.30
        }
        
        # Calculate weighted score
        weighted_score = (
            (position_score["composite"] * weights["position"]) +
            (capability_score["composite"] * weights["capability"]) +
            (attractiveness_score["composite"] * weights["attractiveness"])
        )
        
        # Generate recommendation
        recommendation = QualificationService._generate_recommendation(weighted_score)
        
        # Store or update criteria
        criteria_result = await db.execute(
            select(BidNoGidCriteria).where(BidNoGidCriteria.opportunity_id == opportunity_id)
        )
        criteria = criteria_result.scalar_one_or_none()
        
        if not criteria:
            criteria = BidNoGidCriteria(opportunity_id=opportunity_id)
            db.add(criteria)
        
        # Update scores
        criteria.win_probability_score = position_score["win_probability"]
        criteria.competitive_landscape_score = position_score["competitive_landscape"]
        criteria.incumbent_advantage_score = position_score["incumbent_advantage"]
        
        criteria.technical_capability_score = capability_score["technical_capability"]
        criteria.past_performance_relevance_score = capability_score["past_performance"]
        criteria.resource_availability_score = capability_score["resource_availability"]
        criteria.compliance_score = capability_score["compliance"]
        
        criteria.contract_value_score = attractiveness_score["contract_value"]
        criteria.strategic_alignment_score = attractiveness_score["strategic_alignment"]
        criteria.agency_relationship_score = attractiveness_score["agency_relationship"]
        
        criteria.weighted_score = weighted_score
        criteria.recommendation = recommendation
        
        criteria.position_weight = weights["position"]
        criteria.capability_weight = weights["capability"]
        criteria.attractiveness_weight = weights["attractiveness"]
        
        criteria.details = {
            "position_breakdown": position_score,
            "capability_breakdown": capability_score,
            "attractiveness_breakdown": attractiveness_score,
            "calculation_date": datetime.utcnow().isoformat()
        }
        
        criteria.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(criteria)
        
        return {
            "opportunity_id": opportunity_id,
            "weighted_score": weighted_score,
            "recommendation": recommendation,
            "position_to_win": position_score,
            "capability_capacity": capability_score,
            "attractiveness": attractiveness_score,
            "weights": weights,
            "criteria_id": criteria.id
        }
    
    @staticmethod
    async def _assess_position_to_win(
        db: AsyncSession,
        opportunity: Opportunity
    ) -> Dict[str, float]:
        """
        Assess Position to Win (35% weight)
        Uses competitive intelligence data
        """
        # Get competitive intelligence
        comp_intel_result = await db.execute(
            select(CompetitiveIntelligence).where(
                CompetitiveIntelligence.opportunity_id == opportunity.id
            )
        )
        competitors = comp_intel_result.scalars().all()
        
        # Win Probability Score (0-100)
        win_probability = 50.0  # Default neutral
        
        if competitors:
            # Check for incumbent
            incumbent = next((c for c in competitors if c.is_incumbent), None)
            if incumbent:
                # Incumbent present reduces win probability
                win_probability = max(20.0, 50.0 - (incumbent.historical_wins * 5))
            else:
                # No incumbent increases win probability
                win_probability = min(80.0, 50.0 + 20.0)
            
            # Adjust based on number of competitors
            competitor_count = len(competitors)
            if competitor_count > 5:
                win_probability *= 0.8
            elif competitor_count < 2:
                win_probability *= 1.2
        
        # Competitive Landscape Score (0-100)
        competitive_landscape = 50.0
        if competitors:
            # Lower score if many strong competitors
            total_historical_wins = sum(c.historical_wins for c in competitors)
            if total_historical_wins > 10:
                competitive_landscape = 30.0
            elif total_historical_wins < 3:
                competitive_landscape = 70.0
        
        # Incumbent Advantage Score (0-100, higher is better for us)
        incumbent_advantage = 50.0
        if competitors:
            incumbent = next((c for c in competitors if c.is_incumbent), None)
            if incumbent:
                # We are not the incumbent - disadvantage
                incumbent_advantage = 20.0
            else:
                # No incumbent - advantage
                incumbent_advantage = 80.0
        
        # Composite Position to Win score
        composite = (win_probability + competitive_landscape + incumbent_advantage) / 3
        
        return {
            "win_probability": win_probability,
            "competitive_landscape": competitive_landscape,
            "incumbent_advantage": incumbent_advantage,
            "composite": composite
        }
    
    @staticmethod
    async def _assess_capability_capacity(
        db: AsyncSession,
        opportunity: Opportunity
    ) -> Dict[str, float]:
        """
        Assess Capability/Capacity (35% weight)
        Uses SAM entity data and internal resources
        """
        # Get primary company profile
        profile_result = await db.execute(
            select(CompanyProfile).limit(1)
        )
        profile = profile_result.scalar_one_or_none()
        
        # Technical Capability Score (0-100)
        technical_capability = 50.0
        if profile and opportunity.naics_code:
            # Check if NAICS matches our target NAICS
            target_naics = profile.target_naics or []
            if opportunity.naics_code in target_naics:
                technical_capability = 80.0
            else:
                technical_capability = 40.0
        
        # Past Performance Relevance Score (0-100)
        past_performance = 50.0
        # TODO: Implement actual past performance matching
        # For now, use NAICS match as proxy
        if profile and opportunity.naics_code:
            target_naics = profile.target_naics or []
            if opportunity.naics_code in target_naics:
                past_performance = 75.0
        
        # Resource Availability Score (0-100)
        resource_availability = 60.0
        # TODO: Implement actual resource tracking
        # For now, use static score
        
        # Compliance Score (0-100)
        compliance = await QualificationService._check_compliance(db, opportunity, profile)
        
        # Composite Capability/Capacity score
        composite = (
            technical_capability + 
            past_performance + 
            resource_availability + 
            compliance
        ) / 4
        
        return {
            "technical_capability": technical_capability,
            "past_performance": past_performance,
            "resource_availability": resource_availability,
            "compliance": compliance,
            "composite": composite
        }
    
    @staticmethod
    async def _check_compliance(
        db: AsyncSession,
        opportunity: Opportunity,
        profile: Optional[CompanyProfile]
    ) -> float:
        """
        Check compliance with set-aside and eligibility requirements
        Returns 0-100 score
        """
        if not profile or not profile.entity_uei:
            return 50.0  # Unknown compliance
        
        # Get entity data
        entity_result = await db.execute(
            select(Entity).where(Entity.uei == profile.entity_uei)
        )
        entity = entity_result.scalar_one_or_none()
        
        if not entity or not entity.full_response:
            return 50.0
        
        # Check set-aside compliance
        set_aside = opportunity.type_of_set_aside
        if not set_aside or set_aside == "None":
            return 100.0  # No set-aside restrictions
        
        # Check entity business types
        entity_data = entity.full_response
        business_types = []
        
        # Extract business types from SAM data
        if isinstance(entity_data, dict):
            core_data = entity_data.get("coreData", {})
            business_types = core_data.get("businessTypes", {}).get("businessTypeList", [])
            
            # Map business types to set-aside categories
            type_map = {
                "2X": ["8(a)"],
                "A6": ["HUBZone"],
                "QF": ["Service-Disabled Veteran-Owned"],
                "A2": ["Woman Owned"],
                "XX": ["SBA Certified Small Disadvantaged Business"]
            }
            
            if set_aside in type_map:
                required_types = type_map[set_aside]
                for bt in business_types:
                    bt_code = bt.get("businessTypeCode")
                    if bt_code in required_types:
                        return 100.0  # Compliant
                
                return 0.0  # Non-compliant
        
        return 50.0  # Unknown
    
    @staticmethod
    async def _assess_attractiveness(
        db: AsyncSession,
        opportunity: Opportunity
    ) -> Dict[str, float]:
        """
        Assess Attractiveness (30% weight)
        Uses contract value and strategic fit
        """
        # Contract Value Score (0-100)
        contract_value = 50.0
        if opportunity.award:
            award_data = opportunity.award
            if isinstance(award_data, dict):
                amount = award_data.get("amount")
                if amount:
                    # Score based on contract size
                    if amount > 10_000_000:
                        contract_value = 90.0
                    elif amount > 1_000_000:
                        contract_value = 75.0
                    elif amount > 100_000:
                        contract_value = 60.0
                    else:
                        contract_value = 40.0
        
        # Strategic Alignment Score (0-100)
        strategic_alignment = 50.0
        # TODO: Implement strategic alignment based on company priorities
        # For now, use NAICS match as proxy
        profile_result = await db.execute(
            select(CompanyProfile).limit(1)
        )
        profile = profile_result.scalar_one_or_none()
        
        if profile and opportunity.naics_code:
            target_naics = profile.target_naics or []
            if opportunity.naics_code in target_naics:
                strategic_alignment = 80.0
        
        # Agency Relationship Score (0-100)
        agency_relationship = 50.0
        # TODO: Implement agency relationship tracking
        # For now, use static score
        
        # Composite Attractiveness score
        composite = (
            contract_value + 
            strategic_alignment + 
            agency_relationship
        ) / 3
        
        return {
            "contract_value": contract_value,
            "strategic_alignment": strategic_alignment,
            "agency_relationship": agency_relationship,
            "composite": composite
        }
    
    @staticmethod
    def _generate_recommendation(weighted_score: float) -> str:
        """
        Generate BID/NO_BID/REVIEW recommendation based on weighted score
        """
        if weighted_score >= 70.0:
            return "BID"
        elif weighted_score >= 50.0:
            return "REVIEW"
        else:
            return "NO_BID"
    
    @staticmethod
    async def customize_weights(
        db: AsyncSession,
        opportunity_id: int,
        position_weight: float,
        capability_weight: float,
        attractiveness_weight: float
    ) -> Dict[str, Any]:
        """
        Allow user to customize scoring weights
        Weights must sum to 1.0
        """
        total = position_weight + capability_weight + attractiveness_weight
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"Weights must sum to 1.0, got {total}")
        
        # Recalculate with custom weights
        return await QualificationService.calculate_bid_score(
            db,
            opportunity_id,
            custom_weights={
                "position": position_weight,
                "capability": capability_weight,
                "attractiveness": attractiveness_weight
            }
        )
