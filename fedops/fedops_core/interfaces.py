from typing import Protocol, AsyncIterator, Dict, Any

class SourceConnector(Protocol):
    name: str
    async def pull(self, params: Dict[str, Any]) -> AsyncIterator[Dict[str, Any]]:
        ...
