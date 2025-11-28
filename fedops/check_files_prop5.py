
import asyncio
from sqlalchemy import select
from fedops_core.db.engine import AsyncSessionLocal
from fedops_core.db.models import StoredFile

async def check_files_for_proposal_5():
    async with AsyncSessionLocal() as db:
        # Get files for opportunity 2031 (proposal 5)
        result = await db.execute(
            select(StoredFile).where(StoredFile.opportunity_id == 2031)
        )
        files = result.scalars().all()
        
        print(f"Found {len(files)} files for opportunity 2031:")
        for f in files:
            has_parsed = "YES" if f.parsed_content and len(f.parsed_content) > 100 else "NO"
            parsed_len = len(f.parsed_content) if f.parsed_content else 0
            print(f"  {f.filename}")
            print(f"    - Parsed content: {has_parsed} ({parsed_len} chars)")
            print(f"    - File path: {f.file_path}")
            print(f"    - File type: {f.file_type}")
            print()

if __name__ == "__main__":
    asyncio.run(check_files_for_proposal_5())
