"""
Opportunities Router - Appwrite Version

API endpoints for opportunity management using Appwrite database.
Replaces SQLAlchemy-based opportunities.py for the Appwrite migration.
"""

from fastapi import APIRouter, HTTPException, Query
import pydantic
from typing import List, Optional
from datetime import datetime
import asyncio
import httpx
import logging
import math

from fedops_core.services.opportunities_repository import OpportunitiesRepository
from fedops_core.services.additional_repositories import (
    OpportunityCommentsRepository,
    OpportunityScoresRepository,
    OpportunityPipelinesRepository
)
from fedops_core.services.files_repository import FilesRepository
from fedops_core.settings import settings
from appwrite.query import Query as AppwriteQuery

router = APIRouter()
logger = logging.getLogger(__name__)

SAM_API_URL = "https://api.sam.gov/opportunities/v2/search"
SAM_DESCRIPTION_API_URL = "https://api.sam.gov/prod/opportunities/v1/noticedesc"


async def fetch_description(notice_id: str, api_key: str, client: Optional[httpx.AsyncClient] = None) -> str:
    """Fetch full description text from SAM.gov notice description endpoint"""
    try:
        params = {
            "api_key": api_key,
            "noticeid": notice_id
        }
        
        if client:
            response = await client.get(SAM_DESCRIPTION_API_URL, params=params)
        else:
            async with httpx.AsyncClient(timeout=15.0) as local_client:
                response = await local_client.get(SAM_DESCRIPTION_API_URL, params=params)
                
        if response.status_code == 200:
            data = response.json()
            return data.get("description", "")
        else:
            logger.warning(f"Failed to fetch description for notice {notice_id}: {response.status_code}")
            return ""
    except Exception as e:
        logger.error(f"Error fetching description for notice {notice_id}: {e}")
        return ""


def parse_date(date_str: str) -> Optional[str]:
    """Parse date string and return ISO format for Appwrite"""
    if not date_str:
        return None
    try:
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return dt.replace(tzinfo=None).isoformat()
    except:
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            return dt.isoformat()
        except:
            try:
                dt = datetime.strptime(date_str, "%m/%d/%Y")
                return dt.isoformat()
            except:
                return None


@router.get("/")
async def list_opportunities(
    skip: int = 0, 
    limit: int = 10,
    postedFrom: Optional[str] = Query(None, description="Date in MM/DD/YYYY format"),
    postedTo: Optional[str] = Query(None, description="Date in MM/DD/YYYY format"),
    ptype: Optional[str] = Query(None, description="Procurement type"),
    keywords: Optional[str] = Query(None, description="Keywords to search"),
    naics: Optional[str] = Query(None, description="NAICS Code"),
    setAside: Optional[str] = Query(None, description="Set Aside Code"),
    active: Optional[str] = Query(None, description="Active status (yes/no)")
):
    """List opportunities with filtering and pagination."""
    repo = OpportunitiesRepository()
    
    # Build query filters
    queries = []
    
    if keywords:
        queries.append(AppwriteQuery.search("title", keywords))
    
    if naics:
        naics_list = [n.strip() for n in naics.split(",") if n.strip()]
        if naics_list:
            queries.append(AppwriteQuery.equal("naics_code", naics_list))
    
    if setAside:
        set_aside_list = [s.strip() for s in setAside.split(",") if s.strip()]
        if set_aside_list:
            queries.append(AppwriteQuery.equal("type_of_set_aside", set_aside_list))
    
    if postedFrom:
        from_date = parse_date(postedFrom)
        if from_date:
            queries.append(AppwriteQuery.greater_than_equal("posted_date", from_date))
    
    if postedTo:
        to_date = parse_date(postedTo)
        if to_date:
            queries.append(AppwriteQuery.less_than_equal("posted_date", to_date))
    
    if active and active.lower() in ("yes", "no"):
        queries.append(AppwriteQuery.equal("active", active.capitalize()))
    
    # Add ordering
    queries.append(AppwriteQuery.order_desc("posted_date"))
    
    try:
        result = await repo.list(queries=queries, limit=limit, offset=skip)
        
        total = result.get("total", 0)
        documents = result.get("documents", [])
        
        total_pages = math.ceil(total / limit) if limit > 0 else 0
        current_page = (skip // limit) + 1 if limit > 0 else 1
        
        return {
            "items": documents,
            "total": total,
            "page": current_page,
            "limit": limit,
            "pages": total_pages
        }
    except Exception as e:
        logger.error(f"Error listing opportunities: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/unified")
async def unified_search(
    q: str = Query(..., min_length=3, description="Keyword to search"),
    limit: int = 20
):
    """
    Search for opportunities across SAM.gov and local database.
    """
    repo = OpportunitiesRepository()
    
    try:
        result = await repo.search(keyword=q, limit=limit)
        return {
            "query": q,
            "opportunities": result.get("documents", []),
            "total": result.get("total", 0)
        }
    except Exception as e:
        logger.error(f"Error in unified search: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{id}")
async def get_opportunity(id: str):
    """Get a single opportunity by ID."""
    repo = OpportunitiesRepository()
    
    opportunity = await repo.get(id)
    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    return opportunity


@router.get("/{id}/resources")
async def resolve_resources(id: str):
    """Resolve filenames for resource links."""
    repo = OpportunitiesRepository()
    
    opportunity = await repo.get(id)
    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    
    # If already resolved, return cached
    if opportunity.get("resource_files"):
        return opportunity["resource_files"]
    
    resource_links = opportunity.get("resource_links") or []
    if not resource_links:
        return []
    
    resolved_files = []
    
    async with httpx.AsyncClient(timeout=10.0, follow_redirects=False) as client:
        for link in resource_links:
            try:
                filename = link.split("/")[-1]
                response = await client.head(link)
                
                if response.status_code in (301, 302, 303, 307, 308):
                    location = response.headers.get("location")
                    if location:
                        import urllib.parse
                        import re
                        parsed = urllib.parse.urlparse(location)
                        params = urllib.parse.parse_qs(parsed.query)
                        content_disposition = params.get('response-content-disposition', [None])[0]
                        if content_disposition:
                            match = re.search(r'filename="?([^"]+)"?', content_disposition)
                            if match:
                                filename = match.group(1)
                
                if filename:
                    filename = filename.replace("+", " ")
                
                resolved_files.append({"url": link, "filename": filename})
            except Exception as e:
                logger.error(f"Error resolving link {link}: {e}")
                resolved_files.append({"url": link, "filename": link.split("/")[-1]})
    
    # Cache the resolved files
    await repo.update(id, {"resource_files": resolved_files})
    
    return resolved_files


@router.get("/{id}/comments")
async def get_opportunity_comments(id: str):
    """Get comments for an opportunity."""
    repo = OpportunityCommentsRepository()
    result = await repo.get_by_opportunity(id)
    return result.get("documents", [])


class CommentCreate(pydantic.BaseModel):
    text: str


@router.post("/{id}/comments")
async def create_opportunity_comment(id: str, comment: CommentCreate):
    """Create a new comment on an opportunity."""
    # Verify opportunity exists
    opp_repo = OpportunitiesRepository()
    opportunity = await opp_repo.get(id)
    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    
    repo = OpportunityCommentsRepository()
    new_comment = await repo.create({
        "opportunity_id": id,
        "text": comment.text
    })
    return new_comment


@router.delete("/{id}/comments/{comment_id}")
async def delete_opportunity_comment(id: str, comment_id: str):
    """Delete a comment."""
    repo = OpportunityCommentsRepository()
    
    comment = await repo.get(comment_id)
    if not comment or comment.get("opportunity_id") != id:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    await repo.delete(comment_id)
    return {"ok": True}


@router.delete("/{id}")
async def delete_opportunity(id: str):
    """
    Delete an opportunity and all related data.
    
    Cascades to:
    - Stored files
    - Opportunity scores
    - Proposals
    - Pipeline entries
    - Comments
    """
    opp_repo = OpportunitiesRepository()
    files_repo = FilesRepository()
    scores_repo = OpportunityScoresRepository()
    pipelines_repo = OpportunityPipelinesRepository()
    comments_repo = OpportunityCommentsRepository()
    
    opportunity = await opp_repo.get(id)
    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    
    deletion_summary = {
        "opportunity_id": id,
        "notice_id": opportunity.get("notice_id"),
        "title": opportunity.get("title"),
        "deleted_counts": {}
    }
    
    try:
        # Delete files
        files_result = await files_repo.get_by_opportunity(id)
        files = files_result.get("documents", [])
        for file in files:
            await files_repo.delete_with_storage(file["id"])
        deletion_summary["deleted_counts"]["files"] = len(files)
        
        # Delete score
        score = await scores_repo.get_by_opportunity(id)
        if score:
            await scores_repo.delete(score["id"])
            deletion_summary["deleted_counts"]["scores"] = 1
        else:
            deletion_summary["deleted_counts"]["scores"] = 0
        
        # Delete pipeline
        pipeline = await pipelines_repo.get_by_opportunity(id)
        if pipeline:
            await pipelines_repo.delete(pipeline["id"])
            deletion_summary["deleted_counts"]["pipeline_entries"] = 1
        else:
            deletion_summary["deleted_counts"]["pipeline_entries"] = 0
        
        # Delete comments
        comments_result = await comments_repo.get_by_opportunity(id)
        comments = comments_result.get("documents", [])
        for comment in comments:
            await comments_repo.delete(comment["id"])
        deletion_summary["deleted_counts"]["comments"] = len(comments)
        
        # Delete the opportunity
        await opp_repo.delete(id)
        
        logger.info(f"Deleted opportunity {id}")
        
        return {
            "message": "Opportunity deleted successfully",
            "summary": deletion_summary
        }
        
    except Exception as e:
        logger.error(f"Error deleting opportunity {id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete opportunity: {str(e)}")


class NaicsStatsRequest(pydantic.BaseModel):
    naics_codes: List[str]


@router.post("/stats/naics")
async def get_naics_stats(request: NaicsStatsRequest):
    """Get the count of active opportunities for each provided NAICS code."""
    if not request.naics_codes:
        return {}
    
    codes = [c.strip() for c in request.naics_codes if c.strip()]
    if not codes:
        return {}
    
    repo = OpportunitiesRepository()
    stats = {code: 0 for code in codes}
    
    for code in codes:
        try:
            result = await repo.list(
                queries=[
                    AppwriteQuery.equal("naics_code", code),
                    AppwriteQuery.equal("active", "Yes")
                ],
                limit=1
            )
            stats[code] = result.get("total", 0)
        except Exception as e:
            logger.warning(f"Error getting stats for NAICS {code}: {e}")
    
    return stats


# =============================================================================
# SAM.gov Sync Endpoints
# =============================================================================

@router.post("/sync/sam")
async def sync_from_sam(
    postedFrom: str = Query(..., description="Start date MM/DD/YYYY"),
    postedTo: str = Query(..., description="End date MM/DD/YYYY"),
    keywords: Optional[str] = Query(None),
    naics: Optional[str] = Query(None)
):
    """
    Sync opportunities from SAM.gov API to Appwrite database.
    
    This endpoint fetches opportunities from SAM.gov and stores them
    in the Appwrite database.
    """
    if not settings.SAM_API_KEY:
        raise HTTPException(status_code=400, detail="SAM_API_KEY not configured")
    
    repo = OpportunitiesRepository()
    
    params = {
        "api_key": settings.SAM_API_KEY,
        "limit": 1000,
        "offset": 0,
        "postedFrom": postedFrom,
        "postedTo": postedTo
    }
    
    if keywords:
        params["title"] = keywords
    if naics:
        params["ncode"] = [n.strip() for n in naics.split(",") if n.strip()]
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(SAM_API_URL, params=params)
            
            if resp.status_code != 200:
                raise HTTPException(
                    status_code=resp.status_code, 
                    detail=f"SAM.gov API error: {resp.text[:200]}"
                )
            
            data = resp.json()
            opportunities_data = data.get("opportunitiesData", [])
        
        created = 0
        updated = 0
        errors = 0
        
        for opp_data in opportunities_data:
            try:
                notice_id = opp_data.get("noticeId")
                if not notice_id:
                    continue
                
                # Check if exists
                existing = await repo.get_by_notice_id(notice_id)
                
                # Parse description
                raw_description = opp_data.get("description", "")
                description_text = raw_description
                
                if raw_description and ("http" in raw_description or "noticedesc" in raw_description):
                    description_text = await fetch_description(notice_id, settings.SAM_API_KEY)
                
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
                    "active": opp_data.get("active", "Yes"),
                    "description": description_text,
                    "organization_type": opp_data.get("organizationType"),
                    "additional_info_link": opp_data.get("additionalInfoLink"),
                    "ui_link": opp_data.get("uiLink"),
                    "source": "SAM.gov"
                }
                
                if existing:
                    await repo.update(existing["id"], opp_dict)
                    updated += 1
                else:
                    await repo.create(opp_dict)
                    created += 1
                    
            except Exception as e:
                logger.error(f"Error processing opportunity {opp_data.get('noticeId')}: {e}")
                errors += 1
        
        return {
            "message": "SAM.gov sync complete",
            "created": created,
            "updated": updated,
            "errors": errors,
            "total_fetched": len(opportunities_data)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error syncing from SAM.gov: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/auto-fetch-sam")
async def auto_fetch_from_sam(force_refresh: bool = Query(False, description="Force refresh ignoring cache")):
    """
    Auto-fetch opportunities from SAM.gov when database is empty.
    Uses company profile for search criteria if available, otherwise fetches all active opportunities.
    
    Implements 2-hour cache TTL to prevent excessive API calls.
    Set force_refresh=true to bypass cache.
    """
    from fedops_core.services.additional_repositories import CompanyProfilesRepository
    from fedops_core.services.cache_metadata import CacheMetadataRepository, DEFAULT_CACHE_TTL_SECONDS
    from fedops_sources.sam_opportunities.adapter import SAMOpportunitiesConnector
    from datetime import timedelta
    
    # Try to get company profile (optional)
    profile_repo = CompanyProfilesRepository()
    profiles_result = await profile_repo.list(limit=1)
    profile = profiles_result.get("documents", [None])[0] if profiles_result.get("documents") else None
    
    # Build SAM.gov search params
    today = datetime.now()
    thirty_days_ago = today - timedelta(days=30)
    
    if profile:
        # Use profile criteria for targeted search
        sam_params = {
            "naics": profile.get("target_naics", []),
            "setAside": profile.get("target_set_asides", []),
            "keywords": " ".join(profile.get("target_keywords", [])[:3]) if profile.get("target_keywords") else None,
            "limit": 50,
            "active": "yes",
            "postedFrom": thirty_days_ago.strftime("%m/%d/%Y"),
            "postedTo": today.strftime("%m/%d/%Y")
        }
        search_type = "profile-based"
        company_name = profile.get("company_name", "your company")
    else:
        # No profile - fetch all active opportunities (generic search)
        sam_params = {
            "limit": 100,  # Fetch more when no filtering
            "active": "yes",
            "postedFrom": thirty_days_ago.strftime("%m/%d/%Y"),
            "postedTo": today.strftime("%m/%d/%Y")
        }
        search_type = "generic"
        company_name = None
    
    # Remove None values
    sam_params = {k: v for k, v in sam_params.items() if v}
    
    # Check cache before fetching (unless force_refresh)
    cache_repo = CacheMetadataRepository()
    if not force_refresh:
        cache_valid = await cache_repo.is_cache_valid(sam_params, ttl_seconds=DEFAULT_CACHE_TTL_SECONDS)
        if cache_valid:
            # Cache is still valid, return cached info
            cache_entry = await cache_repo.get_cache_entry(sam_params)
            time_remaining = await cache_repo.get_time_until_expiry(sam_params, DEFAULT_CACHE_TTL_SECONDS)
            
            return {
                "status": "cache_hit",
                "message": "Using cached data from recent SAM.gov fetch",
                "opportunities_fetched": 0,
                "opportunities_skipped": cache_entry.get("record_count", 0) if cache_entry else 0,
                "errors": 0,
                "search_type": search_type,
                "cache_info": {
                    "last_fetch": cache_entry.get("last_fetch_time") if cache_entry else None,
                    "ttl_remaining_seconds": time_remaining,
                    "cached_record_count": cache_entry.get("record_count", 0) if cache_entry else 0
                },
                "search_criteria": {
                    "naics": profile.get("target_naics") if profile else "all",
                    "set_asides": profile.get("target_set_asides") if profile else "all",
                    "company": company_name,
                    "date_range": f"{thirty_days_ago.strftime('%m/%d/%Y')} - {today.strftime('%m/%d/%Y')}"
                }
            }
    
    try:
        # Initialize SAM.gov connector
        sam_connector = SAMOpportunitiesConnector()
        
        opportunities_added = 0
        opportunities_skipped = 0
        errors = 0
        repo = OpportunitiesRepository()
        
        async for opp_data in sam_connector.pull(sam_params):
            try:
                # Check if already exists by notice_id
                notice_id = opp_data.get("notice_id")
                if notice_id:
                    existing = await repo.get_by_notice_id(notice_id)
                    if existing:
                        opportunities_skipped += 1
                        continue
                
                # Create opportunity
                await repo.create(opp_data)
                opportunities_added += 1
                
            except Exception as e:
                logger.error(f"Error adding opportunity {opp_data.get('notice_id')}: {e}")
                errors += 1
        
        # Update cache metadata after successful fetch
        await cache_repo.update_cache_entry(
            fetch_params=sam_params,
            record_count=opportunities_added + opportunities_skipped,
            source="SAM.gov"
        )
        
        return {
            "status": "success",
            "opportunities_fetched": opportunities_added,
            "opportunities_skipped": opportunities_skipped,
            "errors": errors,
            "search_type": search_type,
            "search_criteria": {
                "naics": profile.get("target_naics") if profile else "all",
                "set_asides": profile.get("target_set_asides") if profile else "all",
                "company": company_name,
                "date_range": f"{thirty_days_ago.strftime('%m/%d/%Y')} - {today.strftime('%m/%d/%Y')}"
            }
        }
    
    except ValueError as e:
        # This will catch the "SAM_GOV_API_KEY is required" error
        logger.error(f"Configuration error: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"SAM.gov API configuration error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Failed to auto-fetch from SAM.gov: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"SAM.gov fetch failed: {str(e)}"
        )

"""
Cache Management Endpoints

These endpoints will be appended to opportunities_appwrite.py
"""

@router.get("/cache-status")
async def get_cache_status():
    """
    Get current cache status for SAM.gov data fetches.
    
    Returns information about the most recent cache entry and time until expiry.
    """
    from fedops_core.services.additional_repositories import CompanyProfilesRepository
    from fedops_core.services.cache_metadata import CacheMetadataRepository, DEFAULT_CACHE_TTL_SECONDS
    from datetime import timedelta
    
    # Try to get company profile to determine cache key
    profile_repo = CompanyProfilesRepository()
    profiles_result = await profile_repo.list(limit=1)
    profile = profiles_result.get("documents", [None])[0] if profiles_result.get("documents") else None
    
    # Build same params used in auto_fetch_from_sam
    today = datetime.now()
    thirty_days_ago = today - timedelta(days=30)
    
    if profile:
        sam_params = {
            "naics": profile.get("target_naics", []),
            "setAside": profile.get("target_set_asides", []),
            "keywords": " ".join(profile.get("target_keywords", [])[:3]) if profile.get("target_keywords") else None,
            "limit": 50,
            "active": "yes",
            "postedFrom": thirty_days_ago.strftime("%m/%d/%Y"),
            "postedTo": today.strftime("%m/%d/%Y")
        }
    else:
        sam_params = {
            "limit": 100,
            "active": "yes",
            "postedFrom": thirty_days_ago.strftime("%m/%d/%Y"),
            "postedTo": today.strftime("%m/%d/%Y")
        }
    
    sam_params = {k: v for k, v in sam_params.items() if v}
    
    cache_repo = CacheMetadataRepository()
    cache_entry = await cache_repo.get_cache_entry(sam_params)
    
    if not cache_entry:
        return {
            "cache_exists": False,
            "message": "No cache entry found for current search parameters"
        }
    
    is_valid = await cache_repo.is_cache_valid(sam_params, DEFAULT_CACHE_TTL_SECONDS)
    time_remaining = await cache_repo.get_time_until_expiry(sam_params, DEFAULT_CACHE_TTL_SECONDS)
    
    return {
        "cache_exists": True,
        "cache_valid": is_valid,
        "last_fetch_time": cache_entry.get("last_fetch_time"),
        "record_count": cache_entry.get("record_count"),
        "ttl_seconds": DEFAULT_CACHE_TTL_SECONDS,
        "ttl_remaining_seconds": time_remaining,
        "fetch_params": cache_entry.get("fetch_params"),
        "source": cache_entry.get("source")
    }


@router.post("/refresh-cache")
async def refresh_cache():
    """
    Manually refresh SAM.gov data, bypassing cache.
    
    This will force a new fetch from SAM.gov regardless of cache TTL.
    """
    # Simply call auto_fetch_from_sam with force_refresh=True
    result = await auto_fetch_from_sam(force_refresh=True)
    return {
        **result,
        "message": "Cache manually refreshed from SAM.gov"
    }


@router.post("/invalidate-cache")
async def invalidate_cache():
    """
    Invalidate all cache entries.
    
    This will clear all cached SAM.gov fetch metadata, forcing fresh fetches on next request.
    """
    from fedops_core.services.cache_metadata import CacheMetadataRepository
    
    cache_repo = CacheMetadataRepository()
    deleted_count = await cache_repo.invalidate_all_caches()
    
    return {
        "status": "success",
        "message": f"Invalidated {deleted_count} cache entries",
        "deleted_count": deleted_count
    }
