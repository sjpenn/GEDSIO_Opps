import asyncio
import json
from fedops_sources.sam_entity import SamEntityClient

async def debug_search():
    client = SamEntityClient()
    query = "space metrics inc"
    print(f"Searching for: '{query}'")
    
    try:
        results = await client.search_entities(query, bypass_cache=True)
        
        print(f"\nFound {len(results.get('entityData', []))} results.")
        
        print("\nTop 5 Results:")
        for i, entity in enumerate(results.get('entityData', [])[:5]):
            reg = entity.get('entityRegistration', {})
            name = reg.get('legalBusinessName', 'N/A')
            uei = reg.get('ueiSAM', 'N/A')
            match = entity.get('_fuzzy_match', {})
            score = match.get('similarity_score', 'N/A')
            print(f"{i+1}. {name} (UEI: {uei}) - Score: {score}")
            
    except Exception as e:
        print(f"Error during search: {e}")

if __name__ == "__main__":
    asyncio.run(debug_search())
