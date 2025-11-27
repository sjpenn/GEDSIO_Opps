import asyncio
import os
import sys
from sqlalchemy import select

def log(msg):
    with open("test_output.txt", "a") as f:
        f.write(msg + "\n")

log("Starting test script...")

# Add project root to path
sys.path.append(os.getcwd())

try:
    from fedops_core.db.engine import async_session
    from fedops_core.db.models import Proposal, Opportunity
    from fedops_core.services.proposal_content_generator import ProposalContentGenerator
    log("Imports successful")
except ImportError as e:
    log(f"Import Error: {e}")
    sys.exit(1)

async def test_generation():
    async with async_session() as db:
        # Find a proposal
        result = await db.execute(select(Proposal).limit(1))
        proposal = result.scalar_one_or_none()
        
        if not proposal:
            log("No proposal found to test with.")
            return

        log(f"Testing with Proposal ID: {proposal.id}")
        
        generator = ProposalContentGenerator(db)
        
        log("Generating Requirements Matrix...")
        try:
            result = await generator.generate_requirements_matrix(proposal.id)
            log(f"Result Status: {result['status']}")
            if result['status'] == 'error':
                log(f"Error: {result['message']}")
            else:
                log(f"Success! Content length: {len(result['content'])}")
        except Exception as e:
            log(f"Exception during generation: {e}")

if __name__ == "__main__":
    # Clear previous log
    with open("test_output.txt", "w") as f:
        f.write("")
    asyncio.run(test_generation())
