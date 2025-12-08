import asyncio
import os
import sys

# Add the project root to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fedops_core.services.perplexity_service import PerplexityService
from fedops_core.settings import settings

async def main():
    print(f"Testing Perplexity Service with API Key: {settings.PERPLEXITY_API_KEY[:5]}...")
    service = PerplexityService()
    
    entity_name = "JMA SOLUTIONS LLC"
    print(f"Researching entity: {entity_name}")
    
    try:
        result = await service.research_entity(entity_name)
        print("Research successful!")
        print("Overview:", result.overview[:100] + "...")
    except Exception as e:
        print(f"Research failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
