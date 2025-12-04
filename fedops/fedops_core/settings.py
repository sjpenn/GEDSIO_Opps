from pydantic_settings import BaseSettings
from typing import Optional
from dotenv import load_dotenv
import os

load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = "FedOps"
    API_V1_STR: str = "/api/v1"
    
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/fedops"
    
    UPLOAD_DIR: str = "uploads"
    
    # External APIs
    SAM_API_KEY: Optional[str] = None
    
    # LLM Providers
    OPENAI_API_KEY: Optional[str] = None
    OPENROUTER_API_KEY: Optional[str] = None
    DEEPSEEK_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None
    
    # LLM Provider: gemini, openai, openrouter
    LLM_PROVIDER: str = "openrouter"
    
    # OpenRouter Model Options:
    # - deepseek/deepseek-r1 (Strong structured JSON/tool calling)
    # - google/gemini-3-pro-preview (Native PDF support, fast analysis)
    # - google/gemini-2.0-flash-exp (Fast, efficient)
    # - qwen/qwen-2.5-32b-instruct (High accuracy extraction)
    # - mistralai/mistral-large-2 (Tool calling and schema support)
    # - anthropic/claude-3.5-sonnet (Excellent reasoning)
    
    # Gemini Models (when LLM_PROVIDER = "gemini"):
    # - gemini-2.5-flash
    # - gemini-2.5-pro
    # - gemini-3-pro-preview
    
    # OpenAI Models (when LLM_PROVIDER = "openai"):
    # - gpt-4o
    # - gpt-4o-mini
    
    LLM_MODEL: str = "deepseek/deepseek-r1"
    
    # Model-specific settings
    LLM_TEMPERATURE: float = 0.1  # Lower for more deterministic extraction
    LLM_MAX_TOKENS: int = 4096
    LLM_MAX_RETRIES: int = 3
    LLM_RETRY_DELAY: float = 1.0  # seconds
    
    # Fallback model if primary fails
    LLM_FALLBACK_MODEL: Optional[str] = "google/gemini-2.0-flash-exp"

    
    class Config:
        env_file = ".env"
        extra = "ignore"  # Allow extra fields in .env without validation errors

settings = Settings()
