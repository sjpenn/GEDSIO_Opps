from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from fedops_core.services.ai_service import AIService
from fedops_core.settings import settings
import sys

router = APIRouter()

class AIConfigUpdate(BaseModel):
    provider: str
    model: Optional[str] = None

class AIConfigResponse(BaseModel):
    provider: str
    model: str
    available_providers: list[str]

@router.get("/config", response_model=AIConfigResponse)
async def get_ai_config():
    """Get current AI configuration."""
    service = AIService()
    return {
        "provider": service.provider,
        "model": service.model,
        "available_providers": ["openai", "openrouter", "gemini", "local"]
    }

@router.post("/config", response_model=AIConfigResponse)
async def update_ai_config(config: AIConfigUpdate):
    """Update AI configuration (switch provider)."""
    service = AIService()
    
    # Validation
    if config.provider == "local":
        # We assume the user has the local server running.
        # Ideally we could ping it here, but a simple connection test on first use is also fine.
        pass
            
    try:
        service.set_provider(config.provider, config.model)
        return {
            "provider": service.provider,
            "model": service.model,
            "available_providers": ["openai", "openrouter", "gemini", "local"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
