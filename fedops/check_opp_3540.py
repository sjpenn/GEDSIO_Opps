
import asyncio
from sqlalchemy import select
from fedops_core.db.engine import AsyncSessionLocal
from fedops_core.db.models import Proposal, Opportunity

async def check_opp_3540():
    async with AsyncSessionLocal() as db:
        # Check Opportunity
        result = await db.execute(select(Opportunity).where(Opportunity.id == 3540))
        opp = result.scalar_one_or_none()
        
        if opp:
            print(f"Opportunity 3540 FOUND: {opp.title}")
            print(f"  Notice ID: {opp.notice_id}")
            
            # Check Proposal
            p_result = await db.execute(select(Proposal).where(Proposal.opportunity_id == 3540))
            proposal = p_result.scalar_one_or_none()
            
            if proposal:
                print(f"Proposal FOUND: ID {proposal.id}, Version {proposal.version}")
            else:
                print("Proposal NOT FOUND")
        else:
            print("Opportunity 3540 NOT FOUND")

if __name__ == "__main__":
    asyncio.run(check_opp_3540())
