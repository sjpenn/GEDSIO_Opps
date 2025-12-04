from fedops_core.db.engine import AsyncSessionLocal
from sqlalchemy import text
import asyncio

async def manual_migration():
    async with AsyncSessionLocal() as session:
        print("Starting manual migration...")
        
        # 1. Drop tables to ensure clean slate
        print("Dropping tables...")
        await session.execute(text("DROP TABLE IF EXISTS team_members CASCADE"))
        await session.execute(text("DROP TABLE IF EXISTS opportunity_teams CASCADE"))
        
        # 2. Add columns to entities table
        print("Adding columns to entities table...")
        columns_to_add = [
            ("revenue", "FLOAT"),
            ("capabilities", "JSONB"),
            ("locations", "JSONB"),
            ("web_addresses", "JSONB"),
            ("personnel_count", "INTEGER"),
            ("business_types", "JSONB")
        ]
        
        for col_name, col_type in columns_to_add:
            try:
                await session.execute(text(f"ALTER TABLE entities ADD COLUMN IF NOT EXISTS {col_name} {col_type}"))
                print(f"Added column {col_name}")
            except Exception as e:
                print(f"Error adding column {col_name}: {e}")
        
        # 3. Create opportunity_teams table
        print("Creating opportunity_teams table...")
        await session.execute(text("""
            CREATE TABLE IF NOT EXISTS opportunity_teams (
                id SERIAL PRIMARY KEY,
                opportunity_id INTEGER NOT NULL,
                name VARCHAR NOT NULL,
                description TEXT,
                created_at TIMESTAMP WITHOUT TIME ZONE,
                updated_at TIMESTAMP WITHOUT TIME ZONE,
                FOREIGN KEY(opportunity_id) REFERENCES opportunities (id)
            )
        """))
        await session.execute(text("CREATE INDEX IF NOT EXISTS ix_opportunity_teams_id ON opportunity_teams (id)"))
        await session.execute(text("CREATE INDEX IF NOT EXISTS ix_opportunity_teams_opportunity_id ON opportunity_teams (opportunity_id)"))
        
        # 4. Create team_members table
        print("Creating team_members table...")
        await session.execute(text("""
            CREATE TABLE IF NOT EXISTS team_members (
                id SERIAL PRIMARY KEY,
                team_id INTEGER NOT NULL,
                entity_uei VARCHAR NOT NULL,
                role VARCHAR NOT NULL,
                capabilities_contribution JSONB,
                notes TEXT,
                created_at TIMESTAMP WITHOUT TIME ZONE,
                FOREIGN KEY(team_id) REFERENCES opportunity_teams (id),
                FOREIGN KEY(entity_uei) REFERENCES entities (uei)
            )
        """))
        await session.execute(text("CREATE INDEX IF NOT EXISTS ix_team_members_id ON team_members (id)"))
        await session.execute(text("CREATE INDEX IF NOT EXISTS ix_team_members_team_id ON team_members (team_id)"))
        await session.execute(text("CREATE INDEX IF NOT EXISTS ix_team_members_entity_uei ON team_members (entity_uei)"))
        
        await session.commit()
        print("Manual migration completed.")

if __name__ == "__main__":
    asyncio.run(manual_migration())
