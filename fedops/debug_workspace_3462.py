import asyncio
import sys
import os

# Add the project root to the python path
sys.path.append(os.getcwd())

from fedops_core.db.engine import AsyncSessionLocal
from fedops_core.db.models import Proposal
from sqlalchemy import select

async def check_proposal_id():
    async with AsyncSessionLocal() as db:
        print("Checking if 3462 is a Proposal ID...")
        result = await db.execute(select(Proposal).where(Proposal.id == 3462))
        prop = result.scalar_one_or_none()
        
        if prop:
            print(f"✅ Found Proposal with ID 3462! Associated Opportunity ID: {prop.opportunity_id}")
        else:
            print("❌ No Proposal found with ID 3462")

if __name__ == "__main__":
    asyncio.run(check_proposal_id())
