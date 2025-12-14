import asyncio
import logging
import json
import traceback
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from fedops_core.settings import settings
from fedops_agents.orchestrator import OrchestratorAgent
from fedops_core.db.models import Opportunity, OpportunityScore, OpportunityPipeline

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
            
            # Fetch the saved score to get the details
            stmt = select(OpportunityScore).where(OpportunityScore.opportunity_id == opportunity_id)
            score_res = await db.execute(stmt)
            score_entry = score_res.scalar_one_or_none()
            
            if score_entry and score_entry.details:
                sol_details = score_entry.details.get('solicitation')
                if sol_details:
                    ai_analysis = sol_details.get('ai_analysis')
                    logger.info("\n=== AI ANALYSIS STRUCTURE ===")
                    print(json.dumps(ai_analysis, indent=2, default=str))
                    logger.info("=============================\n")
                else:
                    logger.info("No solicitation details found in score entry")
            else:
                logger.info(f"Analysis result: {result} (No score entry found)")
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            logger.error(traceback.format_exc())
        finally:
            await db.close()
    
    await engine.dispose()

if __name__ == "__main__":
    # Use an existing opportunity ID from the database
    asyncio.run(reproduce_analysis(1))
