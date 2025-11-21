import asyncio
import logging
import httpx
from fedops_core.db.engine import AsyncSessionLocal
from fedops_core.db.models import Opportunity
from sqlalchemy import select

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_resolve_resources(id: int):
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Opportunity).where(Opportunity.id == id))
        opportunity = result.scalar_one_or_none()
        
        if not opportunity:
            logger.error("Opportunity not found")
            return

        logger.info(f"Opportunity found: {opportunity.id}")
        logger.info(f"Resource links: {opportunity.resource_links}")
        
        if not opportunity.resource_links:
            logger.info("No resource links")
            return

        resolved_files = []
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            for link in opportunity.resource_links:
                try:
                    logger.info(f"Checking link: {link}")
                    response = await client.head(link)
                    logger.info(f"Status: {response.status_code}")
                    logger.info(f"Headers: {response.headers}")
                except Exception as e:
                    logger.error(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_resolve_resources(33))
