
import asyncio
from sqlalchemy import select
from fedops_core.db.engine import AsyncSessionLocal
from fedops_core.db.models import Proposal, Opportunity, StoredFile

async def check_proposal_5():
    async with AsyncSessionLocal() as db:
        # Get proposal 5
        result = await db.execute(select(Proposal).where(Proposal.id == 5))
        proposal = result.scalar_one_or_none()
        
        if not proposal:
            print("Proposal 5 not found!")
            return
            
        print(f"Proposal 5: opportunity_id={proposal.opportunity_id}, version={proposal.version}")
        
        # Get opportunity
        opp_result = await db.execute(select(Opportunity).where(Opportunity.id == proposal.opportunity_id))
        opp = opp_result.scalar_one_or_none()
        
        if opp:
            print(f"Opportunity: {opp.title}")
            print(f"Notice ID: {opp.notice_id}")
            
        # Get files
        files_result = await db.execute(select(StoredFile).where(StoredFile.opportunity_id == proposal.opportunity_id))
        files = files_result.scalars().all()
        
        print(f"\nFiles for this opportunity: {len(files)}")
        for f in files:
            print(f"  - {f.filename} (parsed: {len(f.parsed_content) if f.parsed_content else 0} chars)")

if __name__ == "__main__":
    asyncio.run(check_proposal_5())
