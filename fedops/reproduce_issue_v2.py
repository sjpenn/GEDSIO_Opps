
import asyncio
import os
from sqlalchemy import select
from fedops_core.db.engine import AsyncSessionLocal
from fedops_core.db.models import Proposal, Opportunity, StoredFile
from fedops_core.services.requirement_extraction_service import RequirementExtractionService
from fedops_api.routers.proposals import generate_proposal
from fastapi import BackgroundTasks

async def reproduce():
    async with AsyncSessionLocal() as db:
        # 1. Find an opportunity that has files
        result = await db.execute(
            select(Opportunity)
            .join(StoredFile, Opportunity.id == StoredFile.opportunity_id)
            .limit(1)
        )
        opp = result.scalar_one_or_none()
        if not opp:
            print("No opportunities found!")
            return
        
        print(f"Using Opportunity: {opp.title} (ID: {opp.id})")
        
        # 2. Check if proposal exists, if not create one
        result = await db.execute(select(Proposal).where(Proposal.opportunity_id == opp.id))
        proposal = result.scalar_one_or_none()
        
        if not proposal:
            print("Creating new proposal...")
            # We can't easily call the router function because it expects BackgroundTasks
            # So we'll manually create it
            proposal = Proposal(opportunity_id=opp.id)
            db.add(proposal)
            await db.commit()
            await db.refresh(proposal)
            print(f"Created Proposal ID: {proposal.id}")
        else:
            print(f"Using existing Proposal ID: {proposal.id}")
            
        # 3. Trigger Extraction
        print("Triggering extraction...")
        service = RequirementExtractionService(db)
        try:
            result = await service.extract_requirements_from_proposal(proposal.id)
            print("Extraction Result:", result)
        except Exception as e:
            print(f"Extraction Failed: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(reproduce())
