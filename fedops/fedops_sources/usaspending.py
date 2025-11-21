import httpx
from typing import List, Dict, Any

class USASpendingClient:
    BASE_URL = "https://api.usaspending.gov/api/v2"

    async def get_awards_by_uei(self, uei: str, limit: int = 10) -> List[Dict[str, Any]]:
        endpoint = "/search/spending_by_award/"
        url = f"{self.BASE_URL}{endpoint}"
        
        payload = {
            "filters": {
                "recipient_search_text": [uei],
                "award_type_codes": ["A", "B", "C", "D"] # Contracts
            },
            "fields": [
                "Award ID",
                "Recipient Name",
                "Start Date",
                "End Date",
                "Award Amount",
                "Description",
                "Awarding Agency",
                "Place of Performance City Name",
                "Place of Performance State Code",
                "Place of Performance ZIP Code",
                "Place of Performance Country Code"
            ],
            "limit": limit,
            "page": 1
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
                return data.get("results", [])
            except httpx.HTTPStatusError as e:
                print(f"Error fetching awards for {uei}: {e}")
                return []
            except Exception as e:
                print(f"Unexpected error fetching awards for {uei}: {e}")
                return []
