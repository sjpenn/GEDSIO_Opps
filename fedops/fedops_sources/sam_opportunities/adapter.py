import httpx
import os
from typing import AsyncIterator, Dict, Any, Optional
from datetime import datetime

class SAMOpportunitiesConnector:
    """
    SAM.gov Opportunities API v2 Connector
    Documentation: https://open.gsa.gov/api/get-opportunities-public-api/
    """
    name = "sam_opportunities"
    BASE_URL = "https://api.sam.gov/opportunities/v2/search"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("SAM_GOV_API_KEY")
        if not self.api_key:
            raise ValueError("SAM_GOV_API_KEY is required. Set it in environment variables.")
    
    async def pull(
        self, 
        params: Dict[str, Any]
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Fetch opportunities from SAM.gov API.
        
        Params:
            naics: Comma-separated NAICS codes or list
            keywords: Search keywords
            setAside: Comma-separated set-aside types or list
            limit: Max results (default: 10, max: 1000)
            offset: Pagination offset
            active: "yes", "no", or "all"
            postedFrom: Date in MM/DD/YYYY format
            postedTo: Date in MM/DD/YYYY format
        """
        headers = {
            "X-Api-Key": self.api_key,
            "Accept": "application/json"
        }
        
        # Build query params for SAM.gov API
        query_params = {
            "limit": min(params.get("limit", 10), 1000),  # SAM.gov max is 1000
            "offset": params.get("offset", 0),
            "api_key": self.api_key
        }
        
        # NAICS codes
        if params.get("naics"):
            naics = params["naics"]
            if isinstance(naics, list):
                naics = ",".join(naics)
            query_params["ncode"] = naics
        
        # Keywords
        if params.get("keywords"):
            query_params["q"] = params["keywords"]
            
        # Set-aside types
        if params.get("setAside"):
            set_aside = params["setAside"]
            if isinstance(set_aside, list):
                set_aside = ",".join(set_aside)
            query_params["typeOfSetAsideCode"] = set_aside
        
        # Active status
        if params.get("active") == "yes":
            query_params["active"] = "true"
        elif params.get("active") == "no":
            query_params["active"] = "false"
        
        # Date range
        if params.get("postedFrom"):
            query_params["postedFrom"] = params["postedFrom"]
        if params.get("postedTo"):
            query_params["postedTo"] = params["postedTo"]
        
        # Type filter
        if params.get("ptype"):
            query_params["ptype"] = params["ptype"]
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    self.BASE_URL,
                    headers=headers,
                    params=query_params
                )
                response.raise_for_status()
                data = response.json()
                
                # SAM.gov returns: { "opportunitiesData": [...], "totalRecords": N }
                opportunities = data.get("opportunitiesData", [])
                
                for opp in opportunities:
                    yield self._transform_opportunity(opp)
                    
        except httpx.HTTPStatusError as e:
            raise Exception(f"SAM.gov API error: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            raise Exception(f"SAM.gov API request failed: {str(e)}")
    
    def _transform_opportunity(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform SAM.gov API response to Appwrite opportunities schema.
        
        Only includes fields that exist in the Appwrite collection.
        Complex objects are stored in full_response field.
        """
        # Extract department from fullParentPathName
        full_path = raw.get("fullParentPathName", "")
        dept_parts = full_path.split(".") if full_path else []
        
        return {
            # Core identification
            "notice_id": raw.get("noticeId"),
            "solicitation_number": raw.get("solicitationNumber"),
            "title": raw.get("title"),
            
            # Agency information (simplified)
            "department": dept_parts[0] if len(dept_parts) > 0 else raw.get("organizationHierarchy", {}).get("departmentName"),
            "sub_tier": raw.get("subtierName") or (dept_parts[1] if len(dept_parts) > 1 else None),
            "office": raw.get("officeAddress", {}).get("city") if raw.get("officeAddress") else None,
            
            # Dates
            "posted_date": self._parse_date(raw.get("postedDate")),
            "response_deadline": self._parse_date(raw.get("responseDeadLine")),
            
            # Classification
            "type": raw.get("type"),
            "base_type": raw.get("baseType"),
            "naics_code": raw.get("naicsCode"),
            "classification_code": raw.get("classificationCode"),
            
            # Status
            "active": "Yes" if raw.get("active", True) else "No",
            
            # Content
            "description": raw.get("description"),
            
            # Set-aside information
            "type_of_set_aside": raw.get("typeOfSetAside"),
            "type_of_set_aside_description": raw.get("typeOfSetAsideDescription"),
            
            # UI link
            "ui_link": raw.get("uiLink"),
            
            # Archive info
            "archive_type": raw.get("archiveType"),
            "archive_date": self._parse_date(raw.get("archiveDate")),
            
            # Source marker
            "source": "SAM.gov"
        }
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[str]:
        """Parse SAM.gov date format to ISO 8601."""
        if not date_str:
            return None
        try:
            # SAM.gov uses ISO 8601 format already
            return date_str
        except:
            return None
