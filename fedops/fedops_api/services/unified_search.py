from typing import List, Dict, Any, Optional
import asyncio
from fedops_sources.sam_opportunities.client import SamOpportunitiesClient
from fedops_sources.usaspending import USASpendingClient

class UnifiedSearchService:
    def __init__(self):
        self.sam_client = SamOpportunitiesClient()
        self.usa_client = USASpendingClient()

    async def search(self, keyword: str, limit: int = 20) -> Dict[str, Any]:
        """
        Search both SAM.gov (active/archived opportunities) and USASpending.gov (historical awards).
        Returns a unified structure.
        """
        # Run searches in parallel
        sam_task = self.sam_client.search_opportunities(keyword, limit=limit)
        usa_task = self.usa_client.search_awards_by_keyword(keyword, limit=limit)
        
        sam_results, usa_results = await asyncio.gather(sam_task, usa_task)
        
        unified_results = []
        
        # Process SAM results
        for item in sam_results:
            unified_results.append({
                "source": "SAM.gov",
                "id": item.get("solicitationNumber") or item.get("noticeId"),
                "title": item.get("title"),
                "description": item.get("description"), # Might be None or URL
                "status": "Active" if item.get("active") == "Yes" else "Archived",
                "date": item.get("postedDate"),
                "amount": None, # SAM doesn't usually show amount
                "recipient": None,
                "agency": item.get("department"),
                "type": item.get("type"),
                "raw": item
            })
            
        # Process USASpending results
        for item in usa_results:
            unified_results.append({
                "source": "USASpending",
                "id": item.get("Award ID"),
                "title": item.get("Description"), # USASpending uses description as title-equivalent
                "description": item.get("Description"),
                "status": "Awarded",
                "date": item.get("Start Date"),
                "amount": item.get("Award Amount"),
                "recipient": item.get("Recipient Name"),
                "agency": item.get("Awarding Agency"),
                "type": item.get("Contract Award Type"),
                "raw": item
            })
            
        return {
            "query": keyword,
            "total_results": len(unified_results),
            "results": unified_results
        }
