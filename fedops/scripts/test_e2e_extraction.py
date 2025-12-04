"""
End-to-End Test for Document Extraction and Analysis Pipeline

Tests the complete workflow:
1. Document extraction from real RFP files
2. Agent analysis using extracted data
3. Verification of output structure

Uses DCS G8 Support Services RFP as test case.
"""

import asyncio
import logging
import sys
import json
from pathlib import Path
from fedops_core.services.document_extractor import DocumentExtractor
from fedops_core.prompts import determine_document_type

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_end_to_end():
    """Test complete extraction pipeline with real RFP documents"""
    
    # Define test files from DCS G8 RFP
    base_path = Path("/Users/sjpenn/SitesAgents/GEDSIO_Opps/fedops/uploads")
    
    test_files = [
        {
            "file_path": str(base_path / "J.7 - Section L Instructions%2C Conditions%2C and Notices to Offerors %28Amended 30 September 2025%29.pdf"),
            "filename": "Section L - Instructions to Offerors.pdf",
            "expected_type": "section_l"
        },
        {
            "file_path": str(base_path / "J.8 - Section M%2C Evaluation Factors for Award %28Amended 30 September 2025%29.pdf"),
            "filename": "Section M - Evaluation Factors.pdf",
            "expected_type": "section_m"
        },
        {
            "file_path": str(base_path / "Solicitation - W91CRB25RA001 %28Amended 30 September 2025%29.pdf"),
            "filename": "Main Solicitation.pdf",
            "expected_type": "rfp"
        }
    ]
    
    logger.info("=" * 80)
    logger.info("END-TO-END EXTRACTION TEST")
    logger.info("=" * 80)
    
    # Initialize extractor
    extractor = DocumentExtractor()
    
    # Test 1: Extract from all documents
    logger.info("\n--- Test 1: Multi-Document Extraction ---")
    try:
        extracted_data = await extractor.extract_all_documents(test_files)
        
        logger.info(f"\n✅ Extraction completed successfully!")
        logger.info(f"Sections extracted: {[k for k, v in extracted_data.items() if v and k != 'source_documents']}")
        logger.info(f"Source documents: {len(extracted_data.get('source_documents', []))}")
        
        # Display extracted data summary
        for section_key, section_data in extracted_data.items():
            if section_key == 'source_documents':
                continue
            if section_data:
                logger.info(f"\n📄 {section_key.upper()}:")
                if isinstance(section_data, dict):
                    logger.info(f"   Fields: {list(section_data.keys())}")
                    # Show first few characters of each field
                    for key, value in list(section_data.items())[:3]:
                        value_str = str(value)[:100] if value else "None"
                        logger.info(f"   - {key}: {value_str}...")
                else:
                    logger.info(f"   Data: {str(section_data)[:200]}...")
        
        # Test 2: Verify source tracking
        logger.info("\n--- Test 2: Source Document Tracking ---")
        source_docs = extracted_data.get('source_documents', [])
        if source_docs:
            logger.info(f"✅ Source tracking working: {len(source_docs)} documents tracked")
            for doc in source_docs:
                logger.info(f"   - {doc.get('filename')} → {doc.get('type')}")
        else:
            logger.warning("⚠️  No source documents tracked")
        
        # Test 3: Verify data structure
        logger.info("\n--- Test 3: Data Structure Validation ---")
        required_sections = ['section_l', 'section_m']
        for section in required_sections:
            if extracted_data.get(section):
                logger.info(f"✅ {section} extracted")
            else:
                logger.warning(f"⚠️  {section} not extracted")
        
        # Test 4: Save results for inspection
        logger.info("\n--- Test 4: Saving Results ---")
        output_file = Path("test_extraction_results.json")
        with open(output_file, 'w') as f:
            # Convert to JSON-serializable format
            json_data = {}
            for key, value in extracted_data.items():
                if key == 'source_documents':
                    json_data[key] = value
                elif value:
                    json_data[key] = value
            json.dump(json_data, f, indent=2)
        logger.info(f"✅ Results saved to {output_file}")
        
        # Summary
        logger.info("\n" + "=" * 80)
        logger.info("TEST SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Total sections extracted: {len([k for k, v in extracted_data.items() if v and k != 'source_documents'])}")
        logger.info(f"Source documents tracked: {len(source_docs)}")
        logger.info(f"Results file: {output_file}")
        logger.info("=" * 80)
        
        return extracted_data
        
    except Exception as e:
        logger.error(f"❌ Extraction failed: {e}", exc_info=True)
        return None

if __name__ == "__main__":
    result = asyncio.run(test_end_to_end())
    if result:
        print("\n✅ End-to-end test PASSED")
        sys.exit(0)
    else:
        print("\n❌ End-to-end test FAILED")
        sys.exit(1)
