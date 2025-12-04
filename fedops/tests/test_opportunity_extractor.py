"""
Tests for OpportunityExtractor service
"""

import pytest
from fedops_core.services.opportunity_extractor import OpportunityExtractor


class TestParseFullParentPath:
    """Test fullParentPathName parsing"""
    
    def test_parse_with_subtier(self):
        """Test parsing with both department and sub-tier"""
        result = OpportunityExtractor.parse_full_parent_path(
            "DEPT OF DEFENSE.DEPT OF THE NAVY"
        )
        assert result["department"] == "DEPT OF DEFENSE"
        assert result["sub_tier"] == "DEPT OF THE NAVY"
    
    def test_parse_without_subtier(self):
        """Test parsing with only department"""
        result = OpportunityExtractor.parse_full_parent_path(
            "DEPT OF DEFENSE"
        )
        assert result["department"] == "DEPT OF DEFENSE"
        assert result["sub_tier"] == "N/A"
    
    def test_parse_with_multiple_periods(self):
        """Test parsing with multiple levels (takes first two)"""
        result = OpportunityExtractor.parse_full_parent_path(
            "DEPT OF DEFENSE.DEPT OF THE NAVY.NAVAL AIR SYSTEMS COMMAND"
        )
        assert result["department"] == "DEPT OF DEFENSE"
        assert result["sub_tier"] == "DEPT OF THE NAVY"
    
    def test_parse_empty_string(self):
        """Test parsing empty string"""
        result = OpportunityExtractor.parse_full_parent_path("")
        assert result["department"] == "N/A"
        assert result["sub_tier"] == "N/A"
    
    def test_parse_none(self):
        """Test parsing None"""
        result = OpportunityExtractor.parse_full_parent_path(None)
        assert result["department"] == "N/A"
        assert result["sub_tier"] == "N/A"
    
    def test_parse_with_whitespace(self):
        """Test parsing with extra whitespace"""
        result = OpportunityExtractor.parse_full_parent_path(
            "  DEPT OF DEFENSE  .  DEPT OF THE NAVY  "
        )
        assert result["department"] == "DEPT OF DEFENSE"
        assert result["sub_tier"] == "DEPT OF THE NAVY"
    
    def test_parse_homeland_security(self):
        """Test parsing DHS example"""
        result = OpportunityExtractor.parse_full_parent_path(
            "DEPT OF HOMELAND SECURITY.TRANSPORTATION SECURITY ADMINISTRATION"
        )
        assert result["department"] == "DEPT OF HOMELAND SECURITY"
        assert result["sub_tier"] == "TRANSPORTATION SECURITY ADMINISTRATION"
