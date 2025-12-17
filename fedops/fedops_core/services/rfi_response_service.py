"""
RFI Response Engine Service

Handles extraction of RFI requirements and generation of block-by-block responses.
"""

import json
import logging
from typing import Dict, List, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from fedops_core.db.models import Opportunity, OpportunityScore, Entity, PastPerformance
from fedops_core.services.ai_service import AIService
from fedops_core.prompts import (
    RFI_REQUIREMENTS_EXTRACTION_PROMPT,
    RFI_BLOCK_RESPONSE_PROMPT,
    RFI_FULL_RESPONSE_PROMPT,
    GOVCON_PROFILE
)

logger = logging.getLogger(__name__)


class RFIResponseService:
    """
    Service for generating RFI/Sources Sought responses.
    Extracts requirements and generates block-by-block responses.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.ai_service = AIService()
    
    async def extract_requirements(self, opportunity_id: int) -> Dict[str, Any]:
        """
        Extract all requirements/questions from RFI documents.
        Pulls content from ALL files associated with the opportunity.
        
        Returns:
            {
                "requirements": [...],
                "total_count": int,
                "summary": str
            }
        """
        from fedops_core.db.models import StoredFile, DoclingDocument
        
        # Get opportunity
        result = await self.db.execute(
            select(Opportunity).where(Opportunity.id == opportunity_id)
        )
        opportunity = result.scalar_one_or_none()
        
        if not opportunity:
            return {"error": "Opportunity not found", "requirements": []}
        
        # Collect content from multiple sources
        all_content = []
        
        # Source 1: Get parsed content from ALL StoredFiles for this opportunity
        files_result = await self.db.execute(
            select(StoredFile).where(StoredFile.opportunity_id == opportunity_id)
        )
        files = files_result.scalars().all()
        
        for file in files:
            if file.parsed_content:
                all_content.append(f"\n\n{'='*60}\nFILE: {file.filename}\n{'='*60}\n{file.parsed_content}")
                logger.info(f"RFI Extraction: Added {len(file.parsed_content)} chars from {file.filename}")
        
        # Source 2: Get Docling markdown if available (more structured)
        docling_result = await self.db.execute(
            select(DoclingDocument).where(DoclingDocument.opportunity_id == opportunity_id)
        )
        docling_docs = docling_result.scalars().all()
        
        for doc in docling_docs:
            if doc.markdown and doc.markdown not in str(all_content):
                all_content.append(f"\n\n{'='*60}\nDOCLING PARSED CONTENT\n{'='*60}\n{doc.markdown}")
                logger.info(f"RFI Extraction: Added {len(doc.markdown)} chars from Docling")
        
        # Source 3: Check extracted_data in score details
        score_result = await self.db.execute(
            select(OpportunityScore).where(OpportunityScore.opportunity_id == opportunity_id)
        )
        score = score_result.scalar_one_or_none()
        
        if score and score.details and score.details.get("extracted_data"):
            extracted = score.details.get("extracted_data", {})
            for key, value in extracted.items():
                if isinstance(value, dict) and value.get("raw_text"):
                    content = value.get('raw_text', '')
                    if content and content not in str(all_content):
                        all_content.append(f"\n\n=== {key.upper()} ===\n{content}")
                elif isinstance(value, str) and value not in str(all_content):
                    all_content.append(f"\n\n=== {key.upper()} ===\n{value}")
        
        # Source 4: Fallback to opportunity description
        if not all_content and opportunity.description:
            all_content.append(opportunity.description)
        
        rfi_content = "\n".join(all_content)
        
        logger.info(f"RFI Extraction: Total content length: {len(rfi_content)} characters from {len(files)} files")
        
        if not rfi_content.strip():
            return {
                "error": "No document content found. Please run analysis first.",
                "requirements": [],
                "total_count": 0
            }
        
        # Use AI to extract requirements - use generate_content for raw text response
        # Limit content size to leave room for output tokens
        prompt = RFI_REQUIREMENTS_EXTRACTION_PROMPT.format(
            rfi_content=rfi_content[:40000]  # Reduced to leave more output tokens
        )
        
        logger.info(f"RFI Extraction: Sending {len(prompt)} chars to AI for analysis")
        
        try:
            # Use generate_content to get raw text response
            response_text = await self.ai_service.generate_content(prompt, timeout=180)
            
            logger.info(f"RFI Extraction: Got {len(response_text)} chars response from AI")
            
            # Parse JSON from response
            parsed = self._parse_json_response(response_text)
            
            if parsed and "requirements" in parsed:
                reqs = parsed.get("requirements", [])
                logger.info(f"RFI Extraction: Successfully extracted {len(reqs)} requirements")
                return {
                    "requirements": reqs,
                    "total_count": parsed.get("total_count", len(reqs)),
                    "summary": parsed.get("summary", ""),
                    "opportunity_title": opportunity.title
                }
            else:
                # Try to salvage partial requirements from truncated response
                salvaged_reqs = self._salvage_requirements(response_text)
                if salvaged_reqs:
                    logger.warning(f"RFI Extraction: Salvaged {len(salvaged_reqs)} requirements from truncated response")
                    return {
                        "requirements": salvaged_reqs,
                        "total_count": len(salvaged_reqs),
                        "summary": "Note: Response may have been truncated. Some requirements may be incomplete.",
                        "opportunity_title": opportunity.title,
                        "truncated": True
                    }
                
                logger.error(f"RFI Extraction: Failed to parse requirements. Full response:\n{response_text}")
                return {
                    "error": f"Failed to parse JSON. AI response starts with: {response_text[:200]}...",
                    "requirements": [],
                    "total_count": 0,
                    "debug_response": response_text[:2000]
                }
                    
        except Exception as e:
            logger.error(f"Error extracting requirements: {e}")
            return {"error": str(e), "requirements": []}
    
    def _parse_json_response(self, text: str) -> Optional[Dict]:
        """Parse JSON from AI response text, handling code blocks and nested JSON."""
        import re
        
        if not text:
            return None
        
        # Strategy 1: Try to parse entire response as JSON
        try:
            return json.loads(text.strip())
        except json.JSONDecodeError:
            pass
        
        # Strategy 2: Extract from markdown code block - match everything between ``` markers
        # Use greedy matching for content between markers
        code_block_match = re.search(r'```(?:json)?\s*\n?([\s\S]*?)\n?```', text)
        if code_block_match:
            code_content = code_block_match.group(1).strip()
            try:
                return json.loads(code_content)
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse code block as JSON: {e}")
        
        # Strategy 3: Find the first { and last } to extract full JSON
        first_brace = text.find('{')
        last_brace = text.rfind('}')
        if first_brace != -1 and last_brace > first_brace:
            try:
                return json.loads(text[first_brace:last_brace+1])
            except json.JSONDecodeError:
                pass
        
        # Strategy 4: Try to find balanced braces
        try:
            start = text.find('{')
            if start != -1:
                depth = 0
                for i, char in enumerate(text[start:], start):
                    if char == '{':
                        depth += 1
                    elif char == '}':
                        depth -= 1
                        if depth == 0:
                            return json.loads(text[start:i+1])
        except json.JSONDecodeError:
            pass
        
        return None
    
    def _salvage_requirements(self, text: str) -> List[Dict]:
        """
        Attempt to salvage individual requirements from a truncated JSON response.
        Extracts requirement objects that were fully formed before truncation.
        """
        import re
        
        requirements = []
        
        # Pattern to match individual requirement objects
        # Looks for {...} objects with id and text fields
        req_pattern = re.compile(
            r'\{\s*"id"\s*:\s*"([^"]+)"\s*,\s*"text"\s*:\s*"([^"]+)"[^}]*\}',
            re.DOTALL
        )
        
        # Also try pattern where fields may be in different order
        alt_pattern = re.compile(
            r'\{\s*[^}]*?"id"\s*:\s*"([^"]+)"[^}]*?"text"\s*:\s*"([^"]+)"[^}]*\}',
            re.DOTALL
        )
        
        for match in req_pattern.finditer(text):
            try:
                # Try to extract the full matched object
                obj_text = match.group(0)
                # Parse it as JSON
                req = json.loads(obj_text)
                if req.get("id") and req.get("text"):
                    requirements.append(req)
            except:
                # If parsing fails, create a minimal object from the captured groups
                requirements.append({
                    "id": match.group(1),
                    "text": match.group(2),
                    "type": "OTHER"
                })
        
        # Remove duplicates
        seen_ids = set()
        unique_reqs = []
        for req in requirements:
            if req.get("id") not in seen_ids:
                seen_ids.add(req.get("id"))
                unique_reqs.append(req)
        
        logger.info(f"Salvaged {len(unique_reqs)} requirements from truncated response")
        return unique_reqs
    
    async def generate_block_response(
        self, 
        opportunity_id: int, 
        requirement: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate a response for a single requirement block.
        
        Args:
            opportunity_id: The opportunity ID
            requirement: Dict with id, text, type, section
            
        Returns:
            {
                "requirement_id": str,
                "response": str,
                "fit_score": int,
                "fit_rationale": str,
                "supporting_evidence": [...]
            }
        """
        # Get company context
        company_profile = await self._get_company_profile()
        past_performance = await self._get_past_performance_summary()
        
        prompt = RFI_BLOCK_RESPONSE_PROMPT.format(
            company_profile=company_profile,
            past_performance=past_performance,
            requirement_id=requirement.get("id", "REQ-???"),
            requirement_type=requirement.get("type", "OTHER"),
            requirement_text=requirement.get("text", "")
        )
        
        try:
            response = await self.ai_service.analyze_opportunity(prompt)
            
            if isinstance(response, dict):
                return response
            else:
                try:
                    return json.loads(response)
                except json.JSONDecodeError:
                    return {
                        "requirement_id": requirement.get("id"),
                        "response": response,
                        "fit_score": 50,
                        "fit_rationale": "Unable to assess fit",
                        "supporting_evidence": []
                    }
        except Exception as e:
            logger.error(f"Error generating block response: {e}")
            return {
                "requirement_id": requirement.get("id"),
                "response": f"Error generating response: {str(e)}",
                "fit_score": 0,
                "fit_rationale": "Error occurred",
                "supporting_evidence": []
            }
    
    async def generate_all_responses(
        self, 
        opportunity_id: int,
        requirements: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Generate responses for all requirements.
        
        Args:
            opportunity_id: The opportunity ID
            requirements: Optional list of requirements (will extract if not provided)
            
        Returns:
            {
                "requirements": [...with responses...],
                "overall_fit_score": int,
                "generated_at": str
            }
        """
        # Extract requirements if not provided
        if not requirements:
            extraction_result = await self.extract_requirements(opportunity_id)
            if extraction_result.get("error"):
                return extraction_result
            requirements = extraction_result.get("requirements", [])
        
        if not requirements:
            return {"error": "No requirements found", "requirements": []}
        
        # Generate response for each requirement
        responses = []
        total_fit_score = 0
        
        for req in requirements:
            response = await self.generate_block_response(opportunity_id, req)
            
            # Merge requirement with response
            req_with_response = {
                **req,
                "response": response.get("response", ""),
                "fit_score": response.get("fit_score", 50),
                "fit_rationale": response.get("fit_rationale", ""),
                "supporting_evidence": response.get("supporting_evidence", [])
            }
            responses.append(req_with_response)
            total_fit_score += response.get("fit_score", 50)
        
        overall_score = total_fit_score / len(responses) if responses else 0
        
        from datetime import datetime
        return {
            "requirements": responses,
            "total_count": len(responses),
            "overall_fit_score": round(overall_score, 1),
            "generated_at": datetime.utcnow().isoformat()
        }
    
    async def compile_full_response(
        self,
        opportunity_id: int,
        block_responses: List[Dict]
    ) -> Dict[str, Any]:
        """
        Compile all block responses into a complete RFI response document.
        
        Returns:
            {
                "document": str (Markdown),
                "word_count": int
            }
        """
        # Get opportunity details
        result = await self.db.execute(
            select(Opportunity).where(Opportunity.id == opportunity_id)
        )
        opportunity = result.scalar_one_or_none()
        
        if not opportunity:
            return {"error": "Opportunity not found"}
        
        company_profile = await self._get_company_profile()
        past_performance = await self._get_past_performance_summary()
        
        # Format block responses for prompt
        formatted_blocks = json.dumps(block_responses, indent=2)
        
        prompt = RFI_FULL_RESPONSE_PROMPT.format(
            company_profile=company_profile,
            past_performance=past_performance,
            block_responses=formatted_blocks,
            title=opportunity.title or "Sources Sought Notice",
            agency=opportunity.department or "N/A",
            naics_code=opportunity.naics_code or "N/A",
            description=(opportunity.description or "")[:2000]
        )
        
        try:
            document = await self.ai_service.generate_content(prompt)
            
            return {
                "document": document,
                "word_count": len(document.split()),
                "opportunity_title": opportunity.title
            }
        except Exception as e:
            logger.error(f"Error compiling full response: {e}")
            return {"error": str(e)}
    
    async def _get_company_profile(self) -> str:
        """Get the company profile for context."""
        # Try to get primary entity
        result = await self.db.execute(
            select(Entity).where(Entity.is_primary == True)
        )
        entity = result.scalar_one_or_none()
        
        if entity:
            profile_parts = [
                f"Company Name: {entity.legal_business_name}",
                f"UEI: {entity.uei}" if entity.uei else "",
                f"CAGE Code: {entity.cage_code}" if entity.cage_code else "",
            ]
            
            # Get business types from dedicated column
            if entity.business_types:
                if isinstance(entity.business_types, list):
                    type_names = [bt.get('businessTypeDescription', bt.get('type', str(bt))) if isinstance(bt, dict) else str(bt) for bt in entity.business_types[:5]]
                    profile_parts.append(f"Business Types: {', '.join(type_names)}")
            
            # Get capabilities from dedicated column
            if entity.capabilities:
                if isinstance(entity.capabilities, list):
                    profile_parts.append(f"Capabilities: {', '.join(entity.capabilities[:5])}")
            
            # Check full_response for additional NAICS data
            if entity.full_response and isinstance(entity.full_response, dict):
                core_data = entity.full_response.get('coreData', {})
                naics_list = core_data.get('naics', [])
                if naics_list:
                    codes = [str(n.get('naicsCode', '')) for n in naics_list[:5] if n.get('naicsCode')]
                    if codes:
                        profile_parts.append(f"NAICS Codes: {', '.join(codes)}")
            
            return "\n".join([p for p in profile_parts if p])
        
        # Fallback to default profile
        return GOVCON_PROFILE
    
    async def _get_past_performance_summary(self) -> str:
        """Get summary of past performance for context."""
        result = await self.db.execute(
            select(PastPerformance).limit(5)
        )
        past_performances = result.scalars().all()
        
        if not past_performances:
            return "No past performance records available."
        
        summaries = []
        for pp in past_performances:
            summary = f"- {pp.title or 'Project'}"
            
            # Get additional details from questionnaire_data if available
            if pp.questionnaire_data and isinstance(pp.questionnaire_data, dict):
                overview = pp.questionnaire_data.get('project_overview', {})
                if isinstance(overview, dict) and overview.get('content'):
                    summary += f": {overview.get('content', '')[:100]}..."
            
            summaries.append(summary)
        
        return "Recent Past Performance:\n" + "\n".join(summaries)

