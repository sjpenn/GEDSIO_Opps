import httpx
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime
from fedops_core.settings import settings
from fedops_sources.fuzzy_search import (
    generate_sam_search_queries,
    deduplicate_entities,
    filter_by_similarity,
    generate_cache_key,
    get_cached_results,
    cache_results,
    get_cache_stats
)

class SamEntityClient:
    BASE_URL = "https://api.sam.gov/entity-information/v3/entities"

    def __init__(self):
        self.api_key = settings.SAM_API_KEY

    async def get_entity(self, uei: str) -> Optional[Dict[str, Any]]:
        if not self.api_key:
            print("Warning: SAM_API_KEY not set")
            return None

        params = {
            "api_key": self.api_key,
            "ueiSAM": uei,
            "includeSections": "entityRegistration,coreData,assertions,repsAndCerts,pointsOfContact"
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(self.BASE_URL, params=params)
                response.raise_for_status()
                data = response.json()
                # SAM API structure is a bit deep, usually data['entityData'] or similar
                # We might need to adjust based on actual response
                if data and isinstance(data, list) and len(data) > 0:
                     return data[0] # Assuming list of matches
                return data
            except httpx.HTTPStatusError as e:
                print(f"Error fetching entity {uei}: {e}")
                return None
            except Exception as e:
                print(f"Unexpected error fetching entity {uei}: {e}")
                return None

    async def search_entities(
        self, 
        legal_business_name: str, 
        fuzzy: bool = True,
        min_similarity: float = 0.5,
        use_phonetic: bool = True,
        use_abbreviations: bool = True,
        use_typos: bool = True,
        bypass_cache: bool = False
    ) -> Dict[str, Any]:
        """
        Search for entities with fuzzy matching applied LOCALLY to avoid API rate limits.
        
        Strategy:
        1. Make ONE exact API call to SAM.gov
        2. Store results in local database
        3. Apply fuzzy matching to ALL locally stored entities
        
        Args:
            legal_business_name: Business name to search for
            fuzzy: Enable fuzzy matching on local entities
            min_similarity: Minimum similarity score for fuzzy matches (0.0-1.0)
            use_phonetic: Enable phonetic matching for sound-alike names
            use_abbreviations: Enable abbreviation expansion/contraction
            use_typos: Enable typo tolerance
            bypass_cache: Skip cache and fetch fresh results
            
        Returns:
            Dictionary with entityData list and search metadata
        """
        if not self.api_key:
            print("Warning: SAM_API_KEY not set")
            return {}
        
        # Generate cache key
        cache_key = generate_cache_key(
            legal_business_name,
            fuzzy=fuzzy,
            min_similarity=min_similarity,
            use_phonetic=use_phonetic,
            use_abbreviations=use_abbreviations,
            use_typos=use_typos
        )
        
        # Check cache first (unless bypassed)
        if not bypass_cache:
            cached_result = get_cached_results(cache_key)
            if cached_result:
                print(f"Cache hit for query '{legal_business_name}'")
                cached_result["searchMetadata"]["cached"] = True
                cached_result["searchMetadata"]["cacheStats"] = get_cache_stats()
                return cached_result
        
        # Make ONE exact API call to SAM.gov
        params = {
            "api_key": self.api_key,
            "q": f"(legalBusinessName:*{legal_business_name}*)",
            "includeSections": "entityRegistration"
        }
        
        api_entities = []
        async with httpx.AsyncClient() as client:
            try:
                print(f"Making single API call for: {legal_business_name}")
                response = await client.get(self.BASE_URL, params=params, timeout=30.0)
                
                if response.status_code == 429:
                    print("Rate limited on API call. Proceeding with local search only.")
                else:
                    response.raise_for_status()
                    data = response.json()
                    api_entities = data.get("entityData", []) if isinstance(data, dict) else []
                    print(f"API returned {len(api_entities)} results")
                    
                    # Store API results in database for future fuzzy searches
                    from fedops_core.db.engine import AsyncSessionLocal
                    from fedops_core.db.models import Entity as DBEntity
                    from sqlalchemy import select
                    
                    async with AsyncSessionLocal() as db:
                        for entity_data in api_entities:
                            reg = entity_data.get("entityRegistration", {})
                            uei = reg.get("ueiSAM")
                            if not uei:
                                continue
                            
                            # Check if exists
                            result = await db.execute(select(DBEntity).where(DBEntity.uei == uei))
                            existing = result.scalars().first()
                            
                            if not existing:
                                # Create new entity
                                new_entity = DBEntity(
                                    uei=uei,
                                    legal_business_name=reg.get("legalBusinessName", ""),
                                    cage_code=reg.get("cageCode"),
                                    full_response=entity_data,
                                    last_synced_at=datetime.utcnow()
                                )
                                db.add(new_entity)
                        
                        await db.commit()
                        
            except Exception as e:
                print(f"Error calling SAM.gov API: {e}")
                # Continue with local search even if API fails
        
        # Now apply fuzzy matching to ALL locally stored entities
        if fuzzy:
            from fedops_core.db.engine import AsyncSessionLocal
            from fedops_core.db.models import Entity as DBEntity
            from sqlalchemy import select
            
            all_local_entities = []
            async with AsyncSessionLocal() as db:
                result = await db.execute(select(DBEntity))
                db_entities = result.scalars().all()
                
                # Convert DB entities to API format for fuzzy matching
                for db_entity in db_entities:
                    if db_entity.full_response:
                        all_local_entities.append(db_entity.full_response)
                    else:
                        # Create minimal entity structure
                        all_local_entities.append({
                            "entityRegistration": {
                                "ueiSAM": db_entity.uei,
                                "legalBusinessName": db_entity.legal_business_name,
                                "cageCode": db_entity.cage_code
                            }
                        })
            
            print(f"Applying fuzzy matching to {len(all_local_entities)} local entities")
            
            # Deduplicate and score
            unique_entities = deduplicate_entities(
                all_local_entities,
                legal_business_name,
                use_phonetic=use_phonetic
            )
            
            # Filter by similarity threshold
            filtered_entities = filter_by_similarity(unique_entities, min_similarity)
            print(f"Found {len(filtered_entities)} matches after fuzzy filtering")
            
            result = {
                "entityData": filtered_entities,
                "searchMetadata": {
                    "originalQuery": legal_business_name,
                    "apiResults": len(api_entities),
                    "localEntities": len(all_local_entities),
                    "filteredResults": len(filtered_entities),
                    "minSimilarity": min_similarity,
                    "fuzzyEnabled": True,
                    "phoneticEnabled": use_phonetic,
                    "abbreviationsEnabled": use_abbreviations,
                    "typosEnabled": use_typos,
                    "cached": False,
                    "cacheStats": get_cache_stats()
                }
            }
        else:
            # Non-fuzzy: just return API results
            result = {
                "entityData": api_entities,
                "searchMetadata": {
                    "originalQuery": legal_business_name,
                    "apiResults": len(api_entities),
                    "fuzzyEnabled": False,
                    "cached": False
                }
            }
        
        # Cache the result if we have results
        if not bypass_cache and len(result["entityData"]) > 0:
            cache_results(cache_key, result)
        
        return result

