import asyncio
import logging
import json
import traceback
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from fedops_core.settings import settings
from fedops_agents.financial_agent import FinancialAnalysisAgent
from fedops_core.db.models import Opportunity

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def verify_ptw(opportunity_id: int):
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        try:
            logger.info(f"Starting PTW verification for opportunity {opportunity_id}")
            
            # Check if opportunity exists
            opp = await db.get(Opportunity, opportunity_id)
            if not opp:
                logger.error(f"Opportunity {opportunity_id} not found")
                return

            agent = FinancialAnalysisAgent(db)
            result = await agent.execute(opportunity_id)
            
            logger.info("\n=== PTW ANALYSIS RESULT ===")
            if isinstance(result, dict):
                print(json.dumps(result, indent=2, default=str))
                
                # Extract financial details
                details = result.get('details', {})
                financial = details.get('financial', {})
                
                if 'lcat_pricing' in financial:
                    lcats = financial['lcat_pricing']
                    if lcats:
                        logger.info(f"\nFound {len(lcats)} LCAT pricing entries.")
                        for lcat in lcats:
                            print(f"  - {lcat.get('lcat_title')}:")
                            print(f"    Phase: {lcat.get('project_phase')}")
                            print(f"    Hours: {lcat.get('estimated_hours')} | FTE: {lcat.get('fte_count')}")
                            print(f"    Rates: ${lcat.get('bill_rate_low')} - ${lcat.get('bill_rate_high')}/hr")
                            print(f"    Requirements: {lcat.get('requirements')[:100]}...")
                    else:
                        logger.warning("\n'lcat_pricing' key exists but is EMPTY list.")
                else:
                    logger.warning("\n'lcat_pricing' KEY MISSING in result details['financial']!")

                # Check for incumbent_summary
                incumbent = financial.get('incumbent_summary')
                if incumbent:
                    logger.info(f"\nIncumbent Summary: {incumbent}")
                else:
                    logger.warning("\nNo 'incumbent_summary' found in result details['financial']!")
            else:
                 logger.info(f"Result type: {type(result)}")
                 print(result)
            logger.info("===========================\n")
            
        except Exception as e:
            logger.error(f"Verification failed: {e}")
            logger.error(traceback.format_exc())
        finally:
            await db.close()
    
    await engine.dispose()

if __name__ == "__main__":
    # Test with Opportunity 424 as planned
    asyncio.run(verify_ptw(424))
