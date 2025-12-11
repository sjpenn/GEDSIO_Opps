
import pytest
from fedops_core.services.perplexity_service import PerplexityService

def test_parse_org_node_recursive():
    """Verify that _parse_org_node correctly parses deep hierarchies."""
    service = PerplexityService()
    
    # Mock deeply nested data structure (mirroring LLM response format)
    # Level 1: Agency Head
    # Level 2: Line Office
    # Level 3: Program Office (AJM-1)
    # Level 4: Specific Team/Unit
    
    raw_data = {
        "name": "Jane Doe",
        "title": "Agency Head",
        "icon_type": "leadership",
        "children": [
            {
                "name": "John Smith",
                "title": "VP of Operations",
                "icon_type": "default",
                "children": [
                    {
                        "name": "AJM-1",
                        "title": "Technical Operations",
                        "icon_type": "aviation",
                        "children": [
                            {
                                "name": "Team Alpha",
                                "title": "Field Support",
                                "icon_type": "default",
                                "children": []
                            }
                        ]
                    }
                ]
            }
        ]
    }
    
    result = service._parse_org_node(raw_data)
    
    # Verify Level 1
    assert result.name == "Jane Doe"
    assert result.title == "Agency Head"
    assert len(result.children) == 1
    
    # Verify Level 2
    level2 = result.children[0]
    assert level2.name == "John Smith"
    assert len(level2.children) == 1
    
    # Verify Level 3 (AJM-1)
    level3 = level2.children[0]
    assert level3.name == "AJM-1"
    assert level3.title == "Technical Operations"
    assert len(level3.children) == 1
    
    # Verify Level 4
    level4 = level3.children[0]
    assert level4.name == "Team Alpha"
    assert len(level4.children) == 0

def test_parse_org_node_empty_children():
    """Verify handling of nodes with no children."""
    service = PerplexityService()
    
    raw_data = {
        "name": "Solo Node",
        "title": "Director",
        "children": []
    }
    
    result = service._parse_org_node(raw_data)
    assert result.name == "Solo Node"
    assert len(result.children) == 0

