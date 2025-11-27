import asyncio
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from fedops_core.settings import settings
from fedops_agents.orchestrator import OrchestratorAgent
from fedops_core.db.models import Opportunity

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def reproduce_analysis(opportunity_id: int):
    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        try:
            logger.info(f"Starting analysis for opportunity {opportunity_id}")
            
            # Check if opportunity exists
            opp = await db.get(Opportunity, opportunity_id)
            if not opp:
                logger.error(f"Opportunity {opportunity_id} not found")
                return

            orchestrator = OrchestratorAgent(db)
            result = await orchestrator.execute(opportunity_id)
            logger.info(f"Analysis result: {result}")
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
        finally:
            await db.close()
    
    await engine.dispose()

if __name__ == "__main__":
    # Use an existing opportunity ID from the database
    asyncio.run(reproduce_analysis(1))
