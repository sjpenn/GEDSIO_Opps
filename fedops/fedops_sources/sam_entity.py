import httpx
from typing import Optional, Dict, Any, List
from fedops_core.settings import settings
from fedops_sources.fuzzy_search import (
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
                # SAM API returns a wrapper with "entityData" list
                if isinstance(data, dict) and "entityData" in data:
                    entity_list = data["entityData"]
                    if isinstance(entity_list, list) and len(entity_list) > 0:
                        return entity_list[0]
                
                # Fallback if structure is different (e.g. direct list)
                if isinstance(data, list) and len(data) > 0:
                     return data[0]
                
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
        2. Apply fuzzy matching to returned entities (no database persistence)
        
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
            # Surface a clear error instead of silently returning nothing
            raise ValueError("SAM_API_KEY not set; configure it in .env for entity search to work.")
        
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
        api_error: Optional[str] = None
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
                        
            except httpx.HTTPStatusError as e:
                api_error = f"SAM.gov API error {e.response.status_code}: {e.response.text[:200]}"
                print(api_error)
            except Exception as e:
                api_error = f"Error calling SAM.gov API: {e}"
                print(api_error)
        
        # Apply fuzzy matching to returned entities
        if fuzzy:
            # Deduplicate and score against the current API response
            unique_entities = deduplicate_entities(
                api_entities,
                legal_business_name,
                use_phonetic=use_phonetic
            )
            
            # Filter by similarity threshold
            filtered_entities = filter_by_similarity(unique_entities, min_similarity)
            print(f"Found {len(filtered_entities)} matches after fuzzy filtering")

            # If the external call failed and we also have no data, surface the error
            if api_error and len(api_entities) == 0 and len(filtered_entities) == 0:
                raise ValueError(api_error)
            
            result = {
                "entityData": filtered_entities,
                "searchMetadata": {
                    "originalQuery": legal_business_name,
                    "apiResults": len(api_entities),
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
            if api_error and len(api_entities) == 0:
                raise ValueError(api_error)
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
