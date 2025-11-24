import httpx
from typing import Optional, Dict, Any, List
from fedops_core.settings import settings

class SamOpportunitiesClient:
    BASE_URL = "https://api.sam.gov/opportunities/v2/search"

    def __init__(self):
        self.api_key = settings.SAM_API_KEY

    async def get_opportunity_by_solicitation_id(self, solicitation_id: str) -> Optional[Dict[str, Any]]:
        if not self.api_key:
            print("Warning: SAM_API_KEY not set")
            return None

        # SAM.gov Opportunities API search parameters
        # We use 'solicitationNumber' to find the opportunity
        params = {
            "api_key": self.api_key,
            "solicitationNumber": solicitation_id,
            "limit": 1,
            "postedFrom": "01/01/2000", # Broad range to find old awards
            "postedTo": "12/31/2099"
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(self.BASE_URL, params=params)
                response.raise_for_status()
                data = response.json()
                
                if "opportunitiesData" in data and len(data["opportunitiesData"]) > 0:
                    return data["opportunitiesData"][0]
                return None
            except httpx.HTTPStatusError as e:
                print(f"Error fetching opportunity {solicitation_id}: {e}")
                return None
            except Exception as e:
                print(f"Unexpected error fetching opportunity {solicitation_id}: {e}")
                return None

    async def get_opportunity_by_id(self, notice_id: str) -> Optional[Dict[str, Any]]:
        # If we have the internal SAM noticeId
        if not self.api_key:
            return None
            
        url = f"https://api.sam.gov/opportunities/v2/search/{notice_id}"
        params = {"api_key": self.api_key}
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, params=params)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                print(f"Error fetching opportunity by ID {notice_id}: {e}")
                return None
