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
    # LLM Providers
    OPENAI_API_KEY: Optional[str] = None
    OPENROUTER_API_KEY: Optional[str] = None
    DEEPSEEK_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None
    
    # LLM_PROVIDER: str = "openai" # gemini, openai, openrouter
    # LLM_MODEL: str = "gpt-4o-mini" # default model

    LLM_PROVIDER: str = "gemini"
    # LLM_MODEL: str = "gemini-2.5-flash"
    LLM_MODEL: str = "gemini-3-pro-preview"

    
    class Config:
        env_file = ".env"

settings = Settings()
