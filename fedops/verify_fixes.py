import asyncio
import os
import sys
from sqlalchemy import select

def log(msg):
    print(msg)
    with open("verify_fixes.txt", "a") as f:
        f.write(msg + "\n")

log("Starting verification script...")

# Add project root to path
sys.path.append(os.getcwd())

try:
    from fedops_core.db.engine import async_session
    from fedops_core.db.models import Proposal, ProposalVolume, StoredFile, Opportunity
    from fedops_core.services.proposal_content_generator import ProposalContentGenerator
    log("Imports successful")
except ImportError as e:
    log(f"Import Error: {e}")
    sys.exit(1)

async def verify():
    async with async_session() as db:
        # 1. Find a proposal
        result = await db.execute(select(Proposal).limit(1))
        proposal = result.scalar_one_or_none()
        
        if not proposal:
            log("No proposal found. Cannot test.")
            return

        log(f"Testing with Proposal ID: {proposal.id}")

        # 2. Test Past Performance Saving
        generator = ProposalContentGenerator(db)
        try:
            log("Generating Past Performance Volume...")
            # Mocking the AI generation to avoid cost/time if possible, but for integration test we'll run it
            # Actually, let's just check if the code runs and saves.
            # We'll rely on the real generation.
            
            # Ensure primary entity exists (from previous step)
            
            result = await generator.generate_past_performance_volume(proposal.id)
            if result['status'] == 'success':
                log("Generation successful.")
                
                # Verify DB save
                vol_result = await db.execute(
                    select(ProposalVolume).where(
                        ProposalVolume.proposal_id == proposal.id,
                        ProposalVolume.title.ilike("%Past Performance%")
                    )
                )
                volume = vol_result.scalar_one_or_none()
                if volume and volume.blocks:
                    log(f"SUCCESS: Past Performance saved to DB. Volume ID: {volume.id}, Blocks: {len(volume.blocks)}")
                else:
                    log("FAILURE: Past Performance NOT saved to DB.")
            else:
                log(f"Generation failed: {result.get('message')}")
        except Exception as e:
            log(f"Exception during Past Performance test: {e}")

        # 3. Test SOW Generation Fallback
        # Ensure we have a stored file without parsed content but with a real file path
        # This is hard to mock without creating files. 
        # We'll just check if the function runs without error on existing files.
        try:
            log("Generating SOW Decomposition...")
            result = await generator.generate_sow_decomposition(proposal.id)
            if result['status'] == 'success':
                log(f"SUCCESS: SOW Generation successful. Content length: {len(result['content'])}")
            else:
                log(f"SOW Generation failed: {result.get('message')}")
        except Exception as e:
            log(f"Exception during SOW test: {e}")

if __name__ == "__main__":
    # Clear log
    with open("verify_fixes.txt", "w") as f:
        f.write("")
    asyncio.run(verify())
