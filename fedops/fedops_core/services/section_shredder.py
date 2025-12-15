"""
Section Shredder Service - Splits combined RFP documents into individual sections.

Federal solicitations often combine multiple standard sections (A-M) into a single
PDF document. This service detects section boundaries and extracts content for 
each section separately, enabling more accurate extraction with section-specific prompts.
"""

import re
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SectionBoundary:
    """Represents a detected section boundary"""
    section_letter: str
    section_name: str
    start_position: int
    end_position: Optional[int] = None
    confidence: str = "high"  # high, medium, low


class SectionShredder:
    """
    Service for splitting combined RFP documents into individual sections.
    
    Uses pattern matching and heuristics to detect standard solicitation sections:
    - Section A: Solicitation/Contract Form
    - Section B: Supplies or Services and Prices/Costs
    - Section C: Description/Specs/Statement of Work
    - Section D: Packaging and Marking
    - Section E: Inspection and Acceptance
    - Section F: Deliveries or Performance
    - Section G: Contract Administration Data
    - Section H: Special Contract Requirements
    - Section I: Contract Clauses
    - Section J: List of Attachments
    - Section K: Representations, Certifications, and Other Statements
    - Section L: Instructions, Conditions, and Notices to Offerors
    - Section M: Evaluation Factors for Award
    """
    
    # Standard section definitions for federal solicitations
    SECTION_DEFINITIONS = {
        'A': 'Solicitation/Contract Form',
        'B': 'Supplies or Services and Prices/Costs',
        'C': 'Description/Specifications/Statement of Work',
        'D': 'Packaging and Marking',
        'E': 'Inspection and Acceptance',
        'F': 'Deliveries or Performance',
        'G': 'Contract Administration Data',
        'H': 'Special Contract Requirements',
        'I': 'Contract Clauses',
        'J': 'List of Attachments',
        'K': 'Representations, Certifications, and Other Statements',
        'L': 'Instructions, Conditions, and Notices to Offerors',
        'M': 'Evaluation Factors for Award',
    }
    
    # Patterns to detect section headers
    SECTION_HEADER_PATTERNS = [
        # "SECTION L - Instructions to Offerors" or "SECTION L: Instructions"
        r'(?:^|\n)\s*(?:#+\s*)?SECTION\s+([A-M])(?:[\s\-\.:]+|$)(?=[A-Z0-9]|$)(.*)',
        
        # "PART I - SECTION L" or "Part I Section L"
        r'(?:^|\n)\s*(?:#+\s*)?PART\s+[IVX0-9]+\s*(?:[-–:]\s*)?SECTION\s+([A-M])(?:[\s\-\.:]+|$)(.*)',
        
        # "L. Instructions to Offerors" (at start of line)
        r'(?:^|\n)\s*(?:#+\s*)?([A-M])\.\s+([A-Z][^\n]+)',
        
        # "(L) Instructions" or "(M) Evaluation"
        r'(?:^|\n)\s*(?:#+\s*)?\(([A-M])\)\s+([^\n]+)',
        
        # "L - Instructions" or "M - Evaluation Factors" (Fixed \s+ to \s*)
        r'(?:^|\n)\s*(?:#+\s*)?([A-M])\s*[-–]\s*([A-Z][^\n]+)',
        
        # DoD format: "L INSTRUCTIONS TO OFFERORS" (letter, space, ALL CAPS TITLE)
        r'(?:^|\n)\s*(?:#+\s*)?([LMHBCIK])\s+([A-Z\s]{3,}[^\n]*)',
    ]

    
    # Fallback content markers when headers aren't explicit
    CONTENT_MARKERS = {
        'L': [
            'instructions to offerors',
            'instructions, conditions, and notices',
            'proposal submission',
            'proposal preparation instructions',
            'proposal preparation',
            'format and content',
            'page limitations',
            'page limit',
            'volume i',
            'volume ii',
            'volume 1',
            'volume 2',
            'sf 33',
            'sf33',
            'submission instructions',
            'offeror shall submit',
            'offerors shall submit',
            'submit proposals',
            'proposal format',
            'offer preparation',
            'questions regarding this solicitation',
            '52.212-1',
            'addendum to 52.212-1',
            'instructions, conditions',
            'notices to offerors',
        ],
        'M': [
            'evaluation factors',
            'evaluation criteria',
            'basis for award',
            'source selection',
            'technical evaluation',
            'proposal evaluation',
            'best value',
            'lowest price technically acceptable',
            'lpta',
            'tradeoff',
            'award will be made',
            '52.212-2',
            'addendum to 52.212-2',
        ],
        'H': [
            'special contract requirements',
            'key personnel',
            'organizational conflict',
            'security requirements',
            'place of performance',
            'transition requirements',
            'transition plan',
            'non-disclosure',
            'nda',
            'contractor personnel',
            'subcontracting',
            'small business subcontracting',
            'government furnished',
            'gfe',
            'gfp',
        ],
        'B': [
            'supplies or services and prices',
            'contract line item',
            'clin',
            'pricing schedule',
            'price/cost',
            'base year',
            'option year',
            'period of performance',
        ],
        'I': [
            'contract clauses',
            'far 52.',
            'dfars 252.',
            'dfars',
            'clauses incorporated',
            'clauses by reference',
            'full text clauses',
        ],
        'K': [
            'representations and certifications',
            'certifications and representations',
            'offeror representations',
            'annual representations',
        ],
        'C': [
            'statement of work',
            'performance work statement',
            'scope of work',
            'statement of objectives',
            'pws',
            'sow',
            'contractor shall',
            'scope:',
        ],
    }

    
    def __init__(self):
        self._compiled_patterns = [
            re.compile(pattern, re.IGNORECASE | re.MULTILINE)
            for pattern in self.SECTION_HEADER_PATTERNS
        ]
    
    def detect_sections(self, content: str) -> List[SectionBoundary]:
        """
        Detect section boundaries in the document content.
        
        Args:
            content: Full document text
            
        Returns:
            List of SectionBoundary objects sorted by position
        """
        sections = []
        
        # First, try explicit header patterns
        for pattern in self._compiled_patterns:
            for match in pattern.finditer(content):
                groups = match.groups()
                section_letter = groups[0].upper()
                section_name = groups[1].strip() if len(groups) > 1 and groups[1] else ""
                
                # Use standard definition if name not extracted
                if not section_name:
                    section_name = self.SECTION_DEFINITIONS.get(section_letter, "")
                
                boundary = SectionBoundary(
                    section_letter=section_letter,
                    section_name=section_name,
                    start_position=match.start(),
                    confidence="high"
                )
                sections.append(boundary)
        
        # Deduplicate by section letter (keep earliest occurrence)
        seen = {}
        deduplicated = []
        for section in sorted(sections, key=lambda s: s.start_position):
            if section.section_letter not in seen:
                seen[section.section_letter] = section
                deduplicated.append(section)
        
        # Check for missing critical sections or few results
        # Never discard explicit headers - they are the strongest signal!
        found_letters = {s.section_letter for s in deduplicated}
        
        # If we have few sections (< 3) OR are missing any critical sections (L/M/C),
        # try to supplement with content markers.
        # Critical sections we really want to find:
        critical_to_check = {'L', 'M', 'C', 'H', 'B', 'I'}
        missing_critical = critical_to_check - found_letters
        
        if len(deduplicated) < 3 or missing_critical:
            logger.info(f"Checking content markers (Found: {list(found_letters)}, Missing Critical: {list(missing_critical)})")
            
            # We look for all markers, but could optimize to look only for missing
            # For robustness, we look for all and only add if new
            marker_sections = self._detect_by_content_markers(content)
            
            for section in marker_sections:
                if section.section_letter not in found_letters:
                    deduplicated.append(section)
                    found_letters.add(section.section_letter)
                    logger.info(f"Added Section {section.section_letter} via content markers")
        
        # Calculate end positions
        sorted_sections = sorted(deduplicated, key=lambda s: s.start_position)
        for i, section in enumerate(sorted_sections):
            if i < len(sorted_sections) - 1:
                section.end_position = sorted_sections[i + 1].start_position
            else:
                section.end_position = len(content)
        
        logger.info(f"Detected {len(sorted_sections)} sections: {[s.section_letter for s in sorted_sections]}")
        return sorted_sections


    
    def _detect_by_content_markers(self, content: str) -> List[SectionBoundary]:
        """
        Detect sections using content markers when explicit headers aren't found.
        Uses regex to handle multi-line markers (replacing spaces with \s+).
        """
        sections = []
        
        for section_letter, markers in self.CONTENT_MARKERS.items():
            for marker in markers:
                # Convert marker text to regex pattern that matches flexible whitespace
                # Escape the marker first, then replace escaped spaces with \s+
                marker_pattern = re.escape(marker).replace(r'\ ', r'\s+')
                
                # Search using regex (IGNORECASE)
                match = re.search(marker_pattern, content, re.IGNORECASE)
                
                if match:
                    logger.info(f"Found content marker '{marker}' for Section {section_letter} at {match.start()} (Regex)")
                    
                    # Find the start of the paragraph/section (look backwards for double newline)
                    # We search in the substring before the match
                    pre_match_content = content[:match.start()]
                    para_start = pre_match_content.rfind('\n\n')
                    
                    if para_start == -1:
                        # Fallback: just go back 100 chars
                        para_start = max(0, match.start() - 100)
                    else:
                        para_start += 2  # Skip the newlines
                    
                    sections.append(SectionBoundary(
                        section_letter=section_letter,
                        section_name=self.SECTION_DEFINITIONS.get(section_letter, ""),
                        start_position=para_start,
                        confidence="medium"
                    ))
                    break  # Only use first match per section
        
        return sections
    
    def shred(self, content: str) -> Dict[str, str]:
        """
        Split document content into individual sections.
        
        Args:
            content: Full document text
            
        Returns:
            Dictionary mapping section letters to their content
        """
        sections = self.detect_sections(content)
        
        result = {}
        for section in sections:
            section_content = content[section.start_position:section.end_position]
            result[section.section_letter] = section_content.strip()
            
            logger.debug(
                f"Section {section.section_letter}: "
                f"{len(section_content)} chars, confidence={section.confidence}"
            )
        
        return result
    
    def shred_to_extractions(self, content: str) -> Dict[str, dict]:
        """
        Split document and prepare for extraction with metadata.
        
        Args:
            content: Full document text
            
        Returns:
            Dictionary mapping section letters to extraction context
        """
        sections = self.detect_sections(content)
        
        result = {}
        for section in sections:
            section_content = content[section.start_position:section.end_position]
            result[section.section_letter] = {
                'content': section_content.strip(),
                'section_name': section.section_name,
                'confidence': section.confidence,
                'char_count': len(section_content),
            }
        
        return result
    
    def get_critical_sections(self, shredded: Dict[str, str]) -> Dict[str, str]:
        """
        Extract only the critical sections for proposal preparation.
        
        Critical sections are: L (Instructions), M (Evaluation), 
        C/SOW, H (Special Requirements), B (Pricing)
        
        Args:
            shredded: Dictionary from shred() method
            
        Returns:
            Filtered dictionary with only critical sections
        """
        critical_letters = {'L', 'M', 'C', 'H', 'B', 'I'}
        return {k: v for k, v in shredded.items() if k in critical_letters}
