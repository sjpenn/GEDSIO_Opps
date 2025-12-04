"""
Tests for extraction schemas validation.
"""

import pytest
from pydantic import ValidationError
from fedops_core.schemas.extraction_schemas import (
    BaseExtractedItem,
    SectionLSchema,
    SectionMSchema,
    SectionBSchema,
    CDRLSchema,
    FormattingRequirements,
    SubmissionRequirements,
    EvaluationFactor,
    CLINItem,
    CDRLItem,
)


class TestBaseExtractedItem:
    """Test base extracted item schema"""
    
    def test_valid_base_item(self):
        """Test valid base extracted item"""
        item = BaseExtractedItem(
            source_quote="This is the exact text from the document",
            section_reference="Section 3.2.1",
            confidence="high"
        )
        assert item.source_quote == "This is the exact text from the document"
        assert item.section_reference == "Section 3.2.1"
        assert item.confidence == "high"
    
    def test_base_item_without_optional_fields(self):
        """Test base item with only required fields"""
        item = BaseExtractedItem(
            source_quote="Required source quote"
        )
        assert item.source_quote == "Required source quote"
        assert item.section_reference is None
        assert item.confidence is None


class TestSectionLSchema:
    """Test Section L schema"""
    
    def test_valid_section_l(self):
        """Test valid Section L extraction"""
        data = {
            "formatting": {
                "font": "Arial 12pt",
                "margins": "1 inch all sides",
                "source_quote": "All proposals shall use Arial 12pt font with 1 inch margins"
            },
            "submission": {
                "method": "SAM.gov",
                "due_date": "2024-12-31 14:00 ET",
                "source_quote": "Proposals must be submitted via SAM.gov by December 31, 2024"
            },
            "volume_structure": [
                {
                    "volume_name": "Technical Volume",
                    "page_limit": 50,
                    "source_quote": "Technical volume shall not exceed 50 pages"
                }
            ]
        }
        
        schema = SectionLSchema(**data)
        assert schema.formatting.font == "Arial 12pt"
        assert schema.submission.method == "SAM.gov"
        assert len(schema.volume_structure) == 1


class TestSectionMSchema:
    """Test Section M schema"""
    
    def test_valid_section_m(self):
        """Test valid Section M extraction"""
        data = {
            "evaluation_approach": "Best Value Tradeoff",
            "factors": [
                {
                    "factor": "Technical Approach",
                    "weight": "Most Important",
                    "source_quote": "Technical approach is the most important factor",
                    "section_reference": "Section M.1"
                }
            ]
        }
        
        schema = SectionMSchema(**data)
        assert schema.evaluation_approach == "Best Value Tradeoff"
        assert len(schema.factors) == 1
        assert schema.factors[0].factor == "Technical Approach"


class TestSectionBSchema:
    """Test Section B schema"""
    
    def test_valid_section_b_with_clins(self):
        """Test valid Section B with CLIN structure"""
        data = {
            "clin_structure": [
                {
                    "clin": "0001",
                    "description": "Base Year Services",
                    "contract_type": "FFP",
                    "source_quote": "CLIN 0001: Base Year Services (FFP)",
                    "section_reference": "Section B"
                }
            ],
            "period_of_performance": {
                "base_period": "12 months",
                "option_periods": ["12 months", "12 months"],
                "source_quote": "Base period of 12 months with two 12-month options"
            }
        }
        
        schema = SectionBSchema(**data)
        assert len(schema.clin_structure) == 1
        assert schema.clin_structure[0].clin == "0001"
        assert schema.period_of_performance.base_period == "12 months"
        assert len(schema.period_of_performance.option_periods) == 2


class TestCDRLSchema:
    """Test CDRL schema"""
    
    def test_valid_cdrl(self):
        """Test valid CDRL extraction"""
        data = {
            "deliverables": [
                {
                    "cdrl_number": "A001",
                    "title": "Monthly Status Report",
                    "frequency": "MONTHLY",
                    "source_quote": "CDRL A001: Monthly Status Report",
                    "section_reference": "CDRL"
                }
            ]
        }
        
        schema = CDRLSchema(**data)
        assert len(schema.deliverables) == 1
        assert schema.deliverables[0].cdrl_number == "A001"
        assert schema.deliverables[0].frequency == "MONTHLY"


class TestSchemaValidation:
    """Test schema validation errors"""
    
    def test_missing_required_field(self):
        """Test that missing required fields raise validation error"""
        with pytest.raises(ValidationError):
            FormattingRequirements(
                font="Arial 12pt"
                # Missing source_quote
            )
    
    def test_invalid_confidence_level(self):
        """Test that invalid confidence level raises error"""
        with pytest.raises(ValidationError):
            BaseExtractedItem(
                source_quote="test",
                confidence="invalid"  # Should be high, medium, or low
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
