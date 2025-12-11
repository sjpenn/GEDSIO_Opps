import asyncio
import json
import os
import sys
import logging
from typing import List
from datetime import datetime

# Add project root to path
sys.path.append(os.getcwd())

from fedops_core.services.perplexity_service import perplexity_service

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

AGENCIES = [
    "Department of Defense (DOD)",
    "General Services Administration (GSA)",
    "Department of Health and Human Services (HHS)",
    "Department of Veterans Affairs (VA)",
    "Department of Homeland Security (DHS)",
    "National Aeronautics and Space Administration (NASA)",
    "Department of Energy (DOE)",
    "Department of Transportation (DOT)",
    "Department of Justice (DOJ)",
    "Department of State (DOS)",
    "Department of Agriculture (USDA)",
    "Department of Education (ED)",
    "Department of the Interior (DOI)",
    "Department of Labor (DOL)",
    "Department of the Treasury",
    # Add more as needed
]

OUTPUT_DIR = "data/exports"
OUTPUT_FILE = f"agency_contacts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

async def fetch_contacts_for_agency(agency: str) -> List[dict]:
    """Fetch contracting contacts for a specific agency"""
    logger.info(f"Searching for contacts at: {agency}")
    try:
        # Search for "Contracting Officers at [Agency]"
        query = f"Contracting Officers at {agency}"
        result = await perplexity_service.research_contracting_professionals(query)
        
        matches = []
        if result and result.matches:
            # Add agency context if missing from result
            for match in result.matches:
                match_dict = match.model_dump()
                if not match_dict.get('agency') or match_dict.get('agency') == "Unknown":
                    match_dict['agency'] = agency
                matches.append(match_dict)
            
            logger.info(f"Found {len(matches)} contacts for {agency}")
        else:
            logger.warning(f"No contacts found for {agency}")
            
        return matches
        
    except Exception as e:
        logger.error(f"Error fetching contacts for {agency}: {e}")
        return []

async def main():
    logger.info("Starting batch agency contact fetch...")
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    all_contacts = []
    
    for agency in AGENCIES:
        contacts = await fetch_contacts_for_agency(agency)
        all_contacts.extend(contacts)
        
        # Rate limiting / Be nice to API
        await asyncio.sleep(2) 
        
    output_path = os.path.join(OUTPUT_DIR, OUTPUT_FILE)
    
    with open(output_path, 'w') as f:
        json.dump(all_contacts, f, indent=2)
        
    logger.info(f"Completed! Saved {len(all_contacts)} contacts to {output_path}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Fetch agency contacts")
    parser.add_argument("--limit", type=int, help="Limit number of agencies to process (for testing)")
    parser.add_argument("--agency", type=str, help="Specific agency to search (optional)")
    args = parser.parse_args()
    
    # Filter agencies if arguments provided
    if args.agency:
        AGENCIES = [args.agency]
    elif args.limit:
        AGENCIES = AGENCIES[:args.limit]
        
    asyncio.run(main())
