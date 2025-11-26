"""
Fuzzy search utilities for entity name matching.

Provides text normalization, similarity scoring, pattern generation, phonetic matching,
abbreviation expansion, typo tolerance, and caching to find entities with similar names.
"""

import re
import hashlib
from typing import List, Dict, Any, Set, Optional, Tuple
from difflib import SequenceMatcher
from cachetools import TTLCache
from datetime import datetime

# Optional imports with fallbacks
try:
    from metaphone import doublemetaphone
    PHONETIC_AVAILABLE = True
except ImportError:
    PHONETIC_AVAILABLE = False
    print("Warning: metaphone not available, phonetic matching disabled")

try:
    import Levenshtein
    LEVENSHTEIN_AVAILABLE = True
except ImportError:
    LEVENSHTEIN_AVAILABLE = False
    print("Warning: python-Levenshtein not available, using slower fallback")


# Cache configuration
SEARCH_CACHE = TTLCache(maxsize=1000, ttl=3600)  # 1 hour TTL
CACHE_STATS = {"hits": 0, "misses": 0}


# Abbreviation dictionary
ABBREVIATIONS = {
    # Business entities
    "corp": "corporation",
    "inc": "incorporated",
    "llc": "limited liability company",
    "ltd": "limited",
    "co": "company",
    "plc": "public limited company",
    
    # Descriptors
    "intl": "international",
    "natl": "national",
    "tech": "technology",
    "sys": "systems",
    "svcs": "services",
    "mfg": "manufacturing",
    "ind": "industries",
    "grp": "group",
    "assoc": "associates",
    "bros": "brothers",
    
    # Common words
    "dept": "department",
    "div": "division",
    "dist": "district",
    "fed": "federal",
    "govt": "government",
    "mgmt": "management",
}


def normalize_text(text: str) -> str:
    """
    Normalize text for comparison by removing special characters and converting to lowercase.
    
    Args:
        text: Input text to normalize
        
    Returns:
        Normalized text (lowercase, alphanumeric only)
    """
    # Convert to lowercase
    text = text.lower()
    # Remove all non-alphanumeric characters except spaces
    text = re.sub(r'[^a-z0-9\s]', '', text)
    # Collapse multiple spaces into one
    text = re.sub(r'\s+', ' ', text)
    # Strip leading/trailing spaces
    return text.strip()


def calculate_similarity(str1: str, str2: str) -> float:
    """
    Calculate similarity ratio between two strings using Levenshtein distance.
    
    Args:
        str1: First string
        str2: Second string
        
    Returns:
        Similarity ratio between 0.0 and 1.0
    """
    # Normalize both strings for comparison
    norm1 = normalize_text(str1)
    norm2 = normalize_text(str2)
    
    if LEVENSHTEIN_AVAILABLE:
        # Use faster Levenshtein library
        return Levenshtein.ratio(norm1, norm2)
    else:
        # Fallback to SequenceMatcher
        return SequenceMatcher(None, norm1, norm2).ratio()


def phonetic_encode(text: str) -> Tuple[str, str]:
    """
    Encode text using Double Metaphone algorithm for phonetic matching.
    
    Args:
        text: Text to encode
        
    Returns:
        Tuple of (primary_code, secondary_code)
    """
    if not PHONETIC_AVAILABLE:
        return ("", "")
    
    normalized = normalize_text(text)
    primary, secondary = doublemetaphone(normalized)
    return (primary or "", secondary or "")


def phonetic_similarity(str1: str, str2: str) -> float:
    """
    Calculate phonetic similarity between two strings.
    
    Args:
        str1: First string
        str2: Second string
        
    Returns:
        Similarity score between 0.0 and 1.0
    """
    if not PHONETIC_AVAILABLE:
        return 0.0
    
    primary1, secondary1 = phonetic_encode(str1)
    primary2, secondary2 = phonetic_encode(str2)
    
    # Check if any codes match
    if primary1 and primary2 and primary1 == primary2:
        return 1.0
    if secondary1 and secondary2 and secondary1 == secondary2:
        return 0.9
    if primary1 and secondary2 and primary1 == secondary2:
        return 0.8
    if secondary1 and primary2 and secondary1 == primary2:
        return 0.8
    
    return 0.0


def expand_abbreviations(text: str) -> List[str]:
    """
    Generate variations with abbreviations expanded.
    
    Args:
        text: Text containing potential abbreviations
        
    Returns:
        List of text variations with expansions
    """
    variations = [text]
    normalized = normalize_text(text)
    words = normalized.split()
    
    # Try expanding each word
    for i, word in enumerate(words):
        if word in ABBREVIATIONS:
            expanded_words = words.copy()
            expanded_words[i] = ABBREVIATIONS[word]
            variations.append(' '.join(expanded_words))
    
    return list(set(variations))


def contract_abbreviations(text: str) -> List[str]:
    """
    Generate variations with words contracted to abbreviations.
    
    Args:
        text: Text to contract
        
    Returns:
        List of text variations with contractions
    """
    variations = [text]
    normalized = normalize_text(text)
    words = normalized.split()
    
    # Reverse lookup for abbreviations
    reverse_abbrev = {v: k for k, v in ABBREVIATIONS.items()}
    
    # Try contracting each word
    for i, word in enumerate(words):
        if word in reverse_abbrev:
            contracted_words = words.copy()
            contracted_words[i] = reverse_abbrev[word]
            variations.append(' '.join(contracted_words))
    
    return list(set(variations))


def generate_typo_variations(text: str, max_variations: int = 3) -> List[str]:
    """
    Generate common typo variations of the text.
    
    Args:
        text: Original text
        max_variations: Maximum number of variations to generate
        
    Returns:
        List of typo variations
    """
    variations = []
    normalized = normalize_text(text)
    
    # Only generate typos for words longer than 3 characters
    words = normalized.split()
    for word in words:
        if len(word) <= 3:
            continue
        
        # Adjacent character swaps (most common typo)
        for i in range(len(word) - 1):
            typo = word[:i] + word[i+1] + word[i] + word[i+2:]
            variations.append(normalized.replace(word, typo))
            if len(variations) >= max_variations:
                return variations
    
    return variations[:max_variations]


def generate_search_patterns(
    query: str,
    use_abbreviations: bool = True,
    use_typos: bool = True,
    use_phonetic: bool = True
) -> List[str]:
    """
    Generate multiple search pattern variations for fuzzy matching.
    
    Args:
        query: Original search query
        use_abbreviations: Include abbreviation expansions/contractions
        use_typos: Include typo variations
        use_phonetic: Include phonetic variations
        
    Returns:
        List of search pattern variations
    """
    patterns = set()
    
    # Add original query
    patterns.add(query)
    
    # Normalize and add
    normalized = normalize_text(query)
    patterns.add(normalized)
    
    # Version without spaces
    no_spaces = normalized.replace(' ', '')
    if no_spaces != normalized:
        patterns.add(no_spaces)
    
    # Version with spaces between camelCase or words
    spaced = re.sub(r'([a-z])([A-Z])', r'\1 \2', query)
    if spaced != query:
        patterns.add(normalize_text(spaced))
    
    # Add version with common separators replaced by spaces
    for separator in ['-', '_', '.']:
        if separator in query:
            separated = query.replace(separator, ' ')
            patterns.add(normalize_text(separated))
    
    # Abbreviation variations
    if use_abbreviations:
        for pattern in list(patterns):
            patterns.update(expand_abbreviations(pattern))
            patterns.update(contract_abbreviations(pattern))
    
    # Typo variations (limited to avoid too many API calls)
    if use_typos:
        for pattern in list(patterns)[:5]:  # Only first 5 patterns
            patterns.update(generate_typo_variations(pattern, max_variations=2))
    
    # Remove empty strings
    patterns.discard('')
    
    return list(patterns)


def generate_sam_search_queries(
    query: str,
    use_abbreviations: bool = True,
    use_typos: bool = True,
    use_phonetic: bool = True
) -> List[str]:
    """
    Generate SAM.gov API search query strings for fuzzy matching.
    
    Args:
        query: Original search query
        use_abbreviations: Include abbreviation variations
        use_typos: Include typo variations
        use_phonetic: Include phonetic variations
        
    Returns:
        List of SAM.gov query strings with wildcards
    """
    patterns = generate_search_patterns(query, use_abbreviations, use_typos, use_phonetic)
    queries = []
    
    for pattern in patterns:
        # Add wildcard search for each pattern
        queries.append(f"(legalBusinessName:*{pattern}*)")
        
        # For patterns with spaces, also try without wildcards between words
        if ' ' in pattern:
            # Try exact phrase match
            queries.append(f'(legalBusinessName:"{pattern}")')
            
            # Try each word separately with AND
            words = pattern.split()
            if len(words) > 1:
                word_query = ' AND '.join([f'(legalBusinessName:*{word}*)' for word in words])
                queries.append(word_query)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_queries = []
    for q in queries:
        if q not in seen:
            seen.add(q)
            unique_queries.append(q)
    
    # Limit total queries to avoid overwhelming the API
    return unique_queries[:3]


def deduplicate_entities(
    entities: List[Dict[str, Any]],
    original_query: str,
    use_phonetic: bool = True
) -> List[Dict[str, Any]]:
    """
    Deduplicate entities by UEI and add similarity scores.
    
    Args:
        entities: List of entity dictionaries from SAM.gov
        original_query: Original search query for similarity calculation
        use_phonetic: Include phonetic similarity in scoring
        
    Returns:
        Deduplicated list of entities with similarity scores, sorted by score
    """
    seen_ueis: Set[str] = set()
    unique_entities = []
    
    for entity in entities:
        # Extract UEI from entity registration
        reg = entity.get("entityRegistration", {})
        uei = reg.get("ueiSAM")
        name = reg.get("legalBusinessName", "")
        
        if not uei or uei in seen_ueis:
            continue
        
        seen_ueis.add(uei)
        
        # Calculate text similarity score
        text_similarity = calculate_similarity(original_query, name)
        
        # Calculate phonetic similarity if enabled
        phonetic_score = 0.0
        if use_phonetic and PHONETIC_AVAILABLE:
            phonetic_score = phonetic_similarity(original_query, name)
        
        # Combined score: weighted average (70% text, 30% phonetic)
        if phonetic_score > 0:
            combined_similarity = (text_similarity * 0.7) + (phonetic_score * 0.3)
        else:
            combined_similarity = text_similarity
        
        # Add metadata to entity
        entity["_fuzzy_match"] = {
            "similarity_score": combined_similarity,
            "text_similarity": text_similarity,
            "phonetic_similarity": phonetic_score,
            "original_query": original_query,
            "matched_name": name
        }
        
        unique_entities.append(entity)
    
    # Sort by similarity score (highest first)
    unique_entities.sort(key=lambda e: e.get("_fuzzy_match", {}).get("similarity_score", 0), reverse=True)
    
    return unique_entities


def filter_by_similarity(entities: List[Dict[str, Any]], min_similarity: float = 0.5) -> List[Dict[str, Any]]:
    """
    Filter entities by minimum similarity threshold.
    
    Args:
        entities: List of entities with fuzzy match metadata
        min_similarity: Minimum similarity score (0.0 to 1.0)
        
    Returns:
        Filtered list of entities meeting the threshold
    """
    return [
        entity for entity in entities
        if entity.get("_fuzzy_match", {}).get("similarity_score", 0) >= min_similarity
    ]


def get_match_quality(similarity: float) -> str:
    """
    Categorize match quality based on similarity score.
    
    Args:
        similarity: Similarity score between 0.0 and 1.0
        
    Returns:
        Match quality category: "exact", "high", "medium", or "low"
    """
    if similarity >= 0.95:
        return "exact"
    elif similarity >= 0.80:
        return "high"
    elif similarity >= 0.60:
        return "medium"
    else:
        return "low"


def generate_cache_key(query: str, **params) -> str:
    """
    Generate a cache key from query and parameters.
    
    Args:
        query: Search query
        **params: Additional parameters
        
    Returns:
        Cache key string
    """
    # Normalize query for consistent caching
    normalized_query = normalize_text(query)
    
    # Create a deterministic string from params
    param_str = '|'.join(f"{k}:{v}" for k, v in sorted(params.items()))
    
    # Generate hash
    cache_str = f"{normalized_query}|{param_str}"
    return hashlib.md5(cache_str.encode()).hexdigest()


def get_cached_results(cache_key: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve results from cache.
    
    Args:
        cache_key: Cache key
        
    Returns:
        Cached results or None
    """
    if cache_key in SEARCH_CACHE:
        CACHE_STATS["hits"] += 1
        return SEARCH_CACHE[cache_key]
    
    CACHE_STATS["misses"] += 1
    return None


def cache_results(cache_key: str, results: Dict[str, Any]) -> None:
    """
    Store results in cache.
    
    Args:
        cache_key: Cache key
        results: Results to cache
    """
    SEARCH_CACHE[cache_key] = results


def get_cache_stats() -> Dict[str, Any]:
    """
    Get cache statistics.
    
    Returns:
        Dictionary with cache stats
    """
    total = CACHE_STATS["hits"] + CACHE_STATS["misses"]
    hit_rate = (CACHE_STATS["hits"] / total * 100) if total > 0 else 0
    
    return {
        "hits": CACHE_STATS["hits"],
        "misses": CACHE_STATS["misses"],
        "total_requests": total,
        "hit_rate_percent": round(hit_rate, 2),
        "cache_size": len(SEARCH_CACHE),
        "cache_maxsize": SEARCH_CACHE.maxsize
    }


def clear_cache() -> None:
    """Clear the search cache."""
    SEARCH_CACHE.clear()
    CACHE_STATS["hits"] = 0
    CACHE_STATS["misses"] = 0
