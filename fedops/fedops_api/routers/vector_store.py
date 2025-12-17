"""
Vector Store Router - API endpoints for managing vector store embeddings and queries.
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional, Dict, Any
import logging

from fedops_core.db.engine import get_db
from fedops_core.db.models import StoredFile, Opportunity, DocumentChunk
from fedops_core.services.vector_store import VectorStore
from fedops_core.services.docling_chunker import DoclingChunker
from fedops_core.services.document_extractor import DocumentExtractor

router = APIRouter()
logger = logging.getLogger(__name__)


def _get_vector_store_stats_sync():
    """Synchronous function to get vector store stats - runs in thread pool."""
    import chromadb
    from chromadb.config import Settings
    from pathlib import Path
    
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
    
    Runs in a thread pool to avoid blocking the event loop.
    
    Returns:
        Summary of all collections and total chunks
    """
    import asyncio
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


@router.get("/opportunities/{opportunity_id}")
async def get_opportunity_vector_stats(
    opportunity_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get vector store statistics for a specific opportunity.
    """
    try:
        # Verify opportunity exists
        result = await db.execute(
            select(Opportunity).where(Opportunity.id == opportunity_id)
        )
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Opportunity not found")
        
        vector_store = VectorStore()
        stats = await vector_store.get_collection_stats(opportunity_id)
        
        # Get document chunks from database (if opportunity_id column exists)
        db_chunk_count = 0
        try:
            chunk_result = await db.execute(
                select(DocumentChunk).where(DocumentChunk.opportunity_id == opportunity_id)
            )
            db_chunks = chunk_result.scalars().all()
            db_chunk_count = len(db_chunks)
        except Exception as e:
            logger.warning(f"Could not query document chunks: {e}")
        
        return {
            "opportunity_id": opportunity_id,
            "vector_store": stats,
            "database_chunks": db_chunk_count
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting opportunity vector stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/opportunities/{opportunity_id}/generate")
async def generate_embeddings_for_opportunity(
    opportunity_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Generate embeddings for all documents in an opportunity.
    
    This will:
    1. Find all stored files for the opportunity
    2. Parse each document using Docling
    3. Chunk the documents
    4. Store embeddings in the vector store
    
    Runs as a background task for large documents.
    """
    # Verify opportunity exists
    result = await db.execute(
        select(Opportunity).where(Opportunity.id == opportunity_id)
    )
    opportunity = result.scalar_one_or_none()
    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    
    # Get all stored files for this opportunity
    files_result = await db.execute(
        select(StoredFile).where(StoredFile.opportunity_id == opportunity_id)
    )
    files = files_result.scalars().all()
    
    if not files:
        return {
            "status": "no_files",
            "message": "No files found for this opportunity",
            "opportunity_id": opportunity_id
        }
    
    # Prepare file list
    file_list = [
        {
            "id": f.id,
            "file_path": f.file_path,
            "filename": f.filename
        }
        for f in files
    ]
    
    # Run embedding generation in background
    background_tasks.add_task(
        _generate_embeddings_task,
        opportunity_id,
        file_list
    )
    
    return {
        "status": "started",
        "message": f"Generating embeddings for {len(files)} files in background",
        "opportunity_id": opportunity_id,
        "file_count": len(files)
    }


async def _generate_embeddings_task(opportunity_id: int, files: List[Dict[str, Any]]):
    """Background task to generate embeddings."""
    try:
        logger.info(f"Starting embedding generation for opportunity {opportunity_id}")
        
        extractor = DocumentExtractor()
        result = await extractor.ingest_all_documents(
            files=files,
            opportunity_id=opportunity_id,
            db_session=None  # No DB session in background task
        )
        
        logger.info(f"Embedding generation complete: {result}")
        
    except Exception as e:
        logger.error(f"Error generating embeddings for opportunity {opportunity_id}: {e}")


@router.post("/opportunities/{opportunity_id}/search")
async def search_opportunity_vectors(
    opportunity_id: int,
    query: str,
    top_k: int = 10,
    section: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Semantic search within an opportunity's documents.
    
    Args:
        opportunity_id: The opportunity to search
        query: Natural language search query
        top_k: Number of results to return
        section: Optional section filter (L, M, H, C, B, I, K)
    """
    # Verify opportunity exists
    result = await db.execute(
        select(Opportunity).where(Opportunity.id == opportunity_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Opportunity not found")
    
    vector_store = VectorStore()
    
    filter_metadata = None
    if section:
        filter_metadata = {"section": section.upper()}
    
    results = await vector_store.search(
        opportunity_id=opportunity_id,
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


@router.delete("/opportunities/{opportunity_id}")
async def delete_opportunity_vectors(
    opportunity_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete all vector embeddings for an opportunity.
    
    WARNING: This permanently removes the vector data.
    """
    # Verify opportunity exists
    result = await db.execute(
        select(Opportunity).where(Opportunity.id == opportunity_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Opportunity not found")
    
    vector_store = VectorStore()
    success = await vector_store.delete_opportunity(opportunity_id)
    
    return {
        "success": success,
        "opportunity_id": opportunity_id,
        "message": "Vector data deleted" if success else "Failed to delete"
    }


@router.post("/regenerate-all")
async def regenerate_all_embeddings(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Regenerate embeddings for ALL opportunities with stored files.
    
    WARNING: This is a long-running operation and will process all documents.
    """
    # Get all opportunities with files
    result = await db.execute(
        select(Opportunity)
        .where(Opportunity.id.in_(
            select(StoredFile.opportunity_id).distinct()
        ))
    )
    opportunities = result.scalars().all()
    
    if not opportunities:
        return {
            "status": "no_opportunities",
            "message": "No opportunities with files found"
        }
    
    # Queue each opportunity for background processing
    for opp in opportunities:
        files_result = await db.execute(
            select(StoredFile).where(StoredFile.opportunity_id == opp.id)
        )
        files = files_result.scalars().all()
        
        if files:
            file_list = [
                {"id": f.id, "file_path": f.file_path, "filename": f.filename}
                for f in files
            ]
            background_tasks.add_task(
                _generate_embeddings_task,
                opp.id,
                file_list
            )
    
    return {
        "status": "started",
        "message": f"Queued embedding generation for {len(opportunities)} opportunities",
        "opportunity_ids": [opp.id for opp in opportunities]
    }


# Entity-specific endpoints (using new entity-scoped methods)

@router.get("/entities/{entity_uei}/stats")
async def get_entity_vector_stats(entity_uei: str):
    """
    Get vector store statistics for an entity.
    """
    vector_store = VectorStore()
    stats = await vector_store.get_entity_stats(entity_uei)
    return stats


@router.post("/entities/{entity_uei}/search")
async def search_entity_vectors(
    entity_uei: str,
    query: str,
    opportunity_id: Optional[int] = None,
    top_k: int = 10
):
    """
    Semantic search within an entity's vector collections.
    """
    vector_store = VectorStore()
    
    results = await vector_store.search_entity(
        entity_uei=entity_uei,
        query=query,
        opportunity_id=opportunity_id,
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


@router.get("/entities/{entity_uei}/collections")
async def list_entity_collections(entity_uei: str):
    """
    List all vector collections for an entity.
    """
    vector_store = VectorStore()
    collections = await vector_store.list_entity_collections(entity_uei)
    return {
        "entity_uei": entity_uei,
        "collection_count": len(collections),
        "collections": collections
    }
