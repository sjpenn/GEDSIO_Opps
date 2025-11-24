import asyncio
from fedops_core.db.engine import engine, AsyncSession
from fedops_core.db.models import CompanyProfile, Opportunity
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from datetime import datetime

async def seed_data():
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        # 1. Create Company Profile
        print("Checking for Company Profile...")
        result = await session.execute(text("SELECT * FROM company_profiles"))
        company = result.scalars().first()
        
        if not company:
            print("Creating Company Profile...")
            company = CompanyProfile(
                uei="TEST_UEI_12345",
                company_name="Acme GovCon Solutions",
                target_naics=["541511", "541512", "541611"],
                target_keywords=["software development", "cloud migration", "cybersecurity", "ai"],
                target_set_asides=["SBA", "8(a)"]
            )
            session.add(company)
        else:
            print("Company Profile already exists.")

        # 2. Create Opportunity 2051
        print("Checking for Opportunity 2051...")
        result = await session.execute(text("SELECT * FROM opportunities WHERE id = 2051"))
        opp = result.scalars().first()
        
        if not opp:
            print("Creating Opportunity 2051...")
            # We need to force the ID to be 2051
            opp = Opportunity(
                id=2051,
                notice_id="sol-12345-2051",
                solicitation_number="SOL-2025-001",
                title="Cloud Migration and AI Services",
                department="Department of Technology",
                posted_date=datetime.utcnow(),
                type="Solicitation",
                description="The Department requires cloud migration services and AI implementation for legacy systems. Must have experience with AWS and Azure. Security clearance required.",
                naics_code="541511",
                type_of_set_aside="SBA",
                active="Yes"
            )
            session.add(opp)
        else:
            print("Opportunity 2051 already exists.")
            
        await session.commit()
        print("Database seeded successfully!")

if __name__ == "__main__":
    asyncio.run(seed_data())
