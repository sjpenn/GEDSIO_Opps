"""
Document Classification Service

Orchestrates document classification for opportunities, detecting whether they use
SINGLE_DOCUMENT, MULTI_DOCUMENT, or HYBRID patterns. Includes special amendment handling.
"""

import logging
import re
import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from fedops_core.db.models import (
    Opportunity, 
    StoredFile, 
    DocumentClassification,
    DocumentSection,
    SectionSummary
)
from fedops_core.services.ai_service import AIService
from fedops_core.prompts import (
    DOCUMENT_CLASSIFICATION_PROMPT,
    SECTION_BOUNDARY_DETECTION_PROMPT
)

logger = logging.getLogger(__name__)


# Amendment detection patterns
AMENDMENT_PATTERNS = [
    r'amend(?:ment)?[\s_\-]*(?:\d+|0+\d+)',  # Amendment 0001, Amend_01
    r'mod(?:ification)?[\s_\-]*(?:\d+|0+\d+)',  # Mod 01, Modification 001
    r'change[\s_\-]*order',  # Change Order
    r'co[\s_\-]*\d+',  # CO-001
    r'_v\d+',  # RFP_v2
    r'_rev\d+',  # Solicitation_Rev1
]


class ClassificationService:
    """
    Service to classify opportunity document structure and detect section boundaries.
    
    Key Features:
    - Classifies opportunities as SINGLE_DOCUMENT, MULTI_DOCUMENT, or HYBRID
    - Special handling for amendments (not counted as separate document types)
    - Section boundary detection for single-document RFPs
    - Stores classification and sections in database
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.ai_service = AIService()
    
    async def classify_opportunity(self, opportunity_id: int) -> DocumentClassification:
        """
        Classify an opportunity as SINGLE_DOCUMENT, MULTI_DOCUMENT, or HYBRID.
        
        Special handling for amendments:
        - Files named "Amendment", "Mod", "Change Order" are NOT counted
          as separate document types
        - Amendment files are associated with their parent document
        
        Args:
            opportunity_id: ID of the opportunity to classify
            
        Returns:
            DocumentClassification record
        """
        # Check if already classified
        existing = await self.db.execute(
            select(DocumentClassification).where(
                DocumentClassification.opportunity_id == opportunity_id
            )
        )
        classification = existing.scalar_one_or_none()
        if classification:
            logger.info(f"Opportunity {opportunity_id} already classified as {classification.classification_type}")
            return classification
        
        # Get opportunity and its files
        opp_result = await self.db.execute(
            select(Opportunity).where(Opportunity.id == opportunity_id)
        )
        opportunity = opp_result.scalar_one_or_none()
        if not opportunity:
            raise ValueError(f"Opportunity {opportunity_id} not found")
        
        # Get all stored files for this opportunity
        files_result = await self.db.execute(
            select(StoredFile).where(StoredFile.opportunity_id == opportunity_id)
        )
        files = files_result.scalars().all()
        
        if not files:
            logger.warning(f"No files found for opportunity {opportunity_id}")
            # Create a classification with no files
            classification = DocumentClassification(
                opportunity_id=opportunity_id,
                classification_type="UNKNOWN",
                confidence="LOW",
                reasoning="No files found for this opportunity",
                amendment_count=0,
                classified_at=datetime.utcnow()
            )
            self.db.add(classification)
            await self.db.commit()
            await self.db.refresh(classification)
            return classification
        
        # Detect amendments first
        amendments, base_docs = self._detect_amendments(files)
        
        # Prepare document data for classification prompt
        documents_data = []
        for file in files:
            is_amendment = file.filename in amendments
            content_snippet = (file.parsed_content or "")[:500] if file.parsed_content else ""
            
            documents_data.append({
                "filename": file.filename,
                "is_amendment_hint": is_amendment,
                "content_preview": content_snippet
            })
        
        # Call AI for classification
        classification_result = await self._classify_with_ai(documents_data)
        
        # Create and store classification record
        classification = DocumentClassification(
            opportunity_id=opportunity_id,
            classification_type=classification_result.get("classification_type", "HYBRID"),
            confidence=classification_result.get("confidence", "MEDIUM"),
            reasoning=classification_result.get("reasoning", ""),
            document_inventory=classification_result.get("document_inventory", []),
            extraction_strategy=classification_result.get("extraction_strategy", {}),
            amendment_count=len(amendments),
            amendment_files=list(amendments),
            base_document_files=list(base_docs),
            critical_sections=classification_result.get("critical_sections_identified", []),
            classified_at=datetime.utcnow()
        )
        
        self.db.add(classification)
        await self.db.commit()
        await self.db.refresh(classification)
        
        logger.info(f"Classified opportunity {opportunity_id} as {classification.classification_type} "
                   f"(confidence: {classification.confidence}, {len(amendments)} amendments)")
        
        return classification
    
    def _detect_amendments(self, files: List[StoredFile]) -> Tuple[set, set]:
        """
        Identify amendment files and base documents.
        
        Args:
            files: List of StoredFile records
            
        Returns:
            Tuple of (amendment_filenames, base_document_filenames)
        """
        amendments = set()
        base_docs = set()
        
        for file in files:
            filename_lower = file.filename.lower()
            is_amendment = False
            
            for pattern in AMENDMENT_PATTERNS:
                if re.search(pattern, filename_lower, re.IGNORECASE):
                    is_amendment = True
                    break
            
            if is_amendment:
                amendments.add(file.filename)
            else:
                base_docs.add(file.filename)
        
        return amendments, base_docs
    
    async def _classify_with_ai(self, documents_data: List[Dict]) -> Dict:
        """
        Use AI to classify the document structure.
        
        Args:
            documents_data: List of document info dicts
            
        Returns:
            Classification result dict
        """
        # Format documents for prompt
        doc_text = json.dumps(documents_data, indent=2)
        prompt = DOCUMENT_CLASSIFICATION_PROMPT.format(documents=doc_text)
        
        try:
            response = await self.ai_service.generate_response(
                prompt=prompt,
                system_prompt="You are a government solicitation document analyzer. Respond only with valid JSON.",
                max_tokens=2000
            )
            
            # Parse JSON from response
            result = self._parse_json_response(response)
            return result
            
        except Exception as e:
            logger.error(f"AI classification failed: {e}")
            return {
                "classification_type": "HYBRID",
                "confidence": "LOW",
                "reasoning": f"AI classification failed: {str(e)}"
            }
    
    async def detect_sections(self, file_id: int) -> List[DocumentSection]:
        """
        For a single-document file, detect section A-M boundaries.
        
        Args:
            file_id: ID of the StoredFile to analyze
            
        Returns:
            List of DocumentSection records
        """
        # Get the file
        file_result = await self.db.execute(
            select(StoredFile).where(StoredFile.id == file_id)
        )
        file = file_result.scalar_one_or_none()
        if not file:
            raise ValueError(f"StoredFile {file_id} not found")
        
        if not file.parsed_content:
            logger.warning(f"File {file_id} has no parsed content")
            return []
        
        # Check for existing sections
        existing = await self.db.execute(
            select(DocumentSection).where(DocumentSection.stored_file_id == file_id)
        )
        existing_sections = existing.scalars().all()
        if existing_sections:
            logger.info(f"File {file_id} already has {len(existing_sections)} sections detected")
            return list(existing_sections)
        
        # Call AI for section detection
        sections_result = await self._detect_sections_with_ai(file.parsed_content)
        
        # Store detected sections
        sections = []
        for section_data in sections_result.get("sections_detected", []):
            section = DocumentSection(
                stored_file_id=file_id,
                opportunity_id=file.opportunity_id,
                section_letter=section_data.get("section_letter", "?"),
                section_title=section_data.get("section_title"),
                start_position=section_data.get("start_char_position"),
                end_position=section_data.get("end_char_position"),
                start_line=section_data.get("start_line"),
                end_line=section_data.get("end_line"),
                confidence_level=section_data.get("confidence", "MEDIUM"),
                detection_method=section_data.get("detection_method", "ai_detection"),
                content=self._extract_section_content(
                    file.parsed_content,
                    section_data.get("start_char_position"),
                    section_data.get("end_char_position")
                )
            )
            sections.append(section)
            self.db.add(section)
        
        await self.db.commit()
        
        # Refresh all sections to get IDs
        for section in sections:
            await self.db.refresh(section)
        
        logger.info(f"Detected {len(sections)} sections in file {file_id}")
        return sections
    
    async def _detect_sections_with_ai(self, document_text: str) -> Dict:
        """
        Use AI to detect section boundaries in a document.
        
        Args:
            document_text: Full text of the document
            
        Returns:
            Section detection result dict
        """
        # Truncate if too long (keep first 100k chars)
        if len(document_text) > 100000:
            document_text = document_text[:100000] + "\n\n[DOCUMENT TRUNCATED]"
        
        prompt = SECTION_BOUNDARY_DETECTION_PROMPT.format(document_text=document_text)
        
        try:
            response = await self.ai_service.generate_response(
                prompt=prompt,
                system_prompt="You are a document section parser for government solicitations. Respond only with valid JSON.",
                max_tokens=4000
            )
            
            result = self._parse_json_response(response)
            return result
            
        except Exception as e:
            logger.error(f"AI section detection failed: {e}")
            return {"sections_detected": []}
    
    def _extract_section_content(
        self, 
        full_text: str, 
        start_pos: Optional[int], 
        end_pos: Optional[int]
    ) -> Optional[str]:
        """
        Extract section content from full document text.
        
        Args:
            full_text: Complete document text
            start_pos: Starting character position
            end_pos: Ending character position
            
        Returns:
            Extracted section text or None
        """
        if start_pos is None or end_pos is None:
            return None
        
        try:
            return full_text[start_pos:end_pos]
        except (IndexError, TypeError):
            return None
    
    def _parse_json_response(self, response: str) -> Dict:
        """
        Parse JSON from AI response, handling markdown code blocks.
        
        Args:
            response: Raw AI response text
            
        Returns:
            Parsed JSON dict
        """
        # Try to find JSON in response
        text = response.strip()
        
        # Remove markdown code blocks if present
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        
        if text.endswith("```"):
            text = text[:-3]
        
        text = text.strip()
        
        # Try to find JSON object
        json_start = text.find('{')
        json_end = text.rfind('}') + 1
        
        if json_start >= 0 and json_end > json_start:
            json_str = text[json_start:json_end]
            return json.loads(json_str)
        
        # If no JSON found, return empty dict
        logger.warning("No JSON found in AI response")
        return {}
    
    async def get_classification(self, opportunity_id: int) -> Optional[DocumentClassification]:
        """
        Get existing classification for an opportunity.
        
        Args:
            opportunity_id: ID of the opportunity
            
        Returns:
            DocumentClassification record or None
        """
        result = await self.db.execute(
            select(DocumentClassification).where(
                DocumentClassification.opportunity_id == opportunity_id
            )
        )
        return result.scalar_one_or_none()
    
    async def get_sections(self, opportunity_id: int) -> List[DocumentSection]:
        """
        Get all detected sections for an opportunity.
        
        Args:
            opportunity_id: ID of the opportunity
            
        Returns:
            List of DocumentSection records
        """
        result = await self.db.execute(
            select(DocumentSection).where(
                DocumentSection.opportunity_id == opportunity_id
            ).order_by(DocumentSection.section_letter)
        )
        return list(result.scalars().all())
    
    async def reclassify_opportunity(self, opportunity_id: int) -> DocumentClassification:
        """
        Force re-classification of an opportunity (deletes existing classification).
        
        Args:
            opportunity_id: ID of the opportunity
            
        Returns:
            New DocumentClassification record
        """
        # Delete existing classification
        existing = await self.get_classification(opportunity_id)
        if existing:
            await self.db.delete(existing)
            await self.db.commit()
        
        # Classify again
        return await self.classify_opportunity(opportunity_id)
