import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from fedops_core.db.models import AgentActivityLog

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    def __init__(self, name: str, db: AsyncSession):
        self.name = name
        self.db = db

    async def log_activity(self, opportunity_id: int, action: str, status: str, details: Optional[Dict[str, Any]] = None):
        """Logs agent activity to the database."""
        try:
            log_entry = AgentActivityLog(
                opportunity_id=opportunity_id,
                agent_name=self.name,
                action=action,
                status=status,
                details=details
            )
            self.db.add(log_entry)
            await self.db.commit()
        except Exception as e:
            logger.error(f"Failed to log activity for {self.name}: {e}")
            await self.db.rollback()

    @abstractmethod
    async def execute(self, opportunity_id: int, **kwargs) -> Dict[str, Any]:
        """Executes the agent's main logic."""
        pass
