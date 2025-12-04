"""
Tests for Docling service integration.
"""

import pytest
from pathlib import Path
from fedops_core.services.docling_service import DoclingService, DoclingResult, TableData


@pytest.fixture
def docling_service():
    """Create DoclingService instance"""
    return DoclingService()


class TestDoclingService:
    """Test Docling service functionality"""
    
    def test_service_initialization(self, docling_service):
        """Test that service initializes correctly"""
        assert docling_service is not None
        # Service should check for Docling availability
        assert isinstance(docling_service.docling_available, bool)
    
    def test_is_table_heavy_section(self, docling_service):
        """Test table-heavy section detection"""
        assert docling_service.is_table_heavy_section("section_b") is True
        assert docling_service.is_table_heavy_section("cdrl") is True
        assert docling_service.is_table_heavy_section("section_m") is True
        assert docling_service.is_table_heavy_section("section_l") is False
        assert docling_service.is_table_heavy_section("section_h") is False
    
    @pytest.mark.asyncio
    async def test_parse_document_without_docling(self, docling_service):
        """Test parsing when Docling is not available"""
        if not docling_service.docling_available:
            result = await docling_service.parse_document("test.pdf")
            assert result.success is False
            assert result.error is not None
    
    def test_table_to_markdown(self, docling_service):
        """Test table to markdown conversion"""
        headers = ["CLIN", "Description", "Price"]
        rows = [
            ["0001", "Base Year", "$100,000"],
            ["0002", "Option 1", "$105,000"]
        ]
        
        markdown = docling_service._table_to_markdown(headers, rows, "Pricing Table")
        
        assert "**Pricing Table**" in markdown
        assert "| CLIN | Description | Price |" in markdown
        assert "| 0001 | Base Year | $100,000 |" in markdown
        assert "| 0002 | Option 1 | $105,000 |" in markdown
    
    def test_table_to_markdown_without_caption(self, docling_service):
        """Test table to markdown without caption"""
        headers = ["Col1", "Col2"]
        rows = [["A", "B"]]
        
        markdown = docling_service._table_to_markdown(headers, rows)
        
        assert "| Col1 | Col2 |" in markdown
        assert "| A | B |" in markdown
        assert "**" not in markdown  # No caption


class TestDoclingResult:
    """Test DoclingResult dataclass"""
    
    def test_successful_result(self):
        """Test successful parsing result"""
        result = DoclingResult(
            success=True,
            markdown="# Document Content",
            tables=[],
            metadata={"num_pages": 5}
        )
        
        assert result.success is True
        assert result.markdown == "# Document Content"
        assert len(result.tables) == 0
        assert result.metadata["num_pages"] == 5
        assert result.error is None
    
    def test_failed_result(self):
        """Test failed parsing result"""
        result = DoclingResult(
            success=False,
            error="File not found"
        )
        
        assert result.success is False
        assert result.error == "File not found"
        assert result.markdown is None
        assert len(result.tables) == 0
    
    def test_result_with_tables(self):
        """Test result with extracted tables"""
        table = TableData(
            caption="Test Table",
            headers=["A", "B"],
            rows=[["1", "2"]],
            markdown="| A | B |\n|---|---|\n| 1 | 2 |",
            page_number=1
        )
        
        result = DoclingResult(
            success=True,
            markdown="Content",
            tables=[table]
        )
        
        assert len(result.tables) == 1
        assert result.tables[0].caption == "Test Table"
        assert result.tables[0].page_number == 1


class TestTableData:
    """Test TableData dataclass"""
    
    def test_table_data_creation(self):
        """Test creating table data"""
        table = TableData(
            caption="CLIN Structure",
            headers=["CLIN", "Description", "Amount"],
            rows=[
                ["0001", "Base Year", "$100,000"],
                ["0002", "Option 1", "$105,000"]
            ],
            markdown="| CLIN | Description | Amount |",
            page_number=3
        )
        
        assert table.caption == "CLIN Structure"
        assert len(table.headers) == 3
        assert len(table.rows) == 2
        assert table.page_number == 3
    
    def test_table_data_without_page_number(self):
        """Test table data without page number"""
        table = TableData(
            caption=None,
            headers=["A"],
            rows=[["1"]],
            markdown="| A |"
        )
        
        assert table.caption is None
        assert table.page_number is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
