from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from typing import List, Optional
from datetime import datetime
import asyncio
import httpx
import logging
import math

from fedops_api.deps import get_db
from fedops_core.db.models import Opportunity as OpportunityModel, OpportunityComment as OpportunityCommentModel
from fedops_core.schemas.opportunity import Opportunity as OpportunitySchema, OpportunityComment as OpportunityCommentSchema, OpportunityCommentCreate
from fedops_core.schemas.pagination import PaginatedResponse
from fedops_core.settings import settings
from fedops_api.services.unified_search import UnifiedSearchService

router = APIRouter()
logger = logging.getLogger(__name__)

SAM_API_URL = "https://api.sam.gov/opportunities/v2/search"
SAM_DESCRIPTION_API_URL = "https://api.sam.gov/prod/opportunities/v1/noticedesc"

async def fetch_description(notice_id: str, api_key: str) -> str:
    """Fetch full description text from SAM.gov notice description endpoint"""
    try:
        params = {
            "api_key": api_key,
            "noticeid": notice_id
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(SAM_DESCRIPTION_API_URL, params=params)
            if response.status_code == 200:
                data = response.json()
                # The description endpoint returns an object with 'description' field
                return data.get("description", "")
            else:
                logger.warning(f"Failed to fetch description for notice {notice_id}: {response.status_code}")
                return ""
    except Exception as e:
        logger.error(f"Error fetching description for notice {notice_id}: {e}")
        return ""

def parse_date(date_str: str) -> datetime | None:
    """Parse date string in ISO format or YYYY-MM-DD format"""
    if not date_str:
        return None
    try:
        # Try ISO format first (e.g., "2024-11-01T11:00:00-04:00")
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        # Remove timezone info to make it offset-naive for PostgreSQL
        return dt.replace(tzinfo=None)
    except:
        try:
            # Fallback to simple date format
            return datetime.strptime(date_str, "%Y-%m-%d")
        except:
            return None

@router.get("/", response_model=PaginatedResponse[OpportunitySchema])
async def list_opportunities(
    skip: int = 0, 
    limit: int = 10,
    postedFrom: Optional[str] = Query(None, description="Date in MM/DD/YYYY format"),
    postedTo: Optional[str] = Query(None, description="Date in MM/DD/YYYY format"),
    ptype: Optional[str] = Query(None, description="Procurement type"),
    keywords: Optional[str] = Query(None, description="Keywords to search"),
    naics: Optional[str] = Query(None, description="NAICS Code"),
    setAside: Optional[str] = Query(None, description="Set Aside Code"),
    active: Optional[str] = Query(None, description="Active status (yes/no)"),
    db: AsyncSession = Depends(get_db)
):
    logger.error(f"DEBUG: list_opportunities called with skip={skip}, limit={limit}, active={active}, keywords={keywords}")
    logger.info(f"list_opportunities called with skip={skip}, limit={limit}")
    
    # Only fetch from SAM.gov if keywords are provided (explicit search)
    # Don't fetch on every page load - use local DB for browsing
    should_fetch_sam = (keywords is not None and keywords.strip() != "")
    
    if should_fetch_sam and settings.SAM_API_KEY:
        try:
            # Date Cycling Strategy: Fetch by year to ensure API coverage
            # We will fetch from current year back 12 years
            current_year = datetime.now().year
            start_year = current_year - 12
            years = range(current_year, start_year - 1, -1)
            
            async def fetch_year(year: int, base_params: dict):
                year_params = base_params.copy()
                year_params["postedFrom"] = f"01/01/{year}"
                year_params["postedTo"] = f"12/31/{year}"
                # Remove active param from API call to get everything
                if "active" in year_params:
                    del year_params["active"]
                    
                try:
                    async with httpx.AsyncClient(timeout=30.0) as client:
                        logger.info(f"Fetching year {year} with params: {year_params}")
                        resp = await client.get(SAM_API_URL, params=year_params)
                        if resp.status_code == 200:
                            data = resp.json()
                            return data.get("opportunitiesData", [])
                        else:
                            logger.warning(f"Failed to fetch year {year}: {resp.status_code}")
                            return []
                except Exception as e:
                    logger.error(f"Error fetching year {year}: {e}")
                    return []

            # Prepare base params
            base_params = {
                "api_key": settings.SAM_API_KEY,
                "limit": 1000, # Fetch more per year to ensure we find it
                "offset": 0
            }
            if ptype:
                base_params["ptype"] = ptype
            if keywords:
                base_params["title"] = keywords
            if naics:
                # Split comma-separated string into list for API
                base_params["ncode"] = [n.strip() for n in naics.split(",") if n.strip()]
            if setAside:
                base_params["setAside"] = [s.strip() for s in setAside.split(",") if s.strip()]

            # Execute parallel requests
            # Limit concurrency to avoid rate limits (e.g., 5 at a time)
            all_opportunities_data = []
            chunk_size = 5
            for i in range(0, len(years), chunk_size):
                chunk_years = years[i:i + chunk_size]
                tasks = [fetch_year(year, base_params) for year in chunk_years]
                results = await asyncio.gather(*tasks)
                for res in results:
                    all_opportunities_data.extend(res)
            
            logger.info(f"Total raw opportunities found from all years: {len(all_opportunities_data)}")

            # Deduplicate by noticeId
            unique_opps = {}
            for opp in all_opportunities_data:
                # Use noticeId as key
                nid = opp.get("noticeId")
                if nid and nid not in unique_opps:
                    unique_opps[nid] = opp
            
            opportunities_data = list(unique_opps.values())
            
            # Apply local filtering for active status if needed (API might not handle it perfectly across years)
            if active == "yes":
                opportunities_data = [o for o in opportunities_data if o.get("active", "Yes") == "Yes"]
            elif active == "no":
                opportunities_data = [o for o in opportunities_data if o.get("active", "Yes") == "No"]
            # If active is None, empty string, or "all", keep all
            
            logger.info(f"Final filtered opportunities: {len(opportunities_data)}")

            for opp_data in opportunities_data:
                # Map SAM.gov data to our model
                notice_id = opp_data.get("noticeId")
                
                # Check if description is a URL or text
                raw_description = opp_data.get("description", "")
                description_text = raw_description
                
                # If it looks like a URL to the description endpoint, fetch the actual text
                if raw_description and (raw_description.startswith("http") and "noticedesc" in raw_description):
                    if notice_id:
                        fetched_desc = await fetch_description(notice_id, settings.SAM_API_KEY)
                        if fetched_desc:
                            description_text = fetched_desc
                
                # Check if exists
                stmt = select(OpportunityModel).where(OpportunityModel.notice_id == notice_id)
                result = await db.execute(stmt)
                existing_opp = result.scalar_one_or_none()
                
                # logger.info(f"Processing notice {notice_id}. NAICS: {opp_data.get('naicsCode')}")

                opp_dict = {
                    "notice_id": notice_id,
                    "title": opp_data.get("title"),
                    "solicitation_number": opp_data.get("solicitationNumber"),
                    "department": opp_data.get("department"),
                    "sub_tier": opp_data.get("subTier"),
                    "office": opp_data.get("office"),
                    "posted_date": parse_date(opp_data.get("postedDate")),
                    "type": opp_data.get("type"),
                    "base_type": opp_data.get("baseType"),
                    "archive_type": opp_data.get("archiveType"),
                    "archive_date": parse_date(opp_data.get("archiveDate")),
                    "type_of_set_aside_description": opp_data.get("typeOfSetAsideDescription"),
                    "type_of_set_aside": opp_data.get("typeOfSetAside"),
                    "response_deadline": parse_date(opp_data.get("responseDeadLine")),
                    "naics_code": opp_data.get("naicsCode"),
                    "classification_code": opp_data.get("classificationCode"),

                    "active": opp_data.get("active"),
                    "award": opp_data.get("award"),
                    "point_of_contact": opp_data.get("pointOfContact"),
                    "description": description_text,
                    "organization_type": opp_data.get("organizationType"),
                    "office_address": opp_data.get("officeAddress"),
                    "place_of_performance": opp_data.get("placeOfPerformance"),
                    "additional_info_link": opp_data.get("additionalInfoLink"),
                    "ui_link": opp_data.get("uiLink"),
                    "links": opp_data.get("links"),
                    "resource_links": opp_data.get("resourceLinks"),
                    "full_response": opp_data
                }
                
                if existing_opp:
                    for key, value in opp_dict.items():
                        setattr(existing_opp, key, value)
                else:
                    new_opp = OpportunityModel(**opp_dict)
                    db.add(new_opp)
            
            await db.commit()
            
        except Exception as e:
            logger.error(f"Error fetching from SAM.gov: {e}")
            import traceback
            logger.error(traceback.format_exc())
            # Fallback to local DB if API fails or just log error
            pass

    # Return from local DB (which is now updated)
    try:
        logger.info("Querying local DB for opportunities")
        # Build query with filters
        query = select(OpportunityModel)
        
        if naics:
            naics_list = [n.strip() for n in naics.split(",") if n.strip()]
            if naics_list:
                conditions = [OpportunityModel.naics_code.ilike(f"%{n}%") for n in naics_list]
                query = query.where(or_(*conditions))
        
        if setAside:
            set_aside_list = [s.strip() for s in setAside.split(",") if s.strip()]
            if set_aside_list:
                conditions = [OpportunityModel.type_of_set_aside.ilike(f"%{s}%") for s in set_aside_list]
                query = query.where(or_(*conditions))
            
        if keywords:
            search_term = f"%{keywords}%"
            query = query.where(
                or_(
                    OpportunityModel.title.ilike(search_term),
                    OpportunityModel.description.ilike(search_term),
                    OpportunityModel.naics_code.ilike(search_term),
                    OpportunityModel.type_of_set_aside.ilike(search_term),
                    OpportunityModel.solicitation_number.ilike(search_term)
                )
            )

        # Calculate total count for pagination
        count_stmt = select(func.count()).select_from(query.subquery())
        logger.info("Executing count query")
        count_result = await db.execute(count_stmt)
        total = count_result.scalar_one()
        logger.info(f"Count result: {total}")

        # Calculate total pages
        total_pages = math.ceil(total / limit) if limit > 0 else 0
        current_page = (skip // limit) + 1 if limit > 0 else 1

        # Apply sorting and pagination
        query = query.order_by(OpportunityModel.posted_date.desc()).offset(skip).limit(limit)
        logger.info("Executing main query")
        result = await db.execute(query)
        opportunities = result.scalars().all()
        logger.info(f"Main query returned {len(opportunities)} items")
        
        return PaginatedResponse(
            items=opportunities,
            total=total,
            page=current_page,
            limit=limit,
            pages=total_pages
        )
    except Exception as e:
        logger.error(f"Error querying local DB: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search/unified")
async def unified_search(
    q: str = Query(..., min_length=3, description="Keyword to search"),
    limit: int = 20
):
    """
    Search for opportunities across SAM.gov (active/archived) and USASpending.gov (awards).
    """
    service = UnifiedSearchService()
    return await service.search(q, limit)

@router.get("/{id}", response_model=OpportunitySchema)
async def get_opportunity(id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(OpportunityModel).where(OpportunityModel.id == id))
    opportunity = result.scalar_one_or_none()
    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    return opportunity

@router.get("/{id}/resources")
async def resolve_resources(id: int, db: AsyncSession = Depends(get_db)):
    """
    Resolve filenames for resource links by making HEAD requests.
    Cache the results in the database.
    """
    result = await db.execute(select(OpportunityModel).where(OpportunityModel.id == id))
    opportunity = result.scalar_one_or_none()
    
    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")
        
    # If we already have resolved files, return them
    if opportunity.resource_files:
        return opportunity.resource_files
        
    # If no resource links, return empty list
    if not opportunity.resource_links:
        return []
        
    resolved_files = []
    
    async with httpx.AsyncClient(timeout=10.0, follow_redirects=False) as client:
        for link in opportunity.resource_links:
            try:
                # Default filename from URL
                filename = link.split("/")[-1]
                
                # Try to get real filename from headers (without following redirect to S3)
                response = await client.head(link)
                
                # Check for redirect with filename in query params (common for SAM.gov)
                if response.status_code in (301, 302, 303, 307, 308):
                    location = response.headers.get("location")
                    if location:
                        import urllib.parse
                        parsed = urllib.parse.urlparse(location)
                        params = urllib.parse.parse_qs(parsed.query)
                        content_disposition = params.get('response-content-disposition', [None])[0]
                        if content_disposition:
                            import re
                            # Look for filename="name"
                            match = re.search(r'filename="?([^"]+)"?', content_disposition)
                            if match:
                                filename = match.group(1)
                            else:
                                # Try filename*=
                                match = re.search(r"filename\*=UTF-8''(.+)", content_disposition)
                                if match:
                                    filename = urllib.parse.unquote(match.group(1))

                # If not a redirect or no filename in redirect, check Content-Disposition header directly
                elif response.status_code == 200:
                    content_disposition = response.headers.get("content-disposition")
                    if content_disposition:
                        import re
                        match = re.search(r'filename="?([^"]+)"?', content_disposition)
                        if match:
                            filename = match.group(1)
                        else:
                            match = re.search(r"filename\*=UTF-8''(.+)", content_disposition)
                            if match:
                                import urllib.parse
                                filename = urllib.parse.unquote(match.group(1))
                                
                # Clean up filename (replace + with space)
                if filename:
                    filename = filename.replace("+", " ")

                resolved_files.append({
                    "url": link,
                    "filename": filename
                })
            except Exception as e:
                logger.error(f"Error resolving link {link}: {e}")
                # Fallback to URL filename
                resolved_files.append({
                    "url": link,
                    "filename": link.split("/")[-1]
                })
    
    # Save to DB
    opportunity.resource_files = resolved_files
    await db.commit()
    
    return resolved_files

@router.get("/{id}/comments", response_model=List[OpportunityCommentSchema])
async def get_opportunity_comments(id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(OpportunityCommentModel).where(OpportunityCommentModel.opportunity_id == id).order_by(OpportunityCommentModel.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("/{id}/comments", response_model=OpportunityCommentSchema)
async def create_opportunity_comment(id: int, comment: OpportunityCommentCreate, db: AsyncSession = Depends(get_db)):
    # Verify opportunity exists
    result = await db.execute(select(OpportunityModel).where(OpportunityModel.id == id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Opportunity not found")
    
    db_comment = OpportunityCommentModel(opportunity_id=id, text=comment.text)
    db.add(db_comment)
    await db.commit()
    await db.refresh(db_comment)
    return db_comment

@router.delete("/{id}/comments/{comment_id}")
async def delete_opportunity_comment(id: int, comment_id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(OpportunityCommentModel).where(
        OpportunityCommentModel.id == comment_id,
        OpportunityCommentModel.opportunity_id == id
    )
    result = await db.execute(stmt)
    comment = result.scalar_one_or_none()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    await db.delete(comment)
    await db.commit()
    return {"ok": True}
