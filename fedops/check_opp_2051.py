
import asyncio
from sqlalchemy import select
from fedops_core.db.engine import AsyncSessionLocal
from fedops_core.db.models import Proposal, Opportunity, StoredFile

async def check_opp_2051():
    async with AsyncSessionLocal() as db:
        # Check if opportunity 2051 exists
        opp_result = await db.execute(select(Opportunity).where(Opportunity.id == 2051))
        opp = opp_result.scalar_one_or_none()
        
        if not opp:
            print("Opportunity 2051 not found!")
            return
            
        print(f"Opportunity 2051: {opp.title}")
        print(f"Notice ID: {opp.notice_id}")
        
        # Check for proposal
        prop_result = await db.execute(select(Proposal).where(Proposal.opportunity_id == 2051))
        proposal = prop_result.scalar_one_or_none()
        
        if proposal:
            print(f"\nProposal ID: {proposal.id}, Version: {proposal.version}")
        else:
            print("\nNo proposal found for this opportunity!")
            
        # Check for files
        files_result = await db.execute(select(StoredFile).where(StoredFile.opportunity_id == 2051))
        files = files_result.scalars().all()
        
        print(f"\nFiles: {len(files)}")
        for f in files:
            parsed_len = len(f.parsed_content) if f.parsed_content else 0
            print(f"  - {f.filename}")
            print(f"    Parsed: {parsed_len} chars, Type: {f.file_type}")

if __name__ == "__main__":
    asyncio.run(check_opp_2051())
