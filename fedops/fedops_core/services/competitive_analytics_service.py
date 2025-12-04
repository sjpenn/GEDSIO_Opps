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
from fedops_sources.sam_entity import SamEntityClient


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
            
            # If entity doesn't exist, create it so we can link via foreign key
            if not entity:
                entity = Entity(
                    uei=competitor["uei"],
                    legal_business_name=competitor["name"],
                    last_synced_at=datetime.utcnow()
                )
                db.add(entity)
                await db.flush()  # Flush to ensure it's available for FK
            
            # Calculate win probability impact
            # Higher historical wins = lower win probability for us
            win_impact = max(0, 100 - (competitor["historical_wins"] * 10))
            
            intel = CompetitiveIntelligence(
                opportunity_id=opportunity_id,
                competitor_uei=competitor["uei"],
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
    
    BUSINESS_TYPE_MAPPING = {
        "2X": "For Profit Organization",
        "23": "Minority Owned Business",
        "27": "Self Certified Small Disadvantaged Business",
        "8W": "Women Owned Small Business",
        "A6": "SBA Certified 8(a) Program Participant",
        "QF": "Service Disabled Veteran Owned Business",
        "VN": "Contracts",
        "XS": "S Corporation",
        "MF": "Manufacturer of Goods",
        "VW": "Contracts and Grants",
        "A2": "Women Owned Business",
        "NB": "Small Business",
        "LJ": "Limited Liability Company",
        "L2": "Limited Liability Company",
        "K6": "Indian Tribe (Federally Recognized)",
        "HQ": "DoD SkillBridge Partner",
        "A5": "Veteran Owned Business",
        "XX": "Small Disadvantaged Business",
        "OY": "Black American Owned",
        "PI": "Hispanic American Owned",
        "12": "Other Computer Related Services", # Not a business type but sometimes appears? No, these are usually 2 chars.
        "F": "For Profit Organization", # Legacy?
        "20": "For Profit Organization",
        "XS": "S Corporation",
        "M8": "Educational Institution",
        "U2": "Makerspace",
        "A4": "SBA Certified Small Disadvantaged Business",
        "A7": "SBA Certified 8(a) Program Participant", # Another code?
        "A8": "Nonprofit Organization",
        "VG": "Federal Agency",
        "2F": "Sole Proprietorship",
        "2J": "Sole Proprietorship",
        "2K": "Partnership or Limited Liability Partnership",
        "2L": "Corporate Entity (Not Tax Exempt)",
        "2M": "Corporate Entity (Tax Exempt)",
        "2N": "U.S. Government Entity",
        "2O": "Foreign Government",
        "2P": "International Organization",
        "2Q": "Other",
        "2R": "Council of Governments",
        "2S": "Planning Commission",
        "2T": "Interstate Entity",
        "2U": "Housing Authorities Public/Tribal",
        "2V": "Transit Authority",
        "2W": "Subchapter S Corporation",
        "2Y": "Limited Liability Company",
        "2Z": "Joint Venture",
        "3A": "Limited Liability Partnership",
        "3B": "Limited Partnership",
        "3C": "Subchapter S Corporation",
        "3D": "Limited Liability Company",
        "3E": "Corporation",
        "3F": "Partnership",
        "3G": "Sole Proprietorship",
        "3H": "Nonprofit",
        "3I": "Other",
        "3J": "Limited Liability Company",
        "3K": "Partnership",
        "3L": "Sole Proprietorship",
        "3M": "Nonprofit",
        "3N": "Other",
        "3O": "Limited Liability Company",
        "3P": "Partnership",
        "3Q": "Sole Proprietorship",
        "3R": "Nonprofit",
        "3S": "Other",
        "3T": "Limited Liability Company",
        "3U": "Partnership",
        "3V": "Sole Proprietorship",
        "3W": "Nonprofit",
        "3X": "Other",
        "3Y": "Limited Liability Company",
        "3Z": "Partnership",
        "4A": "Sole Proprietorship",
        "4B": "Nonprofit",
        "4C": "Other",
        "4D": "Limited Liability Company",
        "4E": "Partnership",
        "4F": "Sole Proprietorship",
        "4G": "Nonprofit",
        "4H": "Other",
        "4I": "Limited Liability Company",
        "4J": "Partnership",
        "4K": "Sole Proprietorship",
        "4L": "Nonprofit",
        "4M": "Other",
        "4N": "Limited Liability Company",
        "4O": "Partnership",
        "4P": "Sole Proprietorship",
        "4Q": "Nonprofit",
        "4R": "Other",
        "4S": "Limited Liability Company",
        "4T": "Partnership",
        "4U": "Sole Proprietorship",
        "4V": "Nonprofit",
        "4W": "Other",
        "4X": "Limited Liability Company",
        "4Y": "Partnership",
        "4Z": "Sole Proprietorship",
        "5A": "Nonprofit",
        "5B": "Other",
        "5C": "Limited Liability Company",
        "5D": "Partnership",
        "5E": "Sole Proprietorship",
        "5F": "Nonprofit",
        "5G": "Other",
        "5H": "Limited Liability Company",
        "5I": "Partnership",
        "5J": "Sole Proprietorship",
        "5K": "Nonprofit",
        "5L": "Other",
        "5M": "Limited Liability Company",
        "5N": "Partnership",
        "5O": "Sole Proprietorship",
        "5P": "Nonprofit",
        "5Q": "Other",
        "5R": "Limited Liability Company",
        "5S": "Partnership",
        "5T": "Sole Proprietorship",
        "5U": "Nonprofit",
        "5V": "Other",
        "5W": "Limited Liability Company",
        "5X": "Partnership",
        "5Y": "Sole Proprietorship",
        "5Z": "Nonprofit",
        "6A": "Other",
        "6B": "Limited Liability Company",
        "6C": "Partnership",
        "6D": "Sole Proprietorship",
        "6E": "Nonprofit",
        "6F": "Other",
        "6G": "Limited Liability Company",
        "6H": "Partnership",
        "6I": "Sole Proprietorship",
        "6J": "Nonprofit",
        "6K": "Other",
        "6L": "Limited Liability Company",
        "6M": "Partnership",
        "6N": "Sole Proprietorship",
        "6O": "Nonprofit",
        "6P": "Other",
        "6Q": "Limited Liability Company",
        "6R": "Partnership",
        "6S": "Sole Proprietorship",
        "6T": "Nonprofit",
        "6U": "Other",
        "6V": "Limited Liability Company",
        "6W": "Partnership",
        "6X": "Sole Proprietorship",
        "6Y": "Nonprofit",
        "6Z": "Other",
        "7A": "Limited Liability Company",
        "7B": "Partnership",
        "7C": "Sole Proprietorship",
        "7D": "Nonprofit",
        "7E": "Other",
        "7F": "Limited Liability Company",
        "7G": "Partnership",
        "7H": "Sole Proprietorship",
        "7I": "Nonprofit",
        "7J": "Other",
        "7K": "Limited Liability Company",
        "7L": "Partnership",
        "7M": "Sole Proprietorship",
        "7N": "Nonprofit",
        "7O": "Other",
        "7P": "Limited Liability Company",
        "7Q": "Partnership",
        "7R": "Sole Proprietorship",
        "7S": "Nonprofit",
        "7T": "Other",
        "7U": "Limited Liability Company",
        "7V": "Partnership",
        "7W": "Sole Proprietorship",
        "7X": "Nonprofit",
        "7Y": "Other",
        "7Z": "Limited Liability Company",
        "8A": "Partnership",
        "8B": "Sole Proprietorship",
        "8C": "Nonprofit",
        "8D": "Other",
        "8E": "Limited Liability Company",
        "8F": "Partnership",
        "8G": "Sole Proprietorship",
        "8H": "Nonprofit",
        "8I": "Other",
        "8J": "Limited Liability Company",
        "8K": "Partnership",
        "8L": "Sole Proprietorship",
        "8M": "Nonprofit",
        "8N": "Other",
        "8O": "Limited Liability Company",
        "8P": "Partnership",
        "8Q": "Sole Proprietorship",
        "8R": "Nonprofit",
        "8S": "Other",
        "8T": "Limited Liability Company",
        "8U": "Partnership",
        "8V": "Sole Proprietorship",
        "8W": "Nonprofit",
        "8X": "Other",
        "8Y": "Limited Liability Company",
        "8Z": "Partnership",
        "9A": "Sole Proprietorship",
        "9B": "Nonprofit",
        "9C": "Other",
        "9D": "Limited Liability Company",
        "9E": "Partnership",
        "9F": "Sole Proprietorship",
        "9G": "Nonprofit",
        "9H": "Other",
        "9I": "Limited Liability Company",
        "9J": "Partnership",
        "9K": "Sole Proprietorship",
        "9L": "Nonprofit",
        "9M": "Other",
        "9N": "Limited Liability Company",
        "9O": "Partnership",
        "9P": "Sole Proprietorship",
        "9Q": "Nonprofit",
        "9R": "Other",
        "9S": "Limited Liability Company",
        "9T": "Partnership",
        "9U": "Sole Proprietorship",
        "9V": "Nonprofit",
        "9W": "Other",
        "9X": "Limited Liability Company",
        "9Y": "Partnership",
        "9Z": "Sole Proprietorship"
    }

    @staticmethod
    async def fetch_entity_data(competitor_uei: str) -> Optional[Dict[str, Any]]:
        """
        Fetch detailed entity data from SAM.gov
        """
        try:
            sam_client = SamEntityClient()
            entity_data = await sam_client.get_entity(competitor_uei)
            
            if not entity_data:
                return None
            
            # Extract relevant fields from SAM.gov response
            # Structure can vary, so we check multiple locations
            entity_registration = entity_data.get('entityRegistration', {})
            core_data = entity_data.get('coreData', {})
            assertions = entity_data.get('assertions', {})
            
            # legalBusinessName is usually in entityRegistration
            legal_name = entity_registration.get('legalBusinessName') or core_data.get('legalBusinessName') or ''
            
            # DBA name
            dba_name = entity_registration.get('dbaName') or core_data.get('dbaName') or ''
            
            # NAICS codes are usually in assertions -> goodsAndServices -> naicsList
            # OR in coreData -> generalInformation -> naicsCode
            naics_list = []
            if 'goodsAndServices' in assertions:
                naics_list = assertions['goodsAndServices'].get('naicsList', [])
            elif 'naicsList' in core_data:
                naics_list = core_data.get('naicsList', [])
                
            # Business types
            business_types = []
            if 'businessTypes' in entity_registration:
                business_types = entity_registration.get('businessTypes', {}).get('businessTypeList', [])
            elif 'businessTypes' in core_data:
                business_types = core_data.get('businessTypes', {}).get('businessTypeList', [])
            elif 'businessTypes' in assertions:
                business_types = assertions.get('businessTypes', {}).get('businessTypeList', [])
                
            # Flatten business types if they are objects and deduplicate
            formatted_business_types = []
            seen_bt_codes = set()
            
            for bt in business_types:
                if isinstance(bt, dict):
                    code = bt.get('businessTypeCode', '')
                    # Try to get description from API, then mapping, then fallback to code
                    desc = bt.get('businessTypeDescription')
                    if not desc:
                        desc = CompetitiveAnalyticsService.BUSINESS_TYPE_MAPPING.get(code, code)
                    
                    if code and code not in seen_bt_codes:
                        seen_bt_codes.add(code)
                        formatted_business_types.append({
                            "code": code,
                            "description": desc
                        })
                else:
                    # If it's just a string
                    code = str(bt)
                    desc = CompetitiveAnalyticsService.BUSINESS_TYPE_MAPPING.get(code, code)
                    
                    if code not in seen_bt_codes:
                        seen_bt_codes.add(code)
                        formatted_business_types.append({
                            "code": code,
                            "description": desc
                        })
            
            # Sort by description
            formatted_business_types.sort(key=lambda x: x['description'])
            
            # Deduplicate NAICS codes
            seen_naics = set()
            unique_naics = []
            for naics in naics_list:
                code = naics.get('naicsCode')
                if code and code not in seen_naics:
                    seen_naics.add(code)
                    unique_naics.append({
                        "code": code,
                        "description": naics.get('naicsDescription'),
                        "is_primary": naics.get('isPrimary', False)
                    })
            
            # Extract PSC codes
            psc_list = []
            if 'goodsAndServices' in assertions:
                psc_list = assertions['goodsAndServices'].get('pscList', [])
            elif 'pscList' in core_data.get('generalInformation', {}):
                 psc_list = core_data['generalInformation'].get('pscList', [])
            
            unique_psc = []
            seen_psc = set()
            for psc in psc_list:
                code = psc.get('pscCode')
                if code and code not in seen_psc:
                    seen_psc.add(code)
                    unique_psc.append({
                        "code": code,
                        "description": psc.get('pscDescription')
                    })

            return {
                "uei": competitor_uei,
                "legal_business_name": legal_name,
                "dba_name": dba_name,
                "naics_codes": unique_naics,
                "psc_codes": unique_psc,
                "business_types": formatted_business_types,
                "company_division": entity_registration.get('companyDivision', ''),
                "division_number": entity_registration.get('divisionNumber', ''),
                "registration_status": entity_registration.get('registrationStatus', ''),
                "registration_date": entity_registration.get('registrationDate', ''),
                "expiration_date": entity_registration.get('expirationDate', '')
            }
        except Exception as e:
            print(f"Error fetching SAM.gov entity data for {competitor_uei}: {e}")
            return None
    
    @staticmethod
    async def enrich_competitor_profile(
        db: AsyncSession,
        competitor_uei: str,
        naics_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate enriched competitor profile combining USAspending + SAM.gov data
        """
        # Fetch USAspending awards data
        awards = await CompetitiveAnalyticsService.fetch_usaspending_awards(
            naics_code=naics_code,
            limit=200
        )
        
        # Filter to this competitor
        competitor_awards = [
            a for a in awards 
            if a.get("Recipient UEI") == competitor_uei
        ]
        
        total_value = sum(a.get("Award Amount", 0) for a in competitor_awards) if competitor_awards else 0
        naics_codes = list(set(a.get("NAICS Code") for a in competitor_awards if a.get("NAICS Code")))
        
        # Base profile from USAspending
        profile = {
            "uei": competitor_uei,
            "name": competitor_awards[0].get("Recipient Name", "Unknown") if competitor_awards else "Unknown",
            "total_awards": len(competitor_awards),
            "total_value": total_value,
            "average_award_size": total_value / len(competitor_awards) if competitor_awards else 0,
            "naics_codes": naics_codes,
            "recent_awards": competitor_awards[:5]
        }
        
        # Enrich with SAM.gov entity data
        entity_data = await CompetitiveAnalyticsService.fetch_entity_data(competitor_uei)
        if entity_data:
            profile["entity_data"] = entity_data
        
        return profile
    
    @staticmethod
    async def profile_competitor(
        db: AsyncSession,
        competitor_uei: str,
        naics_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate detailed profile for a specific competitor
        (Kept for backward compatibility, delegates to enrich_competitor_profile)
        """
        return await CompetitiveAnalyticsService.enrich_competitor_profile(
            db, competitor_uei, naics_code
        )
