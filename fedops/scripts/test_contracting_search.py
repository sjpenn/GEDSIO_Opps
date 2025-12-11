
import asyncio
import os
import sys
import json

# Add project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fedops_core.settings import settings
from fedops_core.services.perplexity_service import PerplexityService

async def test_contracting_search(query: str):
    print(f"Searching for contracting professionals matching: '{query}'")
    service = PerplexityService()
    
    try:
        results = await service.research_contracting_professionals(query)
        
        print("\n--- RESULT ---")
        print(f"Query: {results.query}")
        print(f"Matches Found: {len(results.matches)}")
        
        for m in results.matches:
            print(f"\nName: {m.name}")
            print(f"Agency: {m.agency}")
            print(f"Role: {m.role}")
            print(f"Reason: {m.match_reason}")
            print(f"Overview: {m.overview}")
            
        print("\nRaw Response:")
        print(results.raw_response[:200] + "...")
                
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Test with a name that might need correction or is generic enough to find people
    # Let's try "Smith" or a specific one if we knew it.
    # The user said "names that sound like", so let's try a potentially misspelled name of a real person if we knew one, 
    # or just a common name. 
    # "John Smith" is too generic.
    # Let's try something that sounds like "Mary Johnson" but spelled "Mari Jonson" to test correction?
    # Or maybe "Patterson" -> "Paterson".
    
    search_query = "Michelle Burnett" # Random common name or maybe we try a slight misspelling "Michele Burnet"
    if len(sys.argv) > 1:
        search_query = sys.argv[1]
        
    asyncio.run(test_contracting_search(search_query))
