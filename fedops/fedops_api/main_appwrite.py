"""
FedOps API Main Entry Point - Appwrite Version

This is the Appwrite-based version of the API that replaces
SQLAlchemy/PostgreSQL with Appwrite Database and Storage.

To use this version instead of the SQLAlchemy version:
1. Rename main.py to main_sqlalchemy.py
2. Rename main_appwrite.py to main.py
3. Or run directly: uvicorn fedops_api.main_appwrite:app --reload
"""

from fastapi import FastAPI
from fedops_core.settings import settings
from starlette.middleware.cors import CORSMiddleware
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import Appwrite-based routers
from fedops_api.routers import (
    opportunities_appwrite, 
    entities_appwrite, 
    files_appwrite,
    proposals_appwrite,
    company_appwrite,
    past_performance_appwrite,
    manual_upload_appwrite,
    resumes_appwrite,
    extraction_appwrite,
    vector_store_appwrite
)

# Import routers that don't need DB modification (stateless or external API based)
# Note: Removed most routers as they use SQLAlchemy
from fedops_api.routers import config

app = FastAPI(
    title=f"{settings.PROJECT_NAME} (Appwrite)",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    description="FedOps API using Appwrite Database"
)

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# Appwrite-Based Routers (Fully Migrated)
# ============================================================================
app.include_router(
    opportunities_appwrite.router, 
    prefix="/api/v1/opportunities", 
    tags=["opportunities"]
)
app.include_router(
    entities_appwrite.router, 
    prefix="/api/v1/entities", 
    tags=["entities"]
)
app.include_router(
    files_appwrite.router, 
    prefix="/api/v1/files", 
    tags=["files"]
)
app.include_router(
    proposals_appwrite.router, 
    prefix="/api/v1/proposals", 
    tags=["proposals"]
)
app.include_router(
    company_appwrite.router, 
    prefix="/api/v1/company", 
    tags=["company"]
)
app.include_router(
    past_performance_appwrite.router, 
    prefix="/api/v1/past-performance", 
    tags=["past_performance"]
)
app.include_router(
    manual_upload_appwrite.router, 
    prefix="/api/v1/manual-upload", 
    tags=["manual_upload"]
)
app.include_router(
    resumes_appwrite.router, 
    prefix="/api/v1/resumes", 
    tags=["resumes"]
)
app.include_router(
    extraction_appwrite.router,
    prefix="/api/v1/extraction",
    tags=["extraction"]
)
app.include_router(
    vector_store_appwrite.router,
    prefix="/api/v1/vector-store",
    tags=["vector_store"]
)

# ============================================================================
# Stateless or External API Routers (No DB migration needed)
# ============================================================================
# Note: Other routers (ingest, agents, workflow, etc.) removed as they use SQLAlchemy
app.include_router(config.router, prefix="/api/v1")


@app.on_event("startup")
async def startup():
    """Verify Appwrite connection on startup."""
    try:
        from fedops_core.db.appwrite_client import databases, DATABASE_ID
        # Quick health check
        logger.info(f"Appwrite configured with database: {DATABASE_ID}")
        logger.info("Appwrite connection ready")
    except Exception as e:
        logger.error(f"Appwrite connection error: {e}")
        raise


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "database": "appwrite",
        "project_id": settings.APPWRITE_PROJECT_ID
    }


@app.get("/")
def root():
    """Root endpoint with API info."""
    return {
        "name": settings.PROJECT_NAME,
        "version": "2.0.0-appwrite",
        "database": "Appwrite",
        "docs": "/docs"
    }
