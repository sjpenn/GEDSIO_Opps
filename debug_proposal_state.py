import asyncio
import os
import sys
from sqlalchemy import select
from sqlalchemy.orm import selectinload

# Add project root to path
sys.path.append(os.path.join(os.getcwd(), 'fedops'))

from fedops_core.db.engine import get_db_context
from fedops_core.db.models import Proposal, Opportunity, StoredFile, ProposalRequirement

async def check_proposal_state(proposal_id):
    with open('debug_output.txt', 'w') as f:
        def log(msg):
            print(msg)
            f.write(msg + '\n')
            
        async with get_db_context() as db:
            log(f"Checking Proposal ID: {proposal_id}")
            
            # Get Proposal
            result = await db.execute(select(Proposal).where(Proposal.id == proposal_id))
            proposal = result.scalar_one_or_none()
            
            if not proposal:
                log("❌ Proposal not found!")
                return
            
            log(f"✅ Proposal found. Opportunity ID: {proposal.opportunity_id}")
            
            # Get Opportunity
            result = await db.execute(select(Opportunity).where(Opportunity.id == proposal.opportunity_id))
            opportunity = result.scalar_one_or_none()
            
            if not opportunity:
                log("❌ Opportunity not found!")
            else:
                log(f"✅ Opportunity found: {opportunity.title}")
                
            # Get Stored Files
            result = await db.execute(select(StoredFile).where(StoredFile.opportunity_id == proposal.opportunity_id))
            files = result.scalars().all()
            
            log(f"Found {len(files)} stored files:")
            for file in files:
                content_len = len(file.parsed_content) if file.parsed_content else 0
                file_exists = os.path.exists(file.file_path) if file.file_path else False
                log(f"  - {file.filename} (ID: {file.id})")
                log(f"    - Path: {file.file_path} (Exists: {file_exists})")
                log(f"    - Parsed Content Length: {content_len}")
                
            # Get Requirements
            result = await db.execute(select(ProposalRequirement).where(ProposalRequirement.proposal_id == proposal_id))
            requirements = result.scalars().all()
            
            log(f"Found {len(requirements)} requirements.")
            for r in requirements[:5]:
                log(f"  - [{r.requirement_type}] {r.requirement_text[:50]}...")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python debug_proposal_state.py <proposal_id>")
        sys.exit(1)
    
    proposal_id = int(sys.argv[1])
    asyncio.run(check_proposal_state(proposal_id))
