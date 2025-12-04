"""
Page Limit Extractor Service

Extracts page limit requirements from solicitation documents (Section L)
using AI to identify section-specific limits and their source references.
"""
from typing import Dict, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import google.generativeai as genai

from fedops_core.db.models import StoredFile, Opportunity
from fedops_core.settings import settings
from fedops_core.services.ai_service import AIService

class PageLimitExtractor:
    """Extract page limits from Section L and other solicitation sections"""
    
    def __init__(self):
        self.ai_service = AIService()
    
    async def extract_page_limits(
        self, 
        db: AsyncSession, 
        opportunity_id: int
    ) -> Dict[str, Dict[str, any]]:
        """
        Extract page limits from solicitation documents.
        
        Args:
            db: Database session
            opportunity_id: Opportunity ID to extract limits for
            
        Returns:
            {
                "executive_summary": {"limit": 2, "source": "Section L.5.1"},
                "technical_approach": {"limit": 15, "source": "Section L.5.2"},
                ...
            }
        """
        # Get solicitation documents for this opportunity
        documents = await self._get_solicitation_documents(db, opportunity_id)
        
        if not documents:
            print(f"No solicitation documents found for opportunity {opportunity_id}")
            return {}
        
        # Extract page limits using AI
        page_limits = {}
        for doc in documents:
            extracted = await self._extract_from_document(doc)
            page_limits.update(extracted)
        
        return page_limits
    
    async def _get_solicitation_documents(
        self, 
        db: AsyncSession, 
        opportunity_id: int
    ) -> List[StoredFile]:
        """Fetch solicitation documents for the opportunity"""
        stmt = select(StoredFile).where(
            StoredFile.opportunity_id == opportunity_id,
            StoredFile.file_type.in_(['pdf', 'txt', 'docx'])
        )
        result = await db.execute(stmt)
        return result.scalars().all()
    
    async def _extract_from_document(self, document: StoredFile) -> Dict[str, Dict]:
        """Extract page limits from a single document using AI"""
        
        # Get document content
        content = document.parsed_content or ""
        if not content:
            return {}
        
        # Focus on Section L content
        section_l_content = self._extract_section_l(content)
        if not section_l_content:
            # If no Section L found, try full document
            section_l_content = content[:50000]  # Limit to first 50k chars
        
        # Use AI to extract page limits
        prompt = self._build_extraction_prompt(section_l_content)
        
        try:
            # Use AIService to get the response
            # Note: AIService.analyze_opportunity returns a dict (JSON), so we don't need _parse_ai_response if it works well
            # But _parse_ai_response handles raw text too, so let's see what AIService gives us.
            # Actually, AIService.analyze_opportunity tries to return a dict.
            
            result = await self.ai_service.analyze_opportunity(prompt)
            
            if result and isinstance(result, dict) and result.get('status') != 'error':
                 # Validate structure matches what we expect
                validated = {}
                for key, value in result.items():
                    if isinstance(value, dict) and 'limit' in value and 'source' in value:
                        try:
                            validated[key] = {
                                'limit': int(value['limit']),
                                'source': str(value['source'])
                            }
                        except (ValueError, TypeError):
                            continue
                return validated
            
            return {}
        except Exception as e:
            print(f"Error extracting page limits from {document.filename}: {e}")
            return {}
    
    def _extract_section_l(self, content: str) -> str:
        """
        Extract Section L content from document.
        Looks for common patterns like "Section L", "L -", "SECTION L", etc.
        """
        content_upper = content.upper()
        
        # Common Section L indicators
        patterns = [
            "SECTION L",
            "SECTION L -",
            "SECTION L:",
            "L. INSTRUCTIONS TO OFFERORS",
            "L - INSTRUCTIONS TO OFFERORS"
        ]
        
        start_idx = -1
        for pattern in patterns:
            idx = content_upper.find(pattern)
            if idx != -1:
                start_idx = idx
                break
        
        if start_idx == -1:
            return ""
        
        # Find end of Section L (usually Section M or end of document)
        end_patterns = ["SECTION M", "\nM.", "\nM -"]
        end_idx = len(content)
        
        for pattern in end_patterns:
            idx = content_upper.find(pattern, start_idx)
            if idx != -1:
                end_idx = idx
                break
        
        # Extract Section L content (limit to reasonable size)
        section_l = content[start_idx:min(end_idx, start_idx + 30000)]
        return section_l
    
    def _build_extraction_prompt(self, section_l_content: str) -> str:
        """Build AI prompt for extracting page limits"""
        return f"""You are analyzing a government solicitation document to extract page limit requirements for proposal sections.

SOLICITATION CONTENT:
{section_l_content}

TASK:
Extract all page limit requirements from this content. For each section that has a page limit, identify:
1. The section name (e.g., "Executive Summary", "Technical Approach", "Past Performance")
2. The numeric page limit
3. The exact source reference (e.g., "Section L.5.1", "Section L.5.2, Page 15")

IMPORTANT:
- Look for phrases like "not to exceed X pages", "maximum X pages", "limited to X pages", "shall not exceed X pages"
- Normalize section names to common proposal sections
- Include the full source reference with section number

OUTPUT FORMAT (JSON):
Return a JSON object mapping normalized section names to their limits and sources:
{{
    "executive_summary": {{
        "limit": 2,
        "source": "Section L.5.1"
    }},
    "technical_approach": {{
        "limit": 15,
        "source": "Section L.5.2"
    }},
    "management_plan": {{
        "limit": 10,
        "source": "Section L.5.3"
    }}
}}

SECTION NAME NORMALIZATION:
- "Executive Summary" -> "executive_summary"
- "Technical Approach", "Technical Solution", "Technical Volume" -> "technical_approach"
- "Management Plan", "Management Approach" -> "management_plan"
- "Past Performance" -> "past_performance"
- "Key Personnel", "Staffing Plan" -> "key_personnel"
- "Quality Assurance", "QA Plan" -> "quality_assurance"
- "Transition Plan", "Phase-in Plan" -> "transition_plan"

Return ONLY the JSON object, no other text."""
    
    def _parse_ai_response(self, response: str) -> Dict[str, Dict]:
        """Parse AI response to extract page limits"""
        import json
        import re
        
        # Try to extract JSON from response
        json_match = re.search(r'\{[\s\S]*\}', response)
        if not json_match:
            return {}
        
        try:
            page_limits = json.loads(json_match.group(0))
            
            # Validate structure
            validated = {}
            for key, value in page_limits.items():
                if isinstance(value, dict) and 'limit' in value and 'source' in value:
                    validated[key] = {
                        'limit': int(value['limit']),
                        'source': str(value['source'])
                    }
            
            return validated
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Error parsing AI response: {e}")
            return {}
    
    def match_to_section_title(
        self, 
        section_title: str, 
        page_limits: Dict[str, Dict]
    ) -> Optional[Dict[str, any]]:
        """
        Match a section title to extracted page limits.
        
        Args:
            section_title: Actual section title (e.g., "2.1 Technical Solution")
            page_limits: Extracted page limits dict
            
        Returns:
            {"limit": 15, "source": "Section L.5.2"} or None
        """
        title_lower = section_title.lower()
        
        # Direct key matching
        for key in page_limits.keys():
            if key in title_lower or title_lower in key:
                return page_limits[key]
        
        # Fuzzy matching based on keywords
        keyword_map = {
            'executive': 'executive_summary',
            'technical': 'technical_approach',
            'management': 'management_plan',
            'past performance': 'past_performance',
            'personnel': 'key_personnel',
            'staffing': 'key_personnel',
            'quality': 'quality_assurance',
            'transition': 'transition_plan',
            'phase': 'transition_plan'
        }
        
        for keyword, normalized_key in keyword_map.items():
            if keyword in title_lower and normalized_key in page_limits:
                return page_limits[normalized_key]
        
        return None
