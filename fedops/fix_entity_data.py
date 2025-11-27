import asyncio
from sqlalchemy import select
from fedops_core.db.engine import AsyncSessionLocal
from fedops_core.db.models import Entity

async def fix_entity_data():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Entity))
        entities = result.scalars().all()
        
        fixed_count = 0
        for entity in entities:
            if entity.full_response and isinstance(entity.full_response, dict):
                if "entityData" in entity.full_response:
                    print(f"Fixing entity {entity.uei} ({entity.legal_business_name})...")
                    data_list = entity.full_response["entityData"]
                    if isinstance(data_list, list) and len(data_list) > 0:
                        # Create a new dict to trigger SQLAlchemy change detection
                        entity.full_response = dict(data_list[0])
                        fixed_count += 1
                    else:
                        print(f"Warning: Entity {entity.uei} has empty entityData list.")
        
        if fixed_count > 0:
            await db.commit()
            print(f"Successfully fixed {fixed_count} entities.")
        else:
            print("No entities needed fixing.")

if __name__ == "__main__":
    asyncio.run(fix_entity_data())
