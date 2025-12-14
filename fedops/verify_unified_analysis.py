import asyncio
import logging
import json
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from fedops_core.settings import settings
from fedops_core.db.models import Opportunity
from fedops_agents.compliance_agent import ComplianceAgent
from fedops_agents.capability_agent import CapabilityMappingAgent
from fedops_agents.financial_agent import FinancialAnalysisAgent
from fedops_agents.document_analysis_agent import DocumentAnalysisAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def verify_unified_flow(opportunity_id: int):
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        try:
            logger.info(f"Starting Unified Analysis Verification for Opp {opportunity_id}")
            
            # 1. Simulate Document Analysis (Get extraction data)
            # In a real run, this would potentially re-run extraction, but we'll try to just grab it if it exists or run it lightly.
            # For verification speed, let's assume we can re-run it or mock it. 
            # Ideally we want to see the CONTEXT passing.
            
            # Let's run DocumentAnalysisAgent to get fresh extracted_data
            logger.info("--- Step 0: Document Analysis (Fetching Data) ---")
            doc_agent = DocumentAnalysisAgent(db)
            doc_results = await doc_agent.execute(opportunity_id)
            extracted_data = doc_results.get("extracted_data", {})
            logger.info(f"Extracted Sections: {list(extracted_data.keys())}")
            
            # 2. Step 1: Compliance (Security)
            logger.info("\n--- Step 1: Compliance Agent (Security) ---")
            comp_agent = ComplianceAgent(db)
            comp_results = await comp_agent.execute(opportunity_id, extracted_data=extracted_data)
            security_details = comp_results.get("security_details", {})
            logger.info(f"Security Details Output: {json.dumps(security_details, default=str)[:200]}...")
            
            # 3. Step 2: Capability (Personnel) - Receives Security Context
            logger.info("\n--- Step 2: Capability Agent (Personnel) ---")
            logger.info(f"Passing Security Context: Clearance={security_details.get('personnel_clearance')}")
            
            cap_agent = CapabilityMappingAgent(db)
            cap_results = await cap_agent.execute(
                opportunity_id, 
                extracted_data=extracted_data,
                security_context=security_details
            )
            personnel_details = cap_results.get("personnel_details", {})
            logger.info(f"Personnel Details Output: {json.dumps(personnel_details, default=str)[:200]}...")
            
            # 4. Step 3: Financial (PTW) - Receives Personnel & Security Context
            logger.info("\n--- Step 3: Financial Agent (PTW) ---")
            logger.info(f"Passing Detailed Context: LCATs found={len(personnel_details.get('labor_categories', []))}")
            
            fin_agent = FinancialAnalysisAgent(db)
            fin_results = await fin_agent.execute(
                opportunity_id, 
                extracted_data=extracted_data,
                security_context=security_details,
                personnel_context=personnel_details
            )
            financial_details = fin_results.get("details", {}).get("financial", {})
            
            logger.info("\n=== VERIFICATION RESULTS ===")
            logger.info(f"Security Clearance Found: {security_details.get('personnel_clearance')}")
            logger.info(f"Personnel LCATs Found: {len(personnel_details.get('labor_categories', []))}")
            logger.info(f"Financial LCATs Generated: {len(financial_details.get('lcat_pricing', []))}")
            
            # Verify Flow Check
            extracted_lcats = personnel_details.get('labor_categories', [])
            ptw_lcats = [l['lcat_title'] for l in financial_details.get('lcat_pricing', [])]
            
            print("\nComparing LCATs:")
            print(f"Personnel Agent: {extracted_lcats}")
            print(f"Financial Agent: {ptw_lcats}")
            
            # Check if Security Clearance influenced Financial Agent
            # (We might need to check the 'insights' or 'risks' if not explicitly in pricing)
            
        except Exception as e:
            logger.error(f"Verification failed: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await db.close()
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(verify_unified_flow(424))
