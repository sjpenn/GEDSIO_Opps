
import asyncio
from sqlalchemy import select
from fedops_core.db.engine import AsyncSessionLocal
from fedops_core.db.models import Proposal, Opportunity

async def check_proposals():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Proposal))
        proposals = result.scalars().all()
        print(f"Found {len(proposals)} proposals:")
        for p in proposals:
            print(f"ID: {p.id}, Opportunity ID: {p.opportunity_id}, Version: {p.version}")
            
            # Check opportunity
            opp_result = await db.execute(select(Opportunity).where(Opportunity.id == p.opportunity_id))
            opp = opp_result.scalar_one_or_none()
            if opp:
                print(f"  Opportunity: {opp.title} (ID: {opp.id})")
            else:
                print(f"  Opportunity not found!")

if __name__ == "__main__":
    asyncio.run(check_proposals())
