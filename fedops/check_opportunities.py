import asyncio
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from fedops_core.settings import settings
from fedops_core.db.models import Opportunity

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def check_opportunities():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        try:
            result = await db.execute(select(Opportunity).limit(5))
            opportunities = result.scalars().all()
            
            if not opportunities:
                logger.info("No opportunities found in database")
            else:
                logger.info(f"Found {len(opportunities)} opportunities:")
                for opp in opportunities:
                    logger.info(f"  ID: {opp.id}, Title: {opp.title}")
            
        except Exception as e:
            logger.error(f"Error: {e}")
            import traceback
            logger.error(traceback.format_exc())
        finally:
            await db.close()
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check_opportunities())
