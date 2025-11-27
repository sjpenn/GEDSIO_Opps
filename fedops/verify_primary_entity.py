import asyncio
import os
import sys
from sqlalchemy import select

def log(msg):
    with open("verify_primary_entity.txt", "a") as f:
        f.write(msg + "\n")

log("Starting verification script...")

# Add project root to path
sys.path.append(os.getcwd())

try:
    from fedops_core.db.engine import async_session
    from fedops_core.db.models import Proposal, Entity, CompanyProfile
    from fedops_core.services.proposal_content_generator import ProposalContentGenerator
    log("Imports successful")
except ImportError as e:
    log(f"Import Error: {e}")
    sys.exit(1)

async def verify():
    async with async_session() as db:
        # 1. Check/Create Primary Entity
        result = await db.execute(select(Entity).where(Entity.is_primary == True))
        primary = result.scalar_one_or_none()
        
        if not primary:
            log("No primary entity found. Creating one for testing...")
            primary = Entity(
                uei="TEST_UEI_12345",
                legal_business_name="Acme Government Solutions",
                is_primary=True,
                entity_type="PARTNER"
            )
            db.add(primary)
            await db.commit()
            log(f"Created primary entity: {primary.legal_business_name}")
        else:
            log(f"Found primary entity: {primary.legal_business_name}")

        # 2. Find a proposal to test with
        result = await db.execute(select(Proposal).limit(1))
        proposal = result.scalar_one_or_none()
        
        if not proposal:
            log("No proposal found. Cannot test generation.")
            return

        # 3. Generate Past Performance
        log(f"Generating Past Performance for Proposal {proposal.id}...")
        generator = ProposalContentGenerator(db)
        
        try:
            result = await generator.generate_past_performance_volume(proposal.id)
            if result['status'] == 'success':
                content = result['content']
                log("Generation successful.")
                
                # 4. Verify Company Name in Content
                if primary.legal_business_name in content:
                    log(f"SUCCESS: Found company name '{primary.legal_business_name}' in generated content.")
                else:
                    log(f"WARNING: Company name '{primary.legal_business_name}' NOT found in content.")
                    log(f"Content snippet: {content[:500]}...")
            else:
                log(f"Generation failed: {result.get('message')}")
        except Exception as e:
            log(f"Exception during generation: {e}")

if __name__ == "__main__":
    # Clear log
    with open("verify_primary_entity.txt", "w") as f:
        f.write("")
    asyncio.run(verify())
