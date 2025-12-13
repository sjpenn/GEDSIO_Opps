
import os
import shutil
import logging
from typing import List, Optional, Dict
from fastapi import UploadFile, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from fedops_core.db.models import CompanyProfileDocument
from fedops_core.settings import settings
from fedops_core.services.docling_service import DoclingService
from fedops_core.services.ai_service import AIService

logger = logging.getLogger(__name__)

class CompanyDocumentService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.docling = DoclingService()
        self.ai = AIService()

    async def save_upload_to_disk(self, file: UploadFile, uei: str) -> str:
        """Save uploaded file to disk and return path"""
        # Create directory for company if not exists
        upload_dir = os.path.join(settings.UPLOAD_DIR, "companies", uei)
        os.makedirs(upload_dir, exist_ok=True)
        
        file_path = os.path.join(upload_dir, file.filename)
        
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        return file_path

    async def process_bulk_upload(self, uei: str, files: List[UploadFile], background_tasks: BackgroundTasks) -> List[CompanyProfileDocument]:
        """
        Handle bulk upload of files. 
        Creates DB records immediately with 'PROCESSING' status, 
        then triggers background extraction/classification.
        """
        created_docs = []

        for file in files:
            try:
                # 1. Save to disk
                file_path = await self.save_upload_to_disk(file, uei)
                file_size = os.path.getsize(file_path)

                # 2. Initial DB Record (Processing)
                doc = CompanyProfileDocument(
                    company_uei=uei,
                    document_type="Unclassified",
                    title=file.filename,
                    file_path=file_path,
                    file_size=file_size,
                    status="PROCESSING"
                )
                self.db.add(doc)
                await self.db.flush()
                await self.db.refresh(doc)
                created_docs.append(doc)

                # 3. Schedule Background Processing
                background_tasks.add_task(self.analyze_document, doc.id, file_path)

            except Exception as e:
                logger.error(f"Failed to initiate upload for {file.filename}: {e}")
                # Create a failed record if possible
                continue

        await self.db.commit()
        return created_docs

    async def analyze_document(self, doc_id: int, file_path: str):
        """Background task to extract text and classify document"""
        # Create a new session for background task if needed, or pass session factory.
        # However, since we are inside a service initialized with a session, we need to be careful.
        # Standard FastAPI: BackgroundTasks run after response, so the original session might be closed.
        # We need a fresh session here.
        
        from fedops_core.db.engine import AsyncSessionLocal
        
        async with AsyncSessionLocal() as session:
            try:
                # Get doc
                result = await session.execute(select(CompanyProfileDocument).where(CompanyProfileDocument.id == doc_id))
                doc = result.scalar_one_or_none()
                
                if not doc:
                    logger.error(f"Document {doc_id} not found in background task")
                    return

                # 1. Extract Content
                parsed_text = await self.docling.parse_with_fallback(file_path)
                
                if not parsed_text:
                    doc.status = "FAILED"
                    doc.description = "Failed to extract text content."
                    await session.commit()
                    return

                doc.parsed_content = parsed_text

                # 2. Classify Document
                doc_type, description = await self._classify_document(doc.title, parsed_text)
                
                doc.document_type = doc_type
                doc.description = description
                doc.status = "COMPLETED"
                
                logger.info(f"Analyzed {doc.title}: Type={doc_type}")
                await session.commit()

            except Exception as e:
                logger.error(f"Error analyzing document {doc_id}: {e}", exc_info=True)
                # We need to re-fetch doc if session rolled back or error occurred
                # But for simplicity, we log it. Ideally update DB to FAILED if possible.

    async def _classify_document(self, filename: str, content: str) -> tuple[str, str]:
        """Returns (DocumentType, Summary/Description)"""
        
        # Heuristic 1: Filename
        fname = filename.lower()
        if "capability" in fname or "cap_stmt" in fname:
            return "Capability Statement", "Auto-classified based on filename."
        if "past" in fname and "perf" in fname:
            return "Past Performance", "Auto-classified based on filename."
        if "iso" in fname or "cert" in fname:
            return "Certification", "Auto-classified based on filename."

        # Heuristic 2: AI Classification
        prompt = f"""
        You are a document classifier for a federal contracting company.
        Analyze the following text (first 2000 chars) and classify it into one of these categories:
        - Capability Statement
        - Past Performance
        - Proposal
        - Statement of Work (SOW) / PWS / SOO
        - Contract
        - Certification
        - Resume
        - Other

        Also provide a 1-sentence description/summary.

        Output JSON: {{ "type": "Category", "description": "Summary..." }}

        Text snippet:
        {content[:2000]}
        """

        try:
            result = await self.ai.analyze_opportunity(prompt) # Re-using generic analysis method
            if result and "type" in result:
                return result["type"], result.get("description", "AI classified.")
            
        except Exception as e:
            logger.warning(f"AI classification failed: {e}")
        
        return "Other", "Could not automatically classify."

    async def reanalyze_document(self, doc_id: int, background_tasks: BackgroundTasks) -> bool:
        """
        Trigger re-analysis of an existing document.
        Resets status to PROCESSING and queues background task.
        """
        # Get document
        result = await self.db.execute(select(CompanyProfileDocument).where(CompanyProfileDocument.id == doc_id))
        doc = result.scalar_one_or_none()
        
        if not doc:
            return False
            
        # Reset status
        doc.status = "PROCESSING"
        doc.document_type = "Unclassified" # Reset type to verify re-classification
        doc.description = None
        await self.db.commit()
        
        # Queue task
        background_tasks.add_task(self.analyze_document, doc.id, doc.file_path)
        
        return True
