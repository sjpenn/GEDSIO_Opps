"""
Appwrite Client Configuration

Centralized Appwrite client for database and storage operations.
Uses server-side API key for backend operations.
"""

# Suppress Appwrite SDK deprecation warnings (SDK v14+ renamed APIs)
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", message=".*deprecated.*")

from appwrite.client import Client
from appwrite.services.databases import Databases
from appwrite.services.storage import Storage
from appwrite.query import Query
from fedops_core.settings import settings
import logging

logger = logging.getLogger(__name__)

# Initialize Appwrite client
client = Client()
client.set_endpoint(settings.APPWRITE_ENDPOINT)
client.set_project(settings.APPWRITE_PROJECT_ID)

# Set API key for server-side operations
if settings.APPWRITE_API_KEY:
    client.set_key(settings.APPWRITE_API_KEY)
else:
    logger.warning("APPWRITE_API_KEY not set - some operations may fail")

# Initialize services
databases = Databases(client)
storage = Storage(client)

# Database configuration
DATABASE_ID = settings.APPWRITE_DATABASE_ID
STORAGE_BUCKET_ID = settings.APPWRITE_STORAGE_BUCKET_ID

# Collection IDs - will be created by init script
COLLECTIONS = {
    "opportunities": "opportunities",
    "entities": "entities",
    "stored_files": "stored_files",
    "proposals": "proposals",
    "proposal_volumes": "proposal_volumes",
    "company_profiles": "company_profiles",
    "company_profile_documents": "company_profile_documents",
    "entity_awards": "entity_awards",
    "opportunity_pipelines": "opportunity_pipelines",
    "document_chunks": "document_chunks",
    "docling_documents": "docling_documents",
    "past_performances": "past_performances",
    "resumes": "resumes",
    "document_sections": "document_sections",
    "section_summaries": "section_summaries",
    "extracted_requirements": "extracted_requirements",
    "evaluation_mappings": "evaluation_mappings",
    "opportunity_comments": "opportunity_comments",
    "agent_activity_logs": "agent_activity_logs",
    "opportunity_scores": "opportunity_scores",
    "proposal_requirements": "proposal_requirements",
    "requirement_responses": "requirement_responses",
    "document_artifacts": "document_artifacts",
    "contracting_officers": "contracting_officers",
    "saved_agency_searches": "saved_agency_searches",
    "document_classifications": "document_classifications",
    "cache_metadata": "cache_metadata",
}


def get_databases() -> Databases:
    """Get the Appwrite Databases service instance."""
    return databases


def get_storage() -> Storage:
    """Get the Appwrite Storage service instance."""
    return storage


def get_collection_id(collection_name: str) -> str:
    """Get the collection ID for a given collection name."""
    return COLLECTIONS.get(collection_name, collection_name)


# Re-export Query for convenience
__all__ = [
    "client",
    "databases",
    "storage",
    "DATABASE_ID",
    "STORAGE_BUCKET_ID",
    "COLLECTIONS",
    "Query",
    "get_databases",
    "get_storage",
    "get_collection_id",
]
