import asyncio
import logging
import sys
from fedops_core.services.document_extractor import DocumentExtractor
from fedops_core.prompts import DocumentType

# Configure logging
logging.basicConfig(level=logging.INFO)

async def test_extraction():
    extractor = DocumentExtractor()
    
    # Sample Section L content
    section_l_content = """
    SECTION L - INSTRUCTIONS, CONDITIONS, AND NOTICES TO OFFERORS
    
    L.1 PROPOSAL SUBMISSION
    Proposals shall be submitted via email to contracting@agency.gov by 2:00 PM EST on January 15, 2024.
    Late submissions will not be accepted.
    
    L.2 PROPOSAL VOLUMES
    The proposal shall be submitted in separate volumes as follows:
    
    Volume I - Technical Proposal (Page Limit: 25 pages)
    Volume II - Past Performance (Page Limit: 10 pages)
    Volume III - Price Proposal (No page limit)
    
    L.3 FORMATTING
    Text shall be single-spaced, Times New Roman, 12-point font.
    Margins shall be 1 inch on all sides.
    Files shall be in PDF format, except Price Proposal which shall be Excel.
    """
    
    print("\n--- Testing Section L Extraction ---")
    try:
        result = await extractor.extract_section_l(section_l_content)
        print("Result:", result)
    except Exception as e:
        print("Error:", e)

    # Sample Section M content
    section_m_content = """
    SECTION M - EVALUATION FACTORS FOR AWARD
    
    M.1 BASIS FOR AWARD
    Award will be made to the responsible offeror whose proposal represents the Best Value to the Government,
    trade-offs considered. Technical and Past Performance, when combined, are significantly more important than Price.
    
    M.2 EVALUATION FACTORS
    Factor 1: Technical Approach
    Factor 2: Past Performance
    Factor 3: Price
    
    M.3 FACTOR 1 - TECHNICAL APPROACH
    The Government will evaluate the offeror's understanding of the SOW...
    """
    
    print("\n--- Testing Section M Extraction ---")
    try:
        result = await extractor.extract_section_m(section_m_content)
        print("Result:", result)
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    asyncio.run(test_extraction())
