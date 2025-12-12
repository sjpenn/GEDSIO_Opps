import asyncio
import sys
from sqlalchemy import select, delete
from fedops_core.db.engine import AsyncSessionLocal
from fedops_core.db.models import Entity, EntityAward, CompanyProfile, CompanyProfileDocument, CompanyProfileLink

async def list_entities():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Entity))
        entities = result.scalars().all()
        print(f"Found {len(entities)} entities:")
        for e in entities:
            print(f" - {e.legal_business_name} (UEI: {e.uei}) [Type: {e.entity_type}, Primary: {e.is_primary}]")

async def clear_entities():
    async with AsyncSessionLocal() as session:
        print("Deleting Company Profile Links...")
        await session.execute(delete(CompanyProfileLink))
        print("Deleting Company Profile Documents...")
        await session.execute(delete(CompanyProfileDocument))
        print("Deleting Company Profiles...")
        await session.execute(delete(CompanyProfile))
        print("Deleting Entity Awards...")
        await session.execute(delete(EntityAward))
        print("Deleting Entities...")
        await session.execute(delete(Entity))
        await session.commit()
        print("Cleared all entities and related profiles.")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "clear":
        print("Clearing database...")
        asyncio.run(clear_entities())
    else:
        asyncio.run(list_entities())
