import asyncio
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, func, or_
from fedops_core.db.models import Opportunity as OpportunityModel
from fedops_core.settings import settings
from datetime import datetime
import math

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def reproduce():
    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        try:
            # Simulate the query from the router
            skip = 0
            limit = 10
            naics = None
            setAside = None
            keywords = None
            
            logger.info("Querying local DB for opportunities")
            # Build query with filters
            query = select(OpportunityModel)
            
            if naics:
                query = query.where(OpportunityModel.naics_code.ilike(f"%{naics}%"))
            
            if setAside:
                query = query.where(OpportunityModel.type_of_set_aside.ilike(f"%{setAside}%"))
                
            if keywords:
                search_term = f"%{keywords}%"
                query = query.where(
                    or_(
                        OpportunityModel.title.ilike(search_term),
                        OpportunityModel.description.ilike(search_term),
                        OpportunityModel.naics_code.ilike(search_term),
                        OpportunityModel.type_of_set_aside.ilike(search_term),
                        OpportunityModel.solicitation_number.ilike(search_term)
                    )
                )

            # Calculate total count for pagination
            count_stmt = select(func.count()).select_from(query.subquery())
            logger.info("Executing count query")
            count_result = await db.execute(count_stmt)
            total = count_result.scalar_one()
            logger.info(f"Count result: {total}")

            # Calculate total pages
            total_pages = math.ceil(total / limit) if limit > 0 else 0
            current_page = (skip // limit) + 1 if limit > 0 else 1

            # Apply sorting and pagination
            query = query.order_by(OpportunityModel.posted_date.desc()).offset(skip).limit(limit)
            logger.info("Executing main query")
            result = await db.execute(query)
            opportunities = result.scalars().all()
            logger.info(f"Main query returned {len(opportunities)} items")
            
        except Exception as e:
            logger.error(f"Caught expected exception: {e}")
            import traceback
            logger.error(traceback.format_exc())
        finally:
            await db.close()
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(reproduce())
