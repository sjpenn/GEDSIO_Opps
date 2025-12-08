"""
Script to fetch and update description text for opportunities that have URL descriptions.
This script calls the SAM.gov noticedesc endpoint to retrieve actual description text.

Run from the fedops directory:
    cd /Users/sjpenn/SitesAgents/GEDSIO_Opps/fedops
    python ../clean_descriptions.py
"""
import asyncio
import httpx
import logging
import sys
import os

# Add the fedops package to the path
sys.path.insert(0, os.path.dirname(__file__) + '/fedops')

from fedops_core.db.engine import AsyncSessionLocal
from fedops_core.db.models import Opportunity
from fedops_core.settings import settings
from sqlalchemy import select, or_

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

SAM_DESCRIPTION_API_URL = "https://api.sam.gov/prod/opportunities/v1/noticedesc"

async def fetch_description(notice_id: str, api_key: str) -> str:
    """Fetch full description text from SAM.gov notice description endpoint"""
    try:
        params = {
            "api_key": api_key,
            "noticeid": notice_id
        }
        logger.info(f"  Calling SAM.gov noticedesc API for {notice_id}...")
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(SAM_DESCRIPTION_API_URL, params=params)
            logger.info(f"  Response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                desc = data.get("description", "")
                if desc:
                    logger.info(f"  Got description: {len(desc)} chars")
                    return desc
                else:
                    logger.warning(f"  Description field was empty in response")
                    return ""
            elif response.status_code == 403:
                logger.error(f"  403 Forbidden - Check your API key!")
                return ""
            else:
                logger.warning(f"  Failed: {response.status_code}")
                try:
                    logger.warning(f"  Response: {response.text[:500]}")
                except:
                    pass
                return ""
    except httpx.TimeoutException:
        logger.error(f"  Timeout fetching description for {notice_id}")
        return ""
    except Exception as e:
        logger.error(f"  Error: {e}")
        return ""

async def main():
    print("=" * 60)
    print("SAM.gov Description Fetcher")
    print("=" * 60)
    
    if not settings.SAM_API_KEY:
        print("\nERROR: SAM_API_KEY not configured in settings!")
        print("Please set your SAM.gov API key in your environment or settings.")
        return
    
    print(f"\nUsing API key: {settings.SAM_API_KEY[:8]}...{settings.SAM_API_KEY[-4:]}")
    print(f"Description endpoint: {SAM_DESCRIPTION_API_URL}")
    
    async with AsyncSessionLocal() as session:
        # Find rows where description looks like a URL
        result = await session.execute(
            select(Opportunity).where(
                or_(
                    Opportunity.description.like('http%'),
                    Opportunity.description.like('%noticedesc%'),
                    Opportunity.description.like('%api.sam.gov%')
                )
            )
        )
        opportunities = result.scalars().all()
        
        if not opportunities:
            print("\nNo URL descriptions found in the database. All good!")
            return
        
        print(f"\nFound {len(opportunities)} opportunities with URL descriptions.\n")
        
        updated_count = 0
        failed_count = 0
        
        for i, opp in enumerate(opportunities, 1):
            print(f"[{i}/{len(opportunities)}] Opportunity ID {opp.id} (notice_id: {opp.notice_id})")
            print(f"  Current description: {opp.description[:80]}...")
            
            if opp.notice_id:
                fetched_desc = await fetch_description(opp.notice_id, settings.SAM_API_KEY)
                if fetched_desc and len(fetched_desc) > 20:
                    opp.description = fetched_desc
                    updated_count += 1
                    print(f"  SUCCESS: Updated with {len(fetched_desc)} chars")
                else:
                    # Keep the URL for now so we can debug
                    failed_count += 1
                    print(f"  FAILED: Could not fetch description")
            else:
                failed_count += 1
                print(f"  SKIPPED: No notice_id")
            
            print()
            
            # Add small delay to avoid rate limiting
            await asyncio.sleep(0.5)
        
        await session.commit()
        
        print("=" * 60)
        print(f"SUMMARY:")
        print(f"  Total processed: {len(opportunities)}")
        print(f"  Successfully updated: {updated_count}")
        print(f"  Failed/Skipped: {failed_count}")
        print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
