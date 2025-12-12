import asyncio
from fedops_core.db.engine import engine, AsyncSession
from fedops_core.db.models import Entity
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from datetime import datetime

async def seed_space_metrics():
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        # Check if exists
        result = await session.execute(select(Entity).where(Entity.uei == "SPACEUEI1234"))
        existing = result.scalars().first()
        
        if existing:
            print("Updating existing Space Metrics Inc...")
            existing.capabilities = [{"description": "Aerospace"}, {"description": "Data Analytics"}, {"description": "Satellite Systems"}]
        else:
            print("Seeding Space Metrics Inc...")
            entity = Entity(
                uei="SPACEUEI1234", 
                legal_business_name="SPACE METRICS INC.",
                entity_type="PARTNER", 
                last_synced_at=datetime.utcnow(),
                is_primary=False,
                full_response={
                    "entityRegistration": {
                        "ueiSAM": "SPACEUEI1234", 
                        "legalBusinessName": "SPACE METRICS INC.", 
                        "cageCode": "SP123",
                        "businessTypes": ["Minority Owned Business"]
                    }
                },
                capabilities=[{"description": "Aerospace"}, {"description": "Data Analytics"}, {"description": "Satellite Systems"}]
            )
            session.add(entity)

        try:
            await session.commit()
            print("Seeded/Updated Space Metrics Inc successfully.")
        except Exception as e:
            print(f"Error seeding: {e}")
            await session.rollback()

if __name__ == "__main__":
    asyncio.run(seed_space_metrics())
