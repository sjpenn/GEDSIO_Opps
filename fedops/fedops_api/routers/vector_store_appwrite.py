"""
Vector Store Router - Appwrite Version

API endpoints for managing vector store embeddings and queries.
Works with Appwrite Database for metadata and ChromaDB for vectors.
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Optional, Dict, Any
import logging
import asyncio
from pathlib import Path

from fedops_core.services.vector_store import VectorStore
from fedops_core.services.files_repository import FilesRepository
from fedops_core.services.opportunities_repository import OpportunitiesRepository

router = APIRouter()
logger = logging.getLogger(__name__)


def _get_vector_store_stats_sync():
    """Synchronous function to get vector store stats - runs in thread pool."""
    import chromadb
    from chromadb.config import Settings
    
    persist_dir = "./chroma_db"
    
    if not Path(persist_dir).exists():
        return {
            "status": "empty",
            "message": "Vector store not initialized - no embeddings stored yet",
            "total_collections": 0,
            "total_chunks": 0,
            "collections": []
        }
    
    client = chromadb.PersistentClient(
        path=persist_dir,
        settings=Settings(anonymized_telemetry=False)
    )
    
    collections = client.list_collections()
    
    collection_stats = []
    total_chunks = 0
    
    for coll in collections:
        count = coll.count()
        total_chunks += count
        collection_stats.append({
            "name": coll.name,
            "count": count,
            "metadata": coll.metadata
        })
    
    return {
        "status": "active",
        "total_collections": len(collections),
        "total_chunks": total_chunks,
        "collections": collection_stats
    }


@router.get("/stats")
async def get_vector_store_stats():
    """
    Get overall vector store statistics.
    
    Returns:
        Summary of all collections and total chunks
    """
    try:
        # Run blocking ChromaDB operations in thread pool
        result = await asyncio.to_thread(_get_vector_store_stats_sync)
        return result
        
    except Exception as e:
        logger.error(f"Error getting vector store stats: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


@router.post("/search")
async def search_vectors(
    query: str,
    opportunity_id: Optional[str] = None,
    entity_uei: Optional[str] = None,
    top_k: int = 10,
    section: Optional[str] = None
):
    """
    Semantic search across vector store.
    
    Args:
        query: Natural language search query
        opportunity_id: Optional filter by opportunity
        entity_uei: Optional filter by entity
        top_k: Number of results to return
        section: Optional section filter (L, M, H, C, B, I, K)
    """
    try:
        vector_store = VectorStore()
        
        filter_metadata = None
        if section:
            filter_metadata = {"section": section.upper()}
        
        # Search based on filters
        if opportunity_id:
            results = await vector_store.search(
                opportunity_id=int(opportunity_id) if opportunity_id.isdigit() else 0,
                query=query,
                top_k=top_k,
                filter_metadata=filter_metadata
            )
        elif entity_uei:
            results = await vector_store.search_entity(
                entity_uei=entity_uei,
                query=query,
                top_k=top_k
            )
        else:
            # Global search - try to search across all collections
            results = []
        
        return {
            "query": query,
            "section_filter": section,
            "result_count": len(results),
            "results": [
                {
                    "chunk_id": r.chunk_id,
                    "content": r.content[:500] + "..." if len(r.content) > 500 else r.content,
                    "score": r.score,
                    "metadata": r.metadata,
                    "filename": r.metadata.get("filename", "") if r.metadata else ""
                }
                for r in results
            ]
        }
    except Exception as e:
        logger.error(f"Error searching vectors: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/opportunity/{opportunity_id}/stats")
async def get_opportunity_vector_stats(opportunity_id: str):
    """
    Get vector store statistics for a specific opportunity.
    """
    try:
        # Verify opportunity exists in Appwrite
        opp_repo = OpportunitiesRepository()
        opportunity = await opp_repo.get(opportunity_id)
        
        if not opportunity:
            raise HTTPException(status_code=404, detail="Opportunity not found")
        
        vector_store = VectorStore()
        # Try to get stats - use int ID if possible
        opp_int_id = int(opportunity_id) if opportunity_id.isdigit() else hash(opportunity_id) % 1000000
        stats = await vector_store.get_collection_stats(opp_int_id)
        
        return {
            "opportunity_id": opportunity_id,
            "vector_store": stats
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting opportunity vector stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/opportunity/{opportunity_id}/search")
async def search_opportunity_vectors(
    opportunity_id: str,
    query: str,
    top_k: int = 10,
    section: Optional[str] = None
):
    """
    Semantic search within an opportunity's documents.
    
    Args:
        opportunity_id: The opportunity to search
        query: Natural language search query
        top_k: Number of results to return
        section: Optional section filter (L, M, H, C, B, I, K)
    """
    try:
        # Verify opportunity exists
        opp_repo = OpportunitiesRepository()
        opportunity = await opp_repo.get(opportunity_id)
        
        if not opportunity:
            raise HTTPException(status_code=404, detail="Opportunity not found")
        
        vector_store = VectorStore()
        
        filter_metadata = None
        if section:
            filter_metadata = {"section": section.upper()}
        
        # Convert string ID to int for vector store
        opp_int_id = int(opportunity_id) if opportunity_id.isdigit() else hash(opportunity_id) % 1000000
        
        results = await vector_store.search(
            opportunity_id=opp_int_id,
            query=query,
            top_k=top_k,
            filter_metadata=filter_metadata
        )
        
        return {
            "opportunity_id": opportunity_id,
            "query": query,
            "section_filter": section,
            "result_count": len(results),
            "results": [
                {
                    "chunk_id": r.chunk_id,
                    "content": r.content[:500] + "..." if len(r.content) > 500 else r.content,
                    "score": r.score,
                    "metadata": r.metadata
                }
                for r in results
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching opportunity vectors: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/entity/{entity_uei}/stats")
async def get_entity_vector_stats(entity_uei: str):
    """
    Get vector store statistics for an entity.
    """
    try:
        vector_store = VectorStore()
        stats = await vector_store.get_entity_stats(entity_uei)
        return stats
    except Exception as e:
        logger.error(f"Error getting entity vector stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/entity/{entity_uei}/search")
async def search_entity_vectors(
    entity_uei: str,
    query: str,
    opportunity_id: Optional[str] = None,
    top_k: int = 10
):
    """
    Semantic search within an entity's vector collections.
    """
    try:
        vector_store = VectorStore()
        
        opp_int_id = None
        if opportunity_id:
            opp_int_id = int(opportunity_id) if opportunity_id.isdigit() else hash(opportunity_id) % 1000000
        
        results = await vector_store.search_entity(
            entity_uei=entity_uei,
            query=query,
            opportunity_id=opp_int_id,
            top_k=top_k
        )
        
        return {
            "entity_uei": entity_uei,
            "query": query,
            "opportunity_id": opportunity_id,
            "result_count": len(results),
            "results": [
                {
                    "chunk_id": r.chunk_id,
                    "content": r.content[:500] + "..." if len(r.content) > 500 else r.content,
                    "score": r.score,
                    "metadata": r.metadata
                }
                for r in results
            ]
        }
    except Exception as e:
        logger.error(f"Error searching entity vectors: {e}")
        raise HTTPException(status_code=500, detail=str(e))
