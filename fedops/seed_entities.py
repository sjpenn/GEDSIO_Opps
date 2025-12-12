import asyncio
from fedops_core.db.engine import engine, AsyncSession
from fedops_core.db.models import Entity
from sqlalchemy.orm import sessionmaker
from datetime import datetime

async def seed_entities():
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        print("Seeding Booz Allen Hamilton...")
        bah = Entity(
            uei="H63FBC7L8414", # Real UEI for BAH
            legal_business_name="BOOZ ALLEN HAMILTON INC.",
            entity_type="PARTNER", 
            last_synced_at=datetime.utcnow(),
            is_primary=False,
            full_response={"entityRegistration": {"ueiSAM": "H63FBC7L8414", "legalBusinessName": "BOOZ ALLEN HAMILTON INC.", "cageCode": "06313"}}
        )
        session.add(bah)
        try:
            await session.commit()
            print("Seeded BAH successfully.")
        except Exception as e:
            print(f"Error seeding BAH: {e}")
            await session.rollback()

if __name__ == "__main__":
    asyncio.run(seed_entities())
