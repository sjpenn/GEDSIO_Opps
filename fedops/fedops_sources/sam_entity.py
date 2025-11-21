import httpx
from typing import Optional, Dict, Any
from fedops_core.settings import settings

class SamEntityClient:
    BASE_URL = "https://api.sam.gov/entity-information/v3/entities"

    def __init__(self):
        self.api_key = settings.SAM_API_KEY

    async def get_entity(self, uei: str) -> Optional[Dict[str, Any]]:
        if not self.api_key:
            print("Warning: SAM_API_KEY not set")
            return None

        params = {
            "api_key": self.api_key,
            "ueiSAM": uei,
            "includeSections": "entityRegistration,coreData,assertions,repsAndCerts,pointsOfContact"
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(self.BASE_URL, params=params)
                response.raise_for_status()
                data = response.json()
                # SAM API structure is a bit deep, usually data['entityData'] or similar
                # We might need to adjust based on actual response
                if data and isinstance(data, list) and len(data) > 0:
                     return data[0] # Assuming list of matches
                return data
            except httpx.HTTPStatusError as e:
                print(f"Error fetching entity {uei}: {e}")
                return None
            except Exception as e:
                print(f"Unexpected error fetching entity {uei}: {e}")
                return None

    async def search_entities(self, legal_business_name: str) -> Dict[str, Any]:
         if not self.api_key:
            print("Warning: SAM_API_KEY not set")
            return {}
         
         # Note: Search might use a different endpoint or parameters
         # For V3, it uses 'legalBusinessName'
         params = {
            "api_key": self.api_key,
            "legalBusinessName": legal_business_name
        }
         
         async with httpx.AsyncClient() as client:
            try:
                response = await client.get(self.BASE_URL, params=params)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                print(f"Error searching entities: {e}")
                return {}
