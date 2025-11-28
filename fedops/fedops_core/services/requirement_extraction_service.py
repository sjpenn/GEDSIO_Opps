"""
Requirement Extraction Service

Extracts requirements from SOW/PWS and solicitation documents using AI analysis.
Identifies requirement types, priorities, and source locations for interactive highlighting.
"""

import os
import re
from typing import List, Dict, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import google.generativeai as genai

from fedops_core.db.models import StoredFile, ProposalRequirement, DocumentArtifact, Proposal
from fedops_core.settings import settings

# Configure Gemini
if settings.GOOGLE_API_KEY:
    genai.configure(api_key=settings.GOOGLE_API_KEY)
else:
    print("Warning: GOOGLE_API_KEY not found in settings")



class RequirementExtractionService:
    """Service for extracting and analyzing requirements from documents"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.model = genai.GenerativeModel(settings.LLM_MODEL)
    
    async def extract_requirements_from_proposal(self, proposal_id: int) -> Dict:
        """
        Extract all requirements from documents associated with a proposal's opportunity.
        
        Returns:
            {
                "requirements_count": int,
                "artifacts_count": int,
                "status": "success" | "partial" | "failed",
                "files_found": int,
                "files_with_content": int,
                "files_processed": int,
                "message": str (optional)
            }
        """
        # Get proposal and associated opportunity
        result = await self.db.execute(
            select(Proposal).where(Proposal.id == proposal_id)
        )
        proposal = result.scalar_one_or_none()
        if not proposal:
            return {"status": "failed", "error": "Proposal not found"}
        
        # Get all stored files for this opportunity
        result = await self.db.execute(
            select(StoredFile).where(StoredFile.opportunity_id == proposal.opportunity_id)
        )
        files = result.scalars().all()
        
        files_found = len(files)
        files_with_content = sum(1 for f in files if f.parsed_content or f.file_path)
        
        if not files:
            return {
                "status": "success", 
                "requirements_count": 0, 
                "artifacts_count": 0, 
                "files_found": 0,
                "files_with_content": 0,
                "files_processed": 0,
                "message": "No documents found for this opportunity. Documents may need to be uploaded or imported from SAM.gov."
            }
        
        if files_with_content == 0:
            return {
                "status": "failed",
                "requirements_count": 0,
                "artifacts_count": 0,
                "files_found": files_found,
                "files_with_content": 0,
                "files_processed": 0,
                "message": f"Found {files_found} document(s) but none have parseable content. Files may need to be processed first."
            }
        
        total_requirements = 0
        total_artifacts = 0
        files_processed = 0
        
        # Debug logging
        with open('extraction_debug.log', 'a') as log_file:
            log_file.write(f"\n=== Starting extraction for proposal {proposal_id} ===\n")
            log_file.write(f"Found {files_found} files, {files_with_content} with content\n")
        
        for file in files:
            # Skip files without content
            if not file.parsed_content and not file.file_path:
                with open('extraction_debug.log', 'a') as log_file:
                    log_file.write(f"Skipping {file.filename}: no content or file path\n")
                continue
                
            # Extract requirements from each document
            req_count, art_count = await self._extract_from_document(file, proposal_id)
            with open('extraction_debug.log', 'a') as log_file:
                log_file.write(f"File {file.filename}: {req_count} requirements, {art_count} artifacts\n")
            total_requirements += req_count
            total_artifacts += art_count
            files_processed += 1
        
        await self.db.commit()
        
        return {
            "status": "success",
            "requirements_count": total_requirements,
            "artifacts_count": total_artifacts,
            "files_found": files_found,
            "files_with_content": files_with_content,
            "files_processed": files_processed
        }
    
    async def _extract_from_document(self, file: StoredFile, proposal_id: int) -> Tuple[int, int]:
        """Extract requirements and artifacts from a single document"""
        
        # Read document content
        content = None
        if file.parsed_content:
            content = file.parsed_content
            with open('extraction_debug.log', 'a') as log_file:
                log_file.write(f"Using parsed_content for {file.filename} ({len(content)} chars)\n")
        elif file.file_path:
            # If no parsed content, try to read from file
            try:
                with open(file.file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                with open('extraction_debug.log', 'a') as log_file:
                    log_file.write(f"Read content from file_path for {file.filename} ({len(content)} chars)\n")
            except Exception as e:
                print(f"Error reading file {file.filename}: {e}")
                with open('extraction_debug.log', 'a') as log_file:
                    log_file.write(f"Error reading file {file.filename}: {e}\n")
                return 0, 0
        
        if not content or len(content.strip()) == 0:
            with open('extraction_debug.log', 'a') as log_file:
                log_file.write(f"No content available for {file.filename}\n")
            return 0, 0
            
        with open('extraction_debug.log', 'a') as log_file:
            log_file.write(f"Content length for {file.filename}: {len(content)}\n")
        
        # Use AI to extract requirements
        requirements = await self._ai_extract_requirements(content, file.filename)
        artifacts = await self._ai_extract_artifacts(content, file.filename)
        
        # Save requirements to database
        req_count = 0
        for req in requirements:
            db_req = ProposalRequirement(
                proposal_id=proposal_id,
                requirement_text=req["text"],
                requirement_type=req["type"],
                source_document_id=file.id,
                source_section=req.get("section"),
                source_location=req.get("location"),
                priority=req.get("priority", "IMPORTANT"),
                compliance_status="NOT_STARTED"
            )
            self.db.add(db_req)
            req_count += 1
        
        # Save artifacts to database
        art_count = 0
        for art in artifacts:
            db_art = DocumentArtifact(
                proposal_id=proposal_id,
                artifact_type=art["type"],
                title=art["title"],
                description=art.get("description"),
                source_section=art.get("section"),
                required=art.get("required", True),
                status="NOT_STARTED"
            )
            self.db.add(db_art)
            art_count += 1
        
        return req_count, art_count
    
    async def _ai_extract_requirements(self, content: str, filename: str) -> List[Dict]:
        """Use AI to extract requirements from document content"""
        
        prompt = f"""
You are analyzing a government solicitation document: {filename}

Extract ALL requirements from this document. For each requirement, identify:
1. The exact requirement text
2. The requirement type (TECHNICAL, MANAGEMENT, PAST_PERFORMANCE, PRICING, CERTIFICATION, OTHER)
3. The section reference (e.g., "C.3.1.2", "Section 5.2")
4. The priority (MANDATORY, IMPORTANT, OPTIONAL)

Focus on:
- Technical specifications and performance requirements
- Management and staffing requirements
- Past performance requirements (Look for "Section L" instructions and "Section M" evaluation criteria related to recent relevant experience)
- Pricing and cost requirements
- Certifications and compliance requirements
- Deliverables and milestones

Return ONLY a JSON array with this structure:
[
  {{
    "text": "The contractor shall provide...",
    "type": "TECHNICAL",
    "section": "C.3.1",
    "priority": "MANDATORY"
  }}
]

Document content:
{content[:15000]}
"""
        
        try:
            response = self.model.generate_content(prompt)
            text = response.text.strip()
            
            # Extract JSON from response
            json_match = re.search(r'\[.*\]', text, re.DOTALL)
            if json_match:
                import json
                requirements = json.loads(json_match.group())
                with open('extraction_debug.log', 'a') as log_file:
                    log_file.write(f"Successfully extracted {len(requirements)} requirements from {filename}\n")
                return requirements
            else:
                with open('extraction_debug.log', 'a') as log_file:
                    log_file.write(f"No JSON array found in AI response for {filename}\n")
                    log_file.write(f"AI Response: {text[:500]}\n")
                return []
        except Exception as e:
            print(f"Error extracting requirements with AI: {e}")
            with open('extraction_debug.log', 'a') as log_file:
                log_file.write(f"Exception during AI extraction for {filename}: {e}\n")
            return []
    
    async def _ai_extract_artifacts(self, content: str, filename: str) -> List[Dict]:
        """Use AI to extract required artifacts/deliverables from document"""
        
        prompt = f"""
You are analyzing a government solicitation document: {filename}

Extract ALL required artifacts, forms, certifications, and deliverables mentioned in this document.

For each artifact, identify:
1. The title/name of the artifact
2. The type (FORM, CERTIFICATION, PAST_PERFORMANCE, PRICING_SHEET, OTHER)
3. A brief description
4. The section where it's mentioned
5. Whether it's required or optional

Return ONLY a JSON array with this structure:
[
  {{
    "title": "SF-330 Form",
    "type": "FORM",
    "description": "Architect-Engineer Qualifications",
    "section": "L.5",
    "required": true
  }}
]

Document content:
{content[:15000]}
"""
        
        try:
            response = self.model.generate_content(prompt)
            text = response.text.strip()
            
            # Extract JSON from response
            json_match = re.search(r'\[.*\]', text, re.DOTALL)
            if json_match:
                import json
                artifacts = json.loads(json_match.group())
                return artifacts
            else:
                return []
        except Exception as e:
            print(f"Error extracting artifacts with AI: {e}")
            return []
    
    def parse_document_structure(self, content: str) -> Dict:
        """
        Parse document into structured sections for highlighting.
        Returns a mapping of section references to character positions.
        """
        sections = {}
        
        # Simple regex-based section detection
        # Matches patterns like "C.3.1", "Section 5.2", "5.2.1", etc.
        section_pattern = r'(?:Section\s+)?([A-Z]?\d+(?:\.\d+)*)'
        
        for match in re.finditer(section_pattern, content):
            section_ref = match.group(1)
            start_pos = match.start()
            
            # Find end of section (next section or end of document)
            next_match = re.search(section_pattern, content[start_pos + 10:])
            if next_match:
                end_pos = start_pos + 10 + next_match.start()
            else:
                end_pos = len(content)
            
            sections[section_ref] = {
                "start": start_pos,
                "end": end_pos,
                "text": content[start_pos:end_pos]
            }
        
        return sections
