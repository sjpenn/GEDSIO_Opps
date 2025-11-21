from typing import AsyncIterator, Dict, Any
from fedops_core.interfaces import SourceConnector

class USASpendingAwardsConnector:
    name = "usaspending_awards"
    
    async def pull(self, params: Dict[str, Any]) -> AsyncIterator[Dict[str, Any]]:
        # Stub implementation
        yield {
            "award_id": "STUB-AWARD-999",
            "amount": 1000000.00,
            "recipient": "Acme Corp",
            "date": "2023-10-01"
        }
