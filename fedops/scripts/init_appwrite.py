#!/usr/bin/env python3
"""
Appwrite Collection Initialization Script

Creates all required collections and attributes in Appwrite database.
Also creates storage buckets for file uploads.

Usage:
    python scripts/init_appwrite.py

Requirements:
    - Set APPWRITE_PROJECT_ID, APPWRITE_DATABASE_ID, and APPWRITE_API_KEY in .env
"""

import sys
import os
import time
import warnings

# Suppress Appwrite SDK deprecation warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load .env file explicitly
from dotenv import load_dotenv
load_dotenv()

from appwrite.client import Client
from appwrite.services.databases import Databases
from appwrite.services.storage import Storage
from appwrite.id import ID
from appwrite.exception import AppwriteException

# Read environment variables directly
APPWRITE_ENDPOINT = os.getenv("APPWRITE_ENDPOINT", "https://nyc.cloud.appwrite.io/v1")
APPWRITE_PROJECT_ID = os.getenv("APPWRITE_PROJECT_ID", "")
APPWRITE_DATABASE_ID = os.getenv("APPWRITE_DATABASE_ID", "")
APPWRITE_API_KEY = os.getenv("APPWRITE_API_KEY", "")

# Validate required settings
if not APPWRITE_PROJECT_ID:
    print("ERROR: APPWRITE_PROJECT_ID is not set in .env file")
    print("Please add: APPWRITE_PROJECT_ID=your_project_id")
    sys.exit(1)

if not APPWRITE_DATABASE_ID:
    print("ERROR: APPWRITE_DATABASE_ID is not set in .env file")
    print("Please add: APPWRITE_DATABASE_ID=your_database_id")
    sys.exit(1)

if not APPWRITE_API_KEY:
    print("ERROR: APPWRITE_API_KEY is not set in .env file")
    print("Please add: APPWRITE_API_KEY=your_api_key")
    print("Create an API key in Appwrite Console with databases.* and storage.* permissions")
    sys.exit(1)

# Initialize client
client = Client()
client.set_endpoint(APPWRITE_ENDPOINT)
client.set_project(APPWRITE_PROJECT_ID)
client.set_key(APPWRITE_API_KEY)

databases = Databases(client)
storage = Storage(client)

DATABASE_ID = APPWRITE_DATABASE_ID


def create_collection(collection_id: str, name: str, attributes: list):
    """Create a collection with the specified attributes."""
    try:
        # Try to create the collection
        databases.create_collection(
            database_id=DATABASE_ID,
            collection_id=collection_id,
            name=name,
            permissions=[],  # Server API key has full access
            document_security=False
        )
        print(f"✓ Created collection: {name}")
    except AppwriteException as e:
        if "already exists" in str(e).lower() or e.code == 409:
            print(f"○ Collection already exists: {name}")
        else:
            print(f"✗ Error creating collection {name}: {e}")
            return False
    
    # Create attributes
    for attr in attributes:
        try:
            attr_type = attr.get("type", "string")
            attr_key = attr["key"]
            required = attr.get("required", False)
            default = attr.get("default")
            size = attr.get("size", 255)
            
            if attr_type == "string":
                databases.create_string_attribute(
                    database_id=DATABASE_ID,
                    collection_id=collection_id,
                    key=attr_key,
                    size=size,
                    required=required,
                    default=default if not required else None,
                    array=attr.get("array", False)
                )
            elif attr_type == "integer":
                databases.create_integer_attribute(
                    database_id=DATABASE_ID,
                    collection_id=collection_id,
                    key=attr_key,
                    required=required,
                    default=default if not required else None,
                    array=attr.get("array", False)
                )
            elif attr_type == "float":
                databases.create_float_attribute(
                    database_id=DATABASE_ID,
                    collection_id=collection_id,
                    key=attr_key,
                    required=required,
                    default=default if not required else None,
                    array=attr.get("array", False)
                )
            elif attr_type == "boolean":
                databases.create_boolean_attribute(
                    database_id=DATABASE_ID,
                    collection_id=collection_id,
                    key=attr_key,
                    required=required,
                    default=default if not required else None,
                    array=attr.get("array", False)
                )
            elif attr_type == "datetime":
                databases.create_datetime_attribute(
                    database_id=DATABASE_ID,
                    collection_id=collection_id,
                    key=attr_key,
                    required=required,
                    default=default if not required else None,
                    array=attr.get("array", False)
                )
            elif attr_type == "url":
                databases.create_url_attribute(
                    database_id=DATABASE_ID,
                    collection_id=collection_id,
                    key=attr_key,
                    required=required,
                    default=default if not required else None,
                    array=attr.get("array", False)
                )
            elif attr_type == "email":
                databases.create_email_attribute(
                    database_id=DATABASE_ID,
                    collection_id=collection_id,
                    key=attr_key,
                    required=required,
                    default=default if not required else None,
                    array=attr.get("array", False)
                )
            
            print(f"  ✓ Created attribute: {attr_key}")
        except AppwriteException as e:
            if "already exists" in str(e).lower() or e.code == 409:
                print(f"  ○ Attribute already exists: {attr_key}")
            else:
                print(f"  ✗ Error creating attribute {attr_key}: {e}")
        
        # Small delay to avoid rate limiting
        time.sleep(0.1)
    
    return True


def create_index(collection_id: str, key: str, attr_type: str = "key", attributes: list = None):
    """Create an index on a collection."""
    try:
        if attributes is None:
            attributes = [key]
        
        databases.create_index(
            database_id=DATABASE_ID,
            collection_id=collection_id,
            key=f"idx_{key}",
            type=attr_type,
            attributes=attributes,
            orders=["ASC"] * len(attributes)
        )
        print(f"  ✓ Created index: idx_{key}")
    except AppwriteException as e:
        if "already exists" in str(e).lower() or e.code == 409:
            print(f"  ○ Index already exists: idx_{key}")
        else:
            print(f"  ✗ Error creating index {key}: {e}")


def create_storage_bucket(bucket_id: str, name: str, max_file_size: int = 100000000, extensions: list = None):
    """Create a storage bucket."""
    try:
        storage.create_bucket(
            bucket_id=bucket_id,
            name=name,
            permissions=[],
            file_security=False,
            enabled=True,
            maximum_file_size=max_file_size,
            allowed_file_extensions=extensions or []
        )
        print(f"✓ Created storage bucket: {name}")
    except AppwriteException as e:
        if "already exists" in str(e).lower() or e.code == 409:
            print(f"○ Storage bucket already exists: {name}")
        else:
            print(f"✗ Error creating bucket {name}: {e}")


def main():
    print("=" * 60)
    print("Appwrite Collection Initialization")
    print("=" * 60)
    print(f"Endpoint: {APPWRITE_ENDPOINT}")
    print(f"Project: {APPWRITE_PROJECT_ID}")
    print(f"Database: {DATABASE_ID}")
    print(f"API Key: {APPWRITE_API_KEY[:8]}...{APPWRITE_API_KEY[-4:]}")
    print("=" * 60)
    print()
    
    # ===== OPPORTUNITIES =====
    print("\n📋 Creating opportunities collection...")
    create_collection("opportunities", "Opportunities", [
        {"key": "notice_id", "type": "string", "size": 255, "required": True},
        {"key": "solicitation_number", "type": "string", "size": 255},
        {"key": "title", "type": "string", "size": 500, "required": True},
        {"key": "department", "type": "string", "size": 255},
        {"key": "sub_tier", "type": "string", "size": 255},
        {"key": "office", "type": "string", "size": 255},
        {"key": "posted_date", "type": "datetime", "required": True},
        {"key": "type", "type": "string", "size": 100, "required": True},
        {"key": "base_type", "type": "string", "size": 100},
        {"key": "archive_type", "type": "string", "size": 100},
        {"key": "archive_date", "type": "datetime"},
        {"key": "type_of_set_aside_description", "type": "string", "size": 500},
        {"key": "type_of_set_aside", "type": "string", "size": 100},
        {"key": "response_deadline", "type": "datetime"},
        {"key": "naics_code", "type": "string", "size": 20},
        {"key": "classification_code", "type": "string", "size": 50},
        {"key": "active", "type": "string", "size": 10, "default": "Yes"},
        {"key": "description", "type": "string", "size": 1000000},
        {"key": "organization_type", "type": "string", "size": 255},
        {"key": "additional_info_link", "type": "url"},
        {"key": "ui_link", "type": "url"},
        {"key": "compliance_status", "type": "string", "size": 50, "default": "PENDING"},
        {"key": "risk_score", "type": "float"},
        {"key": "source", "type": "string", "size": 50, "default": "SAM.gov"},
        {"key": "incumbent_vendor", "type": "string", "size": 255},
        {"key": "incumbent_contract_number", "type": "string", "size": 255},
        {"key": "incumbent_value", "type": "string", "size": 100},
        {"key": "incumbent_expiration_date", "type": "datetime"},
        {"key": "previous_sow_document_id", "type": "string", "size": 36},
        {"key": "created_at", "type": "datetime"},
        {"key": "updated_at", "type": "datetime"},
    ])
    time.sleep(2)  # Wait for attributes to be indexed
    create_index("opportunities", "notice_id", "unique", ["notice_id"])
    create_index("opportunities", "naics_code")
    create_index("opportunities", "posted_date")
    create_index("opportunities", "type")
    
    # ===== ENTITIES =====
    print("\n👥 Creating entities collection...")
    create_collection("entities", "Entities", [
        {"key": "uei", "type": "string", "size": 12, "required": True},
        {"key": "legal_business_name", "type": "string", "size": 500, "required": True},
        {"key": "cage_code", "type": "string", "size": 10},
        {"key": "entity_type", "type": "string", "size": 50, "default": "OTHER"},
        {"key": "notes", "type": "string", "size": 10000},
        {"key": "is_primary", "type": "boolean", "default": False},
        {"key": "logo_url", "type": "url"},
        {"key": "revenue", "type": "float"},
        {"key": "personnel_count", "type": "integer"},
        {"key": "last_synced_at", "type": "datetime"},
        {"key": "last_active_at", "type": "datetime"},
        {"key": "created_at", "type": "datetime"},
        {"key": "updated_at", "type": "datetime"},
    ])
    time.sleep(2)
    create_index("entities", "uei", "unique", ["uei"])
    create_index("entities", "is_primary")
    
    # ===== STORED FILES =====
    print("\n📁 Creating stored_files collection...")
    create_collection("stored_files", "Stored Files", [
        {"key": "filename", "type": "string", "size": 500, "required": True},
        {"key": "file_path", "type": "string", "size": 1000, "required": True},
        {"key": "storage_file_id", "type": "string", "size": 255},
        {"key": "file_type", "type": "string", "size": 50},
        {"key": "file_size", "type": "integer"},
        {"key": "content_summary", "type": "string", "size": 50000},
        {"key": "parsed_content", "type": "string", "size": 1000000},
        {"key": "opportunity_id", "type": "string", "size": 36},
        {"key": "version_number", "type": "string", "size": 20, "default": "1.0"},
        {"key": "status", "type": "string", "size": 50, "default": "DRAFT"},
        {"key": "checked_out_by", "type": "string", "size": 255},
        {"key": "checked_out_at", "type": "datetime"},
        {"key": "s3_uri", "type": "string", "size": 500},
        {"key": "parent_file_id", "type": "string", "size": 36},
        {"key": "created_at", "type": "datetime"},
        {"key": "updated_at", "type": "datetime"},
    ])
    time.sleep(2)
    create_index("stored_files", "opportunity_id")
    create_index("stored_files", "filename")
    
    # ===== PROPOSALS =====
    print("\n📝 Creating proposals collection...")
    create_collection("proposals", "Proposals", [
        {"key": "opportunity_id", "type": "string", "size": 36, "required": True},
        {"key": "version", "type": "integer", "default": 1},
        {"key": "current_stage", "type": "string", "size": 50, "default": "DISCOVERY"},
        {"key": "stage_status", "type": "string", "size": 50, "default": "IN_PROGRESS"},
        {"key": "shipley_phase", "type": "string", "size": 100},
        {"key": "capture_manager_id", "type": "string", "size": 255},
        {"key": "bid_decision_score", "type": "float"},
        {"key": "bid_decision_justification", "type": "string", "size": 10000},
        {"key": "bid_decision_date", "type": "datetime"},
        {"key": "bid_decision_by", "type": "string", "size": 255},
        {"key": "created_at", "type": "datetime"},
        {"key": "updated_at", "type": "datetime"},
    ])
    time.sleep(2)
    create_index("proposals", "opportunity_id")
    create_index("proposals", "current_stage")
    
    # ===== PROPOSAL VOLUMES =====
    print("\n📚 Creating proposal_volumes collection...")
    create_collection("proposal_volumes", "Proposal Volumes", [
        {"key": "proposal_id", "type": "string", "size": 36, "required": True},
        {"key": "title", "type": "string", "size": 255, "required": True},
        {"key": "order", "type": "integer", "default": 0},
        {"key": "created_at", "type": "datetime"},
        {"key": "updated_at", "type": "datetime"},
    ])
    time.sleep(2)
    create_index("proposal_volumes", "proposal_id")
    
    # ===== COMPANY PROFILES =====
    print("\n🏢 Creating company_profiles collection...")
    create_collection("company_profiles", "Company Profiles", [
        {"key": "uei", "type": "string", "size": 12, "required": True},
        {"key": "company_name", "type": "string", "size": 500, "required": True},
        {"key": "entity_uei", "type": "string", "size": 12},
        {"key": "created_at", "type": "datetime"},
        {"key": "updated_at", "type": "datetime"},
    ])
    time.sleep(2)
    create_index("company_profiles", "uei", "unique", ["uei"])
    
    # ===== COMPANY PROFILE DOCUMENTS =====
    print("\n📄 Creating company_profile_documents collection...")
    create_collection("company_profile_documents", "Company Profile Documents", [
        {"key": "company_uei", "type": "string", "size": 12, "required": True},
        {"key": "document_type", "type": "string", "size": 50, "required": True},
        {"key": "title", "type": "string", "size": 500, "required": True},
        {"key": "description", "type": "string", "size": 5000},
        {"key": "file_path", "type": "string", "size": 1000, "required": True},
        {"key": "storage_file_id", "type": "string", "size": 255},
        {"key": "file_size", "type": "integer"},
        {"key": "parsed_content", "type": "string", "size": 1000000},
        {"key": "status", "type": "string", "size": 50, "default": "COMPLETED"},
        {"key": "created_at", "type": "datetime"},
        {"key": "updated_at", "type": "datetime"},
    ])
    time.sleep(2)
    create_index("company_profile_documents", "company_uei")
    create_index("company_profile_documents", "document_type")
    
    # ===== ENTITY AWARDS =====
    print("\n🏆 Creating entity_awards collection...")
    create_collection("entity_awards", "Entity Awards", [
        {"key": "award_id", "type": "string", "size": 255, "required": True},
        {"key": "recipient_uei", "type": "string", "size": 12, "required": True},
        {"key": "total_obligation", "type": "float"},
        {"key": "description", "type": "string", "size": 10000},
        {"key": "award_date", "type": "datetime"},
        {"key": "awarding_agency", "type": "string", "size": 255},
        {"key": "naics_code", "type": "string", "size": 20},
        {"key": "solicitation_id", "type": "string", "size": 255},
        {"key": "award_type", "type": "string", "size": 50, "default": "Prime"},
        {"key": "created_at", "type": "datetime"},
    ])
    time.sleep(2)
    create_index("entity_awards", "recipient_uei")
    create_index("entity_awards", "naics_code")
    
    # ===== OPPORTUNITY PIPELINES =====
    print("\n🔄 Creating opportunity_pipelines collection...")
    create_collection("opportunity_pipelines", "Opportunity Pipelines", [
        {"key": "opportunity_id", "type": "string", "size": 36, "required": True},
        {"key": "status", "type": "string", "size": 50, "default": "WATCHING"},
        {"key": "stage", "type": "string", "size": 50, "default": "QUALIFICATION"},
        {"key": "questions_due_date", "type": "datetime"},
        {"key": "proposal_due_date", "type": "datetime"},
        {"key": "submission_instructions", "type": "string", "size": 10000},
        {"key": "notes", "type": "string", "size": 10000},
        {"key": "archived", "type": "boolean", "default": False},
        {"key": "archived_at", "type": "datetime"},
        {"key": "archived_by", "type": "string", "size": 255},
        {"key": "created_at", "type": "datetime"},
        {"key": "updated_at", "type": "datetime"},
    ])
    time.sleep(2)
    create_index("opportunity_pipelines", "opportunity_id", "unique", ["opportunity_id"])
    create_index("opportunity_pipelines", "status")
    
    # ===== DOCUMENT CHUNKS =====
    print("\n🧩 Creating document_chunks collection...")
    create_collection("document_chunks", "Document Chunks", [
        {"key": "stored_file_id", "type": "string", "size": 36, "required": True},
        {"key": "opportunity_id", "type": "string", "size": 36},
        {"key": "chunk_index", "type": "integer", "required": True},
        {"key": "content", "type": "string", "size": 100000, "required": True},
        {"key": "page_number", "type": "integer"},
        {"key": "section", "type": "string", "size": 50},
        {"key": "start_position", "type": "integer"},
        {"key": "end_position", "type": "integer"},
        {"key": "chunk_type", "type": "string", "size": 50},
        {"key": "vector_id", "type": "string", "size": 255},
        {"key": "created_at", "type": "datetime"},
    ])
    time.sleep(2)
    create_index("document_chunks", "stored_file_id")
    create_index("document_chunks", "opportunity_id")
    create_index("document_chunks", "vector_id")
    
    # ===== DOCLING DOCUMENTS =====
    print("\n📑 Creating docling_documents collection...")
    create_collection("docling_documents", "Docling Documents", [
        {"key": "stored_file_id", "type": "string", "size": 36, "required": True},
        {"key": "opportunity_id", "type": "string", "size": 36, "required": True},
        {"key": "markdown", "type": "string", "size": 1000000},
        {"key": "num_pages", "type": "integer"},
        {"key": "num_tables", "type": "integer"},
        {"key": "num_chunks", "type": "integer"},
        {"key": "processed_at", "type": "datetime"},
        {"key": "created_at", "type": "datetime"},
    ])
    time.sleep(2)
    create_index("docling_documents", "stored_file_id", "unique", ["stored_file_id"])
    create_index("docling_documents", "opportunity_id")
    
    # ===== PAST PERFORMANCES =====
    print("\n🎯 Creating past_performances collection...")
    create_collection("past_performances", "Past Performances", [
        {"key": "entity_uei", "type": "string", "size": 12, "required": True},
        {"key": "award_id", "type": "string", "size": 255},
        {"key": "opportunity_id", "type": "string", "size": 36},
        {"key": "source_document_id", "type": "string", "size": 36},
        {"key": "title", "type": "string", "size": 500, "required": True},
        {"key": "status", "type": "string", "size": 50, "default": "DRAFT"},
        {"key": "created_by", "type": "string", "size": 255},
        {"key": "approved_by", "type": "string", "size": 255},
        {"key": "approved_at", "type": "datetime"},
        {"key": "created_at", "type": "datetime"},
        {"key": "updated_at", "type": "datetime"},
    ])
    time.sleep(2)
    create_index("past_performances", "entity_uei")
    create_index("past_performances", "status")
    
    # ===== RESUMES =====
    print("\n📋 Creating resumes collection...")
    create_collection("resumes", "Resumes", [
        {"key": "user_id", "type": "string", "size": 255},
        {"key": "stored_file_id", "type": "string", "size": 36, "required": True},
        {"key": "raw_text", "type": "string", "size": 1000000},
        {"key": "status", "type": "string", "size": 50, "default": "UPLOADED"},
        {"key": "error_message", "type": "string", "size": 1000},
        {"key": "formatted_content_html", "type": "string", "size": 1000000},
        {"key": "created_at", "type": "datetime"},
        {"key": "updated_at", "type": "datetime"},
    ])
    time.sleep(2)
    create_index("resumes", "user_id")
    create_index("resumes", "stored_file_id")
    
    # ===== DOCUMENT SECTIONS =====
    print("\n📂 Creating document_sections collection...")
    create_collection("document_sections", "Document Sections", [
        {"key": "stored_file_id", "type": "string", "size": 36, "required": True},
        {"key": "opportunity_id", "type": "string", "size": 36, "required": True},
        {"key": "section_letter", "type": "string", "size": 2, "required": True},
        {"key": "section_title", "type": "string", "size": 500},
        {"key": "start_position", "type": "integer"},
        {"key": "end_position", "type": "integer"},
        {"key": "start_line", "type": "integer"},
        {"key": "end_line", "type": "integer"},
        {"key": "confidence_level", "type": "string", "size": 10},
        {"key": "detection_method", "type": "string", "size": 50},
        {"key": "content", "type": "string", "size": 1000000},
        {"key": "created_at", "type": "datetime"},
    ])
    time.sleep(2)
    create_index("document_sections", "stored_file_id")
    create_index("document_sections", "opportunity_id")
    create_index("document_sections", "section_letter")
    
    # ===== OPPORTUNITY COMMENTS =====
    print("\n💬 Creating opportunity_comments collection...")
    create_collection("opportunity_comments", "Opportunity Comments", [
        {"key": "opportunity_id", "type": "string", "size": 36, "required": True},
        {"key": "text", "type": "string", "size": 10000, "required": True},
        {"key": "created_at", "type": "datetime"},
    ])
    time.sleep(2)
    create_index("opportunity_comments", "opportunity_id")
    
    # ===== OPPORTUNITY SCORES =====
    print("\n📊 Creating opportunity_scores collection...")
    create_collection("opportunity_scores", "Opportunity Scores", [
        {"key": "opportunity_id", "type": "string", "size": 36, "required": True},
        {"key": "strategic_alignment_score", "type": "float", "default": 0.0},
        {"key": "financial_viability_score", "type": "float", "default": 0.0},
        {"key": "contract_risk_score", "type": "float", "default": 0.0},
        {"key": "internal_capacity_score", "type": "float", "default": 0.0},
        {"key": "data_integrity_score", "type": "float", "default": 0.0},
        {"key": "weighted_score", "type": "float", "default": 0.0},
        {"key": "go_no_go_decision", "type": "string", "size": 20},
        {"key": "created_at", "type": "datetime"},
        {"key": "updated_at", "type": "datetime"},
    ])
    time.sleep(2)
    create_index("opportunity_scores", "opportunity_id", "unique", ["opportunity_id"])
    
    # ===== STORAGE BUCKET (Single bucket for all files) =====
    print("\n")
    print("=" * 60)
    print("Creating Storage Bucket")
    print("=" * 60)
    
    # Single unified bucket for all file types
    create_storage_bucket(
        "fedops-files",
        "FedOps Files",
        max_file_size=100000000,  # 100MB
        extensions=["pdf", "doc", "docx", "xlsx", "xls", "txt", "zip", "pptx", "ppt", "png", "jpg", "jpeg"]
    )
    
    print("\n")
    print("=" * 60)
    print("Initialization Complete!")
    print("=" * 60)
    print("\nNote: Some attribute creation may take a moment to complete.")
    print("Check the Appwrite Console for the final status of all collections.")


if __name__ == "__main__":
    main()
