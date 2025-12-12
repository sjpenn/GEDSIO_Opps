import asyncio
import os
import sys
from sqlalchemy import select

# Add project root to path
sys.path.append(os.getcwd())

from fedops_core.db.engine import AsyncSessionLocal
from fedops_core.db.models import Entity, EntityAward
from fedops_core.services.entity_enrichment_service import entity_enrichment_service

async def verify_enrichment():
    uei = "J99Y67D6XBM3" # Boeing
    
    print(f"Starting verification for {uei}...")
    
    # 1. Ensure Entity exists (Mocking it if needed for this standalone test)
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Entity).where(Entity.uei == uei))
        entity = result.scalars().first()
        if not entity:
            print("Creating test entity...")
            entity = Entity(
                uei=uei,
                legal_business_name="THE BOEING COMPANY",
                is_primary=True,
                entity_type="PARTNER",
                full_response={}
            )
            db.add(entity)
            await db.commit()
    
    # 2. Run Enrichment Directly
    print("Running enrichment service...")
    await entity_enrichment_service.enrich_entity(uei)
    
    # 3. Verify Results
    async with AsyncSessionLocal() as db:
        # Check Awards
        result = await db.execute(select(EntityAward).where(EntityAward.recipient_uei == uei))
        awards = result.scalars().all()
        print(f"Found {len(awards)} awards in database.")
        
        prime_count = len([a for a in awards if a.award_type == "Prime"])
        sub_count = len([a for a in awards if a.award_type == "Sub"])
        
        print(f"Prime Awards: {prime_count}")
        print(f"Sub Awards: {sub_count}")
        
        if len(awards) > 0:
            print("✅ SUCCESS: Awards fetched and stored.")
            # Show sample
            print(f"Sample Award: {awards[0].award_id} - {awards[0].description}")
            if awards[0].solicitation_id:
                print(f"Sample Solicitation ID: {awards[0].solicitation_id}")
        else:
            print("❌ FAILED: No awards found.")

if __name__ == "__main__":
    asyncio.run(verify_enrichment())
