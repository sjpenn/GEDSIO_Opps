"""
Competitive Analytics Service
Integrates with USAspending.gov API to fetch historical award data
for competitive intelligence and win probability analysis
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import httpx

from fedops_core.db.models import Opportunity, Entity
from fedops_core.db.shipley_models import CompetitiveIntelligence
from fedops_core.settings import settings


class CompetitiveAnalyticsService:
    """Service to fetch and analyze competitive intelligence from USAspending"""
    
    USASPENDING_BASE_URL = "https://api.usaspending.gov/api/v2"
    
    @staticmethod
    async def fetch_usaspending_awards(
        naics_code: Optional[str] = None,
        agency_code: Optional[str] = None,
        set_aside: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Query USAspending API for historical awards
        Uses FPDS File D1 data for contract awards
        """
        url = f"{CompetitiveAnalyticsService.USASPENDING_BASE_URL}/search/spending_by_award/"
        
        # Build filters
        filters = {
            "award_type_codes": ["A", "B", "C", "D"],  # Contract types
            "time_period": [
                {
                    "start_date": (datetime.now() - timedelta(days=1095)).strftime("%Y-%m-%d"),  # 3 years
                    "end_date": datetime.now().strftime("%Y-%m-%d")
                }
            ]
        }
        
        if naics_code:
            filters["naics_codes"] = [naics_code]
        
        if agency_code:
            filters["agencies"] = [{"type": "awarding", "tier": "toptier", "name": agency_code}]
        
        if set_aside:
            filters["set_aside_type"] = [set_aside]
        
        payload = {
            "filters": filters,
            "fields": [
                "Award ID",
                "Recipient Name",
                "Recipient UEI",
                "Award Amount",
                "Start Date",
                "End Date",
                "Awarding Agency",
                "NAICS Code",
                "NAICS Description",
                "Award Type",
                "Contract Award Type"
            ],
            "limit": limit,
            "page": 1,
            "sort": "Award Amount",
            "order": "desc"
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
                return data.get("results", [])
        except Exception as e:
            print(f"Error fetching USAspending data: {e}")
            return []
    
    @staticmethod
    async def identify_competitors(
        db: AsyncSession,
        opportunity_id: int
    ) -> List[Dict[str, Any]]:
        """
        Identify competitors based on historical awards for similar opportunities
        """
        # Get opportunity
        result = await db.execute(
            select(Opportunity).where(Opportunity.id == opportunity_id)
        )
        opportunity = result.scalar_one_or_none()
        
        if not opportunity:
            raise ValueError(f"Opportunity {opportunity_id} not found")
        
        # Fetch historical awards
        awards = await CompetitiveAnalyticsService.fetch_usaspending_awards(
            naics_code=opportunity.naics_code,
            agency_code=opportunity.department,
            set_aside=opportunity.type_of_set_aside
        )
        
        # Aggregate by recipient
        competitor_map = {}
        
        for award in awards:
            recipient_uei = award.get("Recipient UEI")
            recipient_name = award.get("Recipient Name", "Unknown")
            award_amount = award.get("Award Amount", 0)
            
            if not recipient_uei:
                continue
            
            if recipient_uei not in competitor_map:
                competitor_map[recipient_uei] = {
                    "uei": recipient_uei,
                    "name": recipient_name,
                    "historical_wins": 0,
                    "total_obligation": 0,
                    "awards": []
                }
            
            competitor_map[recipient_uei]["historical_wins"] += 1
            competitor_map[recipient_uei]["total_obligation"] += award_amount
            competitor_map[recipient_uei]["awards"].append({
                "award_id": award.get("Award ID"),
                "amount": award_amount,
                "start_date": award.get("Start Date"),
                "naics_code": award.get("NAICS Code")
            })
        
        # Convert to list and sort by total obligation
        competitors = list(competitor_map.values())
        competitors.sort(key=lambda x: x["total_obligation"], reverse=True)
        
        return competitors
    
    @staticmethod
    async def update_competitive_intelligence(
        db: AsyncSession,
        opportunity_id: int
    ) -> Dict[str, Any]:
        """
        Update competitive intelligence data for an opportunity
        Fetches from USAspending and stores in database
        """
        # Get opportunity
        result = await db.execute(
            select(Opportunity).where(Opportunity.id == opportunity_id)
        )
        opportunity = result.scalar_one_or_none()
        
        if not opportunity:
            raise ValueError(f"Opportunity {opportunity_id} not found")
        
        # Identify competitors
        competitors = await CompetitiveAnalyticsService.identify_competitors(
            db, opportunity_id
        )
        
        # Clear existing competitive intelligence
        await db.execute(
            select(CompetitiveIntelligence).where(
                CompetitiveIntelligence.opportunity_id == opportunity_id
            )
        )
        existing = (await db.execute(
            select(CompetitiveIntelligence).where(
                CompetitiveIntelligence.opportunity_id == opportunity_id
            )
        )).scalars().all()
        
        for item in existing:
            await db.delete(item)
        
        # Determine incumbent (most wins or highest total obligation)
        incumbent_uei = None
        if competitors:
            incumbent_uei = competitors[0]["uei"]
        
        # Store new competitive intelligence
        stored_count = 0
        for competitor in competitors[:10]:  # Store top 10 competitors
            # Check if entity exists in our database
            entity_result = await db.execute(
                select(Entity).where(Entity.uei == competitor["uei"])
            )
            entity = entity_result.scalar_one_or_none()
            
            # Calculate win probability impact
            # Higher historical wins = lower win probability for us
            win_impact = max(0, 100 - (competitor["historical_wins"] * 10))
            
            intel = CompetitiveIntelligence(
                opportunity_id=opportunity_id,
                competitor_uei=competitor["uei"] if entity else None,
                competitor_name=competitor["name"],
                historical_wins=competitor["historical_wins"],
                total_obligation=competitor["total_obligation"],
                win_probability_impact=win_impact,
                is_incumbent=(competitor["uei"] == incumbent_uei),
                data_source="USAspending",
                naics_match=opportunity.naics_code,
                agency_match=opportunity.department
            )
            db.add(intel)
            stored_count += 1
        
        await db.commit()
        
        return {
            "opportunity_id": opportunity_id,
            "competitors_found": len(competitors),
            "competitors_stored": stored_count,
            "incumbent_identified": incumbent_uei is not None,
            "incumbent_uei": incumbent_uei
        }
    
    @staticmethod
    async def calculate_win_probability(
        db: AsyncSession,
        opportunity_id: int
    ) -> float:
        """
        Calculate win probability based on competitive intelligence
        Returns score 0-100
        """
        # Get competitive intelligence
        result = await db.execute(
            select(CompetitiveIntelligence).where(
                CompetitiveIntelligence.opportunity_id == opportunity_id
            )
        )
        competitors = result.scalars().all()
        
        if not competitors:
            return 50.0  # Neutral if no data
        
        # Check for incumbent
        incumbent = next((c for c in competitors if c.is_incumbent), None)
        
        base_probability = 50.0
        
        if incumbent:
            # Incumbent present significantly reduces win probability
            base_probability = max(20.0, 50.0 - (incumbent.historical_wins * 5))
        else:
            # No incumbent increases win probability
            base_probability = min(80.0, 50.0 + 20.0)
        
        # Adjust based on total number of competitors
        competitor_count = len(competitors)
        if competitor_count > 5:
            base_probability *= 0.8
        elif competitor_count < 2:
            base_probability *= 1.2
        
        # Cap at 0-100
        return max(0.0, min(100.0, base_probability))
    
    @staticmethod
    async def profile_competitor(
        db: AsyncSession,
        competitor_uei: str,
        naics_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate detailed profile for a specific competitor
        """
        # Fetch awards for this competitor
        awards = await CompetitiveAnalyticsService.fetch_usaspending_awards(
            naics_code=naics_code,
            limit=200
        )
        
        # Filter to this competitor
        competitor_awards = [
            a for a in awards 
            if a.get("Recipient UEI") == competitor_uei
        ]
        
        if not competitor_awards:
            return {
                "uei": competitor_uei,
                "total_awards": 0,
                "total_value": 0,
                "average_award_size": 0,
                "naics_codes": []
            }
        
        total_value = sum(a.get("Award Amount", 0) for a in competitor_awards)
        naics_codes = list(set(a.get("NAICS Code") for a in competitor_awards if a.get("NAICS Code")))
        
        return {
            "uei": competitor_uei,
            "name": competitor_awards[0].get("Recipient Name", "Unknown"),
            "total_awards": len(competitor_awards),
            "total_value": total_value,
            "average_award_size": total_value / len(competitor_awards) if competitor_awards else 0,
            "naics_codes": naics_codes,
            "recent_awards": competitor_awards[:5]
        }
