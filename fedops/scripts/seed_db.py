import asyncio
import sys
import os

# Add the parent directory to sys.path so we can import fedops_core
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fedops_core.db.engine import AsyncSessionLocal
from fedops_core.db.models import Opportunity
from datetime import datetime, timedelta

async def seed_data():
    async with AsyncSessionLocal() as session:
        # Check if data exists
        # (Simplified for now, just adding data)
        
        opps = [
            Opportunity(
                solicitation_number="SOL-12345",
                title="Cloud Migration Services",
                posted_at=datetime.utcnow(),
                type="Solicitation",
                base_type="Presolicitation",
                set_aside_code="SBA",
                naics=["541511", "541512"],
                response_deadline=datetime.utcnow() + timedelta(days=30),
                description_url="https://example.com/sol-12345",
                agency_codes=["DOD", "USAF"]
            ),
            Opportunity(
                solicitation_number="REQ-98765",
                title="Cybersecurity Audit",
                posted_at=datetime.utcnow() - timedelta(days=2),
                type="Presolicitation",
                base_type="Sources Sought",
                set_aside_code="N/A",
                naics=["541690"],
                response_deadline=datetime.utcnow() + timedelta(days=15),
                description_url="https://example.com/req-98765",
                agency_codes=["DHS"]
            ),
             Opportunity(
                solicitation_number="AG-112233",
                title="Agricultural Drone Surveillance",
                posted_at=datetime.utcnow() - timedelta(days=5),
                type="Combined Synopsis/Solicitation",
                base_type="Solicitation",
                set_aside_code="WOSB",
                naics=["115112"],
                response_deadline=datetime.utcnow() + timedelta(days=45),
                description_url="https://example.com/ag-112233",
                agency_codes=["USDA"]
            )
        ]

        session.add_all(opps)
        await session.commit()
        print(f"Successfully seeded {len(opps)} opportunities.")

if __name__ == "__main__":
    asyncio.run(seed_data())
