import asyncio
import os
import sys
from sqlalchemy import select

def log(msg):
    print(msg)

# Add project root to path
sys.path.append(os.getcwd())

try:
    from fedops_core.db.engine import AsyncSessionLocal
    from fedops_core.db.models import Proposal, Opportunity
    from fedops_core.services.proposal_content_generator import ProposalContentGenerator
    log("Imports successful")
except ImportError as e:
    log(f"Import Error: {e}")
    sys.exit(1)

async def test_sources_sought_generation():
    async with AsyncSessionLocal() as db:
        # Find a proposal
        result = await db.execute(select(Proposal).limit(1))
        proposal = result.scalar_one_or_none()
        
        if not proposal:
            log("No proposal found to test with.")
            return

        log(f"Testing with Proposal ID: {proposal.id}")
        
        generator = ProposalContentGenerator(db)
        
        log("Generating Sources Sought Response...")
        try:
            result = await generator.generate_sources_sought_response(proposal.id)
            log(f"Result Status: {result['status']}")
            if result['status'] == 'error':
                log(f"Error: {result['message']}")
            else:
                log(f"Success! Content length: {len(result['content'])}")
                log("Generated Content Preview:")
                log(result['content'][:500] + "...")
        except Exception as e:
            log(f"Exception during generation: {e}")

if __name__ == "__main__":
    asyncio.run(test_sources_sought_generation())
