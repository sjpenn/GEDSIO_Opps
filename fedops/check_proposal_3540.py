
import asyncio
from sqlalchemy import select
from fedops_core.db.engine import AsyncSessionLocal
from fedops_core.db.models import Proposal, Opportunity

async def check_proposal_for_opp():
    async with AsyncSessionLocal() as db:
        # Check if opportunity 3540 exists
        opp_result = await db.execute(select(Opportunity).where(Opportunity.id == 3540))
        opp = opp_result.scalar_one_or_none()
        
        if not opp:
            print("Opportunity 3540 does NOT exist")
            return
            
        print(f"Opportunity 3540 EXISTS: {opp.title}")
        
        # Check if proposal exists for this opportunity
        prop_result = await db.execute(select(Proposal).where(Proposal.opportunity_id == 3540))
        proposal = prop_result.scalar_one_or_none()
        
        if proposal:
            print(f"Proposal EXISTS: ID={proposal.id}, Version={proposal.version}")
        else:
            print("Proposal does NOT exist for this opportunity")
            print("You need to generate a proposal first from the Analysis page")

if __name__ == "__main__":
    asyncio.run(check_proposal_for_opp())
