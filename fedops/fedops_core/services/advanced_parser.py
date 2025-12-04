"""
Advanced Parser Service

Uses the 'unstructured' library to parse documents with high fidelity,
preserving metadata like page numbers and identifying document structure.
"""

from typing import List, Dict, Any, Optional
from unstructured.partition.auto import partition
from unstructured.documents.elements import Element, NarrativeText, Title, Text

class ParsedElement:
    def __init__(self, text: str, type: str, page_number: Optional[int] = None, metadata: Dict = None):
        self.text = text
        self.type = type
        self.page_number = page_number
        self.metadata = metadata or {}

class AdvancedParser:
    def parse_document(self, file_path: str) -> List[ParsedElement]:
        """
        Parses a document and returns a list of structured elements.
        """
        try:
            elements = partition(filename=file_path)
            parsed_elements = []
            
            for el in elements:
                # Extract page number from metadata
                page_number = el.metadata.page_number if hasattr(el.metadata, 'page_number') else None
                
                parsed_elements.append(ParsedElement(
                    text=el.text,
                    type=type(el).__name__,
                    page_number=page_number,
                    metadata=el.metadata.to_dict()
                ))
                
            return parsed_elements
        except Exception as e:
            print(f"Error parsing document {file_path}: {e}")
            return []
