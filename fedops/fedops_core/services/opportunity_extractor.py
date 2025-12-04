"""
Opportunity Metadata Extractor Service

Extracts opportunity metadata from uploaded documents using AI analysis.
Auto-populates form fields to reduce manual data entry.
"""

import re
import json
from typing import Dict, List, Optional, Any
from datetime import datetime

from fedops_core.settings import settings
from fedops_core.services.ai_service import AIService

# Try to import AdvancedParser, but make it optional
try:
    from fedops_core.services.advanced_parser import AdvancedParser
    HAS_ADVANCED_PARSER = True
except ImportError:
    HAS_ADVANCED_PARSER = False
    print("Warning: AdvancedParser not available, will use basic text extraction")

class OpportunityExtractor:
    """Service for extracting opportunity metadata from documents using AI"""
    
    def __init__(self):
        self.ai_service = AIService()
        self.parser = AdvancedParser() if HAS_ADVANCED_PARSER else None
    
    @staticmethod
    def parse_full_parent_path(full_path: str) -> Dict[str, str]:
        """
        Parse fullParentPathName from SAM.gov format into department and sub-tier.
        
        SAM.gov format examples:
        - "DEPT OF DEFENSE.DEPT OF THE NAVY"
        - "DEPT OF HOMELAND SECURITY.TRANSPORTATION SECURITY ADMINISTRATION"
        - "DEPT OF DEFENSE"  (no sub-tier)
        
        Args:
            full_path: The fullParentPathName string from SAM.gov
            
        Returns:
            Dictionary with 'department' and 'sub_tier' keys
            Example: {"department": "DEPT OF DEFENSE", "sub_tier": "DEPT OF THE NAVY"}
        """
        if not full_path or not isinstance(full_path, str):
            return {"department": "N/A", "sub_tier": "N/A"}
        
        # Split by period (SAM.gov uses period as separator)
        parts = full_path.split('.')
        
        # Clean up parts (strip whitespace)
        parts = [part.strip() for part in parts if part.strip()]
        
        if not parts:
            return {"department": "N/A", "sub_tier": "N/A"}
        
        # First part is always the department
        department = parts[0]
        
        # Second part (if exists) is the sub-tier
        sub_tier = parts[1] if len(parts) > 1 else "N/A"
        
        return {
            "department": department,
            "sub_tier": sub_tier
        }
    
    async def extract_from_files(self, file_paths: List[str]) -> Dict[str, Any]:
        """
        Extract opportunity metadata from one or more document files.
        
        Args:
            file_paths: List of absolute paths to document files
            
        Returns:
            Dictionary with extracted fields and confidence scores:
            {
                "title": {"value": str, "confidence": float},
                "solicitation_number": {"value": str, "confidence": float},
                "department": {"value": str, "confidence": float},
                "naics_code": {"value": str, "confidence": float},
                "type_of_set_aside": {"value": str, "confidence": float},
                "description": {"value": str, "confidence": float},
                "response_deadline": {"value": str, "confidence": float},
                "posted_date": {"value": str, "confidence": float},
                "type": {"value": str, "confidence": float}
            }
        """
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"Starting metadata extraction from {len(file_paths)} files")
        
        # Parse all documents
        all_content = []
        for file_path in file_paths:
            logger.info(f"Processing file: {file_path}")
            content = None
            
            try:
                # Try AdvancedParser first if available
                if self.parser:
                    logger.info(f"Using AdvancedParser for {file_path}")
                    parsed_elements = self.parser.parse_document(file_path)
                    if parsed_elements:
                        content = " ".join([el.text for el in parsed_elements])
                        logger.info(f"AdvancedParser extracted {len(content)} characters from {file_path}")
                
                # If AdvancedParser failed or not available, try PDF-specific parsing for PDFs
                if not content and file_path.lower().endswith('.pdf'):
                    logger.info(f"Attempting PDF-specific parsing for {file_path}")
                    content = self._parse_pdf(file_path)
                    if content:
                        logger.info(f"PDF parser extracted {len(content)} characters from {file_path}")
                
                # Fallback to basic text reading for non-PDF or if PDF parsing failed
                if not content:
                    logger.info(f"Using basic text reading for {file_path}")
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        logger.info(f"Basic read extracted {len(content)} characters from {file_path}")
                
                if content and content.strip():
                    all_content.append(content)
                else:
                    logger.warning(f"No content extracted from {file_path}")
                    
            except Exception as e:
                logger.error(f"Error parsing {file_path}: {e}", exc_info=True)
                # Final fallback: try reading as plain text
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        if content and content.strip():
                            logger.info(f"Fallback read {len(content)} characters from {file_path}")
                            all_content.append(content)
                except Exception as read_error:
                    logger.error(f"Error reading {file_path}: {read_error}", exc_info=True)
        
        if not all_content:
            logger.warning("No content extracted from any files, returning empty result")
            return self._empty_result()
        
        # Combine content from all documents
        combined_content = "\n\n=== DOCUMENT SEPARATOR ===\n\n".join(all_content)
        logger.info(f"Combined content length: {len(combined_content)} characters")
        
        # Limit content size for API
        if len(combined_content) > 50000:
            logger.info(f"Truncating content from {len(combined_content)} to 50000 characters")
            combined_content = combined_content[:50000]
        
        # Extract metadata using AI
        logger.info("Calling AI to extract metadata")
        extracted_data = await self._ai_extract_metadata(combined_content)
        logger.info(f"AI extraction complete. Extracted fields: {list(extracted_data.keys())}")
        
        # Log which fields have values
        fields_with_values = [k for k, v in extracted_data.items() if v.get('value')]
        logger.info(f"Fields with values: {fields_with_values}")
        
        return extracted_data
    
    def _parse_pdf(self, file_path: str) -> Optional[str]:
        """Parse PDF file using pypdf library as fallback"""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            # Try using pypdf (PyPDF2's successor)
            try:
                from pypdf import PdfReader
                logger.info(f"Using pypdf to parse {file_path}")
                reader = PdfReader(file_path)
                text_parts = []
                for page in reader.pages:
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)
                content = "\n".join(text_parts)
                if content.strip():
                    return content
            except ImportError:
                logger.debug("pypdf not available, trying PyPDF2")
                pass
            
            # Fallback to PyPDF2 if pypdf not available
            try:
                from PyPDF2 import PdfReader
                logger.info(f"Using PyPDF2 to parse {file_path}")
                reader = PdfReader(file_path)
                text_parts = []
                for page in reader.pages:
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)
                content = "\n".join(text_parts)
                if content.strip():
                    return content
            except ImportError:
                logger.warning("Neither pypdf nor PyPDF2 available for PDF parsing")
                pass
                
        except Exception as e:
            logger.error(f"Error in PDF parsing: {e}", exc_info=True)
        
        return None

    
    async def _ai_extract_metadata(self, content: str) -> Dict[str, Any]:
        """Use AI to extract structured metadata from document content"""
        import logging
        logger = logging.getLogger(__name__)
        
        prompt = f"""
You are analyzing government solicitation documents to extract key metadata.

Extract the following information from the document:

1. **Title**: The official opportunity/solicitation title
2. **Solicitation Number**: RFP number, solicitation number, or notice ID (e.g., "RFQ-2024-001", "FA8732-24-R-0001")
3. **Department/Agency**: The issuing government department or agency
4. **NAICS Code**: The primary NAICS code (6-digit number)
5. **Set Aside Type**: Type of set-aside (e.g., "Small Business", "8(a)", "HUBZone", "SDVOSB", "WOSB", or "None")
6. **Description**: A brief summary of the opportunity (2-3 sentences)
7. **Response Deadline**: The proposal submission deadline (extract as ISO date if possible)
8. **Posted Date**: When the opportunity was posted (extract as ISO date if possible)
9. **Type**: Opportunity type (e.g., "Solicitation", "Presolicitation", "Sources Sought", "RFI", "Combined Synopsis/Solicitation")

For each field, also provide a confidence score from 0.0 to 1.0:
- 1.0 = Explicitly stated and clearly identified
- 0.7-0.9 = Strongly implied or inferred from context
- 0.4-0.6 = Weak inference or partial information
- 0.0-0.3 = Not found or very uncertain

Return ONLY a JSON object with this exact structure:
{{
  "title": {{"value": "extracted title", "confidence": 0.95}},
  "solicitation_number": {{"value": "RFQ-2024-001", "confidence": 1.0}},
  "department": {{"value": "Department of Defense", "confidence": 0.9}},
  "naics_code": {{"value": "541511", "confidence": 0.8}},
  "type_of_set_aside": {{"value": "Small Business", "confidence": 0.85}},
  "description": {{"value": "Brief summary...", "confidence": 0.9}},
  "response_deadline": {{"value": "2024-12-31", "confidence": 0.95}},
  "posted_date": {{"value": "2024-11-01", "confidence": 0.9}},
  "type": {{"value": "Solicitation", "confidence": 1.0}}
}}

If a field cannot be found, set value to null and confidence to 0.0.

Document content:
{content}
"""
        
        try:
            logger.info("Sending request to AI model for metadata extraction")
            
            # Use AIService which handles all providers and JSON extraction
            result = await self.ai_service.analyze_opportunity(prompt)
            
            logger.info(f"AI response received")
            
            # Check if we got a valid result
            if result and isinstance(result, dict):
                # Check if it's an error response from AIService
                if result.get('status') == 'error':
                    logger.error(f"AI service returned error: {result.get('error')}")
                    return self._empty_result()
                
                logger.info(f"Successfully extracted metadata with {len(result)} fields")
                
                # Validate and clean the extracted data
                validated = self._validate_extraction(result)
                logger.info("Validation complete")
                return validated
            else:
                logger.error("AI service returned invalid response")
                return self._empty_result()
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}", exc_info=True)
            logger.error(f"Failed to parse: {json_str if 'json_str' in locals() else 'N/A'}")
            return self._empty_result()
        except Exception as e:
            logger.error(f"Error extracting metadata with AI: {e}", exc_info=True)
            return self._empty_result()
    
    def _validate_extraction(self, extracted: Dict) -> Dict[str, Any]:
        """Validate and clean extracted data"""
        
        result = {}
        
        # Define expected fields
        fields = [
            "title", "solicitation_number", "department", "naics_code",
            "type_of_set_aside", "description", "response_deadline",
            "posted_date", "type"
        ]
        
        for field in fields:
            if field in extracted and isinstance(extracted[field], dict):
                value = extracted[field].get("value")
                confidence = extracted[field].get("confidence", 0.0)
                
                # Clean up the value
                if value and isinstance(value, str):
                    value = value.strip()
                    if value.lower() in ["null", "none", "n/a", "not found", ""]:
                        value = None
                
                # Validate confidence score
                try:
                    confidence = float(confidence)
                    confidence = max(0.0, min(1.0, confidence))
                except (ValueError, TypeError):
                    confidence = 0.0
                
                result[field] = {
                    "value": value,
                    "confidence": confidence
                }
            else:
                result[field] = {"value": None, "confidence": 0.0}
        
        # Special handling for set-aside mapping
        if result["type_of_set_aside"]["value"]:
            result["type_of_set_aside"]["value"] = self._map_set_aside(
                result["type_of_set_aside"]["value"]
            )
        
        # Special handling for opportunity type
        if result["type"]["value"]:
            result["type"]["value"] = self._map_opportunity_type(
                result["type"]["value"]
            )
        
        return result
    
    def _map_set_aside(self, value: str) -> str:
        """Map extracted set-aside to standard codes"""
        value_lower = value.lower()
        
        mapping = {
            "small business": "SBA",
            "sba": "SBA",
            "8(a)": "8A",
            "8a": "8A",
            "hubzone": "HZC",
            "hub zone": "HZC",
            "sdvosb": "SDVOSBC",
            "service-disabled veteran": "SDVOSBC",
            "wosb": "WOSB",
            "women-owned": "WOSB",
            "edwosb": "WOSB",
            "none": "NONE",
            "unrestricted": "NONE"
        }
        
        for key, code in mapping.items():
            if key in value_lower:
                return code
        
        return value  # Return original if no mapping found
    
    def _map_opportunity_type(self, value: str) -> str:
        """Map extracted opportunity type to standard values"""
        value_lower = value.lower()
        
        mapping = {
            "solicitation": "Solicitation",
            "presolicitation": "Presolicitation",
            "pre-solicitation": "Presolicitation",
            "sources sought": "Sources Sought",
            "source sought": "Sources Sought",
            "rfi": "RFI",
            "request for information": "RFI",
            "combined synopsis": "Combined Synopsis/Solicitation",
            "combined synopsis/solicitation": "Combined Synopsis/Solicitation"
        }
        
        for key, standard_type in mapping.items():
            if key in value_lower:
                return standard_type
        
        return value  # Return original if no mapping found
    
    def _empty_result(self) -> Dict[str, Any]:
        """Return empty result structure"""
        fields = [
            "title", "solicitation_number", "department", "naics_code",
            "type_of_set_aside", "description", "response_deadline",
            "posted_date", "type"
        ]
        
        return {
            field: {"value": None, "confidence": 0.0}
            for field in fields
        }
