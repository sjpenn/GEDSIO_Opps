import asyncio
from sqlalchemy import select
from fedops_core.db.engine import AsyncSessionLocal
from fedops_core.db.models import Entity

async def verify_persistence():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Entity).where(Entity.legal_business_name.ilike("%Google%")))
        entities = result.scalars().all()
        print(f"Found {len(entities)} entities matching 'Google'")
        for e in entities:
            print(f"UEI: {e.uei}, Name: {e.legal_business_name}, Full Response Saved: {bool(e.full_response)}")

if __name__ == "__main__":
    asyncio.run(verify_persistence())
