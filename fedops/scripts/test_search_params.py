import asyncio
import os
import httpx
import json
from datetime import datetime, timedelta

# Mock settings if needed, or just use env vars
SAM_API_KEY = os.environ.get("SAM_API_KEY")

async def test_usaspending_keyword(keyword):
    print(f"\n--- Testing USASpending for '{keyword}' ---")
    url = "https://api.usaspending.gov/api/v2/search/spending_by_award/"
    
    payload = {
        "filters": {
            "keywords": [keyword],
            "award_type_codes": ["A", "B", "C", "D"],
            "time_period": [{"start_date": "2020-01-01", "end_date": "2024-12-31"}]
        },
        "fields": ["Award ID", "Recipient Name", "Description", "Award Amount"],
        "limit": 5
    }
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(url, json=payload)
            print(f"Status: {resp.status_code}")
            if resp.status_code == 200:
                data = resp.json()
                results = data.get("results", [])
                print(f"Found {len(results)} results")
                for r in results:
                    print(f"  - {r.get('Award ID')}: {r.get('Description')} ({r.get('Recipient Name')})")
            else:
                print(resp.text)
        except Exception as e:
            print(f"Error: {e}")

async def test_sam_keyword(keyword):
    print(f"\n--- Testing SAM.gov for '{keyword}' ---")
    if not SAM_API_KEY:
        print("Skipping SAM test - No API Key")
        return

    url = "https://api.sam.gov/opportunities/v2/search"
    params = {
        "api_key": SAM_API_KEY,
        "title": keyword,
        "limit": 5,
        "postedFrom": (datetime.now() - timedelta(days=365)).strftime("%m/%d/%Y"),
        "postedTo": datetime.now().strftime("%m/%d/%Y")
    }
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url, params=params)
            print(f"Status: {resp.status_code}")
            if resp.status_code == 200:
                data = resp.json()
                opps = data.get("opportunitiesData", [])
                print(f"Found {len(opps)} results")
                for o in opps:
                    print(f"  - {o.get('solicitationNumber')}: {o.get('title')}")
            else:
                print(resp.text)
        except Exception as e:
            print(f"Error: {e}")

async def main():
    keyword = "Cloud"
    await test_usaspending_keyword(keyword)
    await test_sam_keyword(keyword)

if __name__ == "__main__":
    asyncio.run(main())
