import httpx
from typing import List, Dict, Any
from datetime import datetime, timedelta

class USASpendingClient:
    BASE_URL = "https://api.usaspending.gov/api/v2"

    async def get_awards_by_name(self, recipient_name: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Fetch awards by recipient company name (not UEI - recipient_id filter doesn't work)"""
        endpoint = "/search/spending_by_award/"
        url = f"{self.BASE_URL}{endpoint}"
        
        # Set time period to past 7 years
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7*365)  # 7 years
        
        payload = {
            "filters": {
                "recipient_search_text": [recipient_name],
                "award_type_codes": ["A", "B", "C", "D"],  # Contracts
                "time_period": [
                    {
                        "start_date": start_date.strftime("%Y-%m-%d"),
                        "end_date": end_date.strftime("%Y-%m-%d")
                    }
                ]
            },
            "fields": [
                # Basic Information
                "Award ID",
                "Recipient Name",
                "Description",
                
                # Financial Fields
                "Award Amount",
                "Total Obligation",
                "Base and All Options Value",
                "Base Exercised Options Val",
                
                # Date Fields
                "Start Date",
                "End Date",
                "Current End Date",
                "Period of Performance Start Date",
                "Period of Performance Current End Date",
                "Last Modified Date",
                
                # Contract Details
                "Award Type",
                "Contract Award Type",
                "IDV Type",
                "Contract Pricing",
                "Type of Set Aside",
                "Extent Competed",
                
                # Agency Information
                "Awarding Agency",
                "Awarding Sub Agency",
                "Funding Agency",
                "Funding Sub Agency",
                
                # Location
                "Place of Performance City Name",
                "Place of Performance State Code",
                "Place of Performance ZIP Code",
                "Place of Performance Country Code",
                "Recipient Address Line 1",
                "Recipient City Name",
                "Recipient State Code",
                "Recipient ZIP Code",
                
                # Classification
                "NAICS Code",
                "NAICS Description",
                "Product or Service Code",
                "Product or Service Code Description",
                
                # Identifiers
                "Solicitation ID",
                "Parent Award ID",
                "Referenced IDV Agency Identifier",
                "Contract Award Unique Key",
                "Recipient UEI",
                "Recipient DUNS Number",
                
                # Additional Details
                "Sub-Award Count",
                "Number of Offers Received"
            ],
            "limit": limit,
            "page": 1
        }

        print(f"[USASpending] Fetching awards for: {recipient_name}")
        print(f"[USASpending] Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
                results = data.get("results", [])
                print(f"[USASpending] Found {len(results)} awards for {recipient_name}")
                if results:
                    print(f"[USASpending] First award: {results[0].get('Award ID')} - {results[0].get('Recipient Name')}")
                return results
            except httpx.HTTPStatusError as e:
                print(f"Error fetching awards for {recipient_name}: {e}")
                return []
            except Exception as e:
                print(f"Unexpected error fetching awards for {recipient_name}: {e}")
                return []
