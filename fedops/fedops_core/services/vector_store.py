"""
Vector Store Service - ChromaDB integration for document chunk embeddings.

Provides semantic search capabilities for RAG-based document analysis.
"""

import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Result from vector similarity search."""
    chunk_id: int
    content: str
    score: float
    metadata: Dict[str, Any]


class VectorStore:
    """ChromaDB-based vector storage for document chunks."""
    
    def __init__(self, persist_dir: Optional[str] = None):
        """
        Initialize ChromaDB client.
        
        Args:
            persist_dir: Directory for persistent storage. If None, uses in-memory.
        """
        self._client = None
        self._embedding_function = None
        self.persist_dir = persist_dir or "./chroma_db"
        self._initialized = False
    
    def _ensure_initialized(self) -> bool:
        """Lazy initialization of ChromaDB client."""
        if self._initialized:
            return True
            
        try:
            import chromadb
            from chromadb.config import Settings
            
            # Create persist directory if needed
            Path(self.persist_dir).mkdir(parents=True, exist_ok=True)
            
            self._client = chromadb.PersistentClient(
                path=self.persist_dir,
                settings=Settings(anonymized_telemetry=False)
            )
            
            # Use default embedding function (all-MiniLM-L6-v2)
            from chromadb.utils import embedding_functions
            self._embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="all-MiniLM-L6-v2"
            )
            
            self._initialized = True
            logger.info(f"ChromaDB initialized at {self.persist_dir}")
            return True
            
        except ImportError as e:
            logger.warning(f"ChromaDB not available: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            return False
    
    def _get_collection_name(self, opportunity_id: int) -> str:
        """Get collection name for an opportunity."""
        return f"opportunity_{opportunity_id}"
    
    def _get_or_create_collection(self, opportunity_id: int):
        """Get or create a collection for an opportunity."""
        if not self._ensure_initialized():
            return None
            
        collection_name = self._get_collection_name(opportunity_id)
        return self._client.get_or_create_collection(
            name=collection_name,
            embedding_function=self._embedding_function,
            metadata={"opportunity_id": opportunity_id}
        )
    
    async def add_chunks(
        self,
        opportunity_id: int,
        chunks: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Add chunks with embeddings to the opportunity's collection.
        
        Args:
            opportunity_id: The opportunity ID
            chunks: List of chunk dicts with 'id', 'content', and 'metadata'
            
        Returns:
            List of vector IDs for the added chunks
        """
        if not self._ensure_initialized():
            logger.warning("Vector store not available, skipping chunk addition")
            return []
        
        collection = self._get_or_create_collection(opportunity_id)
        if not collection:
            return []
        
        try:
            # Prepare data for ChromaDB
            ids = [str(chunk['id']) for chunk in chunks]
            documents = [chunk['content'] for chunk in chunks]
            
            # Filter out None values from metadata - ChromaDB doesn't accept None
            def clean_metadata(meta: Dict[str, Any]) -> Dict[str, Any]:
                return {k: v for k, v in meta.items() if v is not None}
            
            metadatas = [clean_metadata(chunk.get('metadata', {})) for chunk in chunks]
            
            # Add to collection
            collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )
            
            logger.info(f"Added {len(chunks)} chunks to collection for opportunity {opportunity_id}")
            return ids
            
        except Exception as e:
            logger.error(f"Error adding chunks to vector store: {e}")
            return []
    
    async def add_chunks_batched(
        self,
        opportunity_id: int,
        chunks: List[Dict[str, Any]],
        batch_size: int = 100,
        progress_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Add chunks in batches with progress tracking.
        
        Args:
            opportunity_id: The opportunity ID
            chunks: List of chunk dicts with 'id', 'content', and 'metadata'
            batch_size: Number of chunks to process per batch
            progress_callback: Optional async function(processed, total, message) for progress updates
            
        Returns:
            Dict with total_added, batches_processed, and errors
        """
        import asyncio
        
        total_chunks = len(chunks)
        total_added = 0
        batches_processed = 0
        errors = []
        
        if progress_callback:
            await progress_callback(0, total_chunks, f"Starting embedding for {total_chunks} chunks...")
        
        for i in range(0, total_chunks, batch_size):
            batch = chunks[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (total_chunks + batch_size - 1) // batch_size
            
            try:
                # Run the blocking embedding operation in a thread pool
                result = await asyncio.to_thread(
                    self._add_chunks_sync,
                    opportunity_id,
                    batch
                )
                total_added += len(result)
                batches_processed += 1
                
                if progress_callback:
                    percent = int((i + len(batch)) / total_chunks * 100)
                    await progress_callback(
                        i + len(batch), 
                        total_chunks, 
                        f"Embedding batch {batch_num}/{total_batches} ({percent}%)"
                    )
                    
            except Exception as e:
                errors.append({"batch": batch_num, "error": str(e)})
                logger.error(f"Error in batch {batch_num}: {e}")
        
        if progress_callback:
            await progress_callback(total_chunks, total_chunks, f"Embedding complete: {total_added} chunks")
        
        return {
            "total_added": total_added,
            "total_chunks": total_chunks,
            "batches_processed": batches_processed,
            "errors": errors
        }
    
    def _add_chunks_sync(
        self,
        opportunity_id: int,
        chunks: List[Dict[str, Any]]
    ) -> List[str]:
        """Synchronous version of add_chunks for running in thread pool."""
        if not self._ensure_initialized():
            return []
        
        collection = self._get_or_create_collection(opportunity_id)
        if not collection:
            return []
        
        try:
            ids = [str(chunk['id']) for chunk in chunks]
            documents = [chunk['content'] for chunk in chunks]
            
            def clean_metadata(meta: Dict[str, Any]) -> Dict[str, Any]:
                return {k: v for k, v in meta.items() if v is not None}
            
            metadatas = [clean_metadata(chunk.get('metadata', {})) for chunk in chunks]
            
            collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )
            
            return ids
            
        except Exception as e:
            logger.error(f"Error adding chunks sync: {e}")
            return []
    
    async def search(
        self,
        opportunity_id: int,
        query: str,
        top_k: int = 10,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """
        Semantic search within an opportunity's chunks.
        
        Args:
            opportunity_id: The opportunity ID
            query: Search query text
            top_k: Number of results to return
            filter_metadata: Optional metadata filters (e.g., {"section": "L"})
            
        Returns:
            List of SearchResult objects
        """
        if not self._ensure_initialized():
            logger.warning("Vector store not available")
            return []
        
        collection = self._get_or_create_collection(opportunity_id)
        if not collection:
            return []
        
        try:
            # Build query parameters
            query_params = {
                "query_texts": [query],
                "n_results": top_k
            }
            
            if filter_metadata:
                query_params["where"] = filter_metadata
            
            results = collection.query(**query_params)
            
            # Convert to SearchResult objects
            search_results = []
            if results and results['ids'] and results['ids'][0]:
                for i, chunk_id in enumerate(results['ids'][0]):
                    search_results.append(SearchResult(
                        chunk_id=int(chunk_id),
                        content=results['documents'][0][i] if results['documents'] else "",
                        score=1 - results['distances'][0][i] if results['distances'] else 0.0,
                        metadata=results['metadatas'][0][i] if results['metadatas'] else {}
                    ))
            
            logger.debug(f"Search returned {len(search_results)} results for opportunity {opportunity_id}")
            return search_results
            
        except Exception as e:
            logger.error(f"Error searching vector store: {e}")
            return []
    
    async def delete_opportunity(self, opportunity_id: int) -> bool:
        """
        Delete all vectors for an opportunity.
        
        Args:
            opportunity_id: The opportunity ID
            
        Returns:
            True if successful
        """
        if not self._ensure_initialized():
            return False
        
        try:
            collection_name = self._get_collection_name(opportunity_id)
            self._client.delete_collection(collection_name)
            logger.info(f"Deleted vector collection for opportunity {opportunity_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting vector collection: {e}")
            return False
    
    async def get_collection_stats(self, opportunity_id: int) -> Dict[str, Any]:
        """Get statistics for an opportunity's collection."""
        if not self._ensure_initialized():
            return {"error": "Vector store not available"}
        
        try:
            collection = self._get_or_create_collection(opportunity_id)
            if collection:
                return {
                    "name": collection.name,
                    "count": collection.count(),
                    "metadata": collection.metadata
                }
            return {"error": "Collection not found"}
        except Exception as e:
            return {"error": str(e)}
    
    # ===== Entity-Scoped Methods for Multi-Entity Support =====
    
    def _get_entity_collection_name(self, entity_uei: str, opportunity_id: int) -> str:
        """Get collection name scoped to an entity and opportunity."""
        # Sanitize UEI for collection name (ChromaDB has restrictions on names)
        safe_uei = entity_uei.replace('-', '_').replace(' ', '_').lower()[:20]
        return f"entity_{safe_uei}_opp_{opportunity_id}"
    
    def _get_entity_profile_collection_name(self, entity_uei: str) -> str:
        """Get collection name for entity profile documents (not opportunity-specific)."""
        safe_uei = entity_uei.replace('-', '_').replace(' ', '_').lower()[:20]
        return f"entity_{safe_uei}_profile"
    
    def _get_or_create_entity_collection(self, entity_uei: str, opportunity_id: Optional[int] = None):
        """Get or create a collection for an entity's data."""
        if not self._ensure_initialized():
            return None
        
        if opportunity_id:
            collection_name = self._get_entity_collection_name(entity_uei, opportunity_id)
            metadata = {"entity_uei": entity_uei, "opportunity_id": opportunity_id}
        else:
            collection_name = self._get_entity_profile_collection_name(entity_uei)
            metadata = {"entity_uei": entity_uei, "type": "profile"}
        
        return self._client.get_or_create_collection(
            name=collection_name,
            embedding_function=self._embedding_function,
            metadata=metadata
        )
    
    async def add_entity_chunks(
        self,
        entity_uei: str,
        chunks: List[Dict[str, Any]],
        opportunity_id: Optional[int] = None
    ) -> List[str]:
        """
        Add chunks to an entity-scoped collection.
        
        Args:
            entity_uei: The entity's UEI
            chunks: List of chunk dicts with 'id', 'content', and 'metadata'
            opportunity_id: Optional opportunity ID for opportunity-specific data
            
        Returns:
            List of vector IDs for the added chunks
        """
        if not self._ensure_initialized():
            logger.warning("Vector store not available, skipping entity chunk addition")
            return []
        
        collection = self._get_or_create_entity_collection(entity_uei, opportunity_id)
        if not collection:
            return []
        
        try:
            ids = [str(chunk['id']) for chunk in chunks]
            documents = [chunk['content'] for chunk in chunks]
            metadatas = [chunk.get('metadata', {}) for chunk in chunks]
            
            # Add entity_uei to all metadata
            for meta in metadatas:
                meta['entity_uei'] = entity_uei
            
            collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )
            
            collection_type = f"opportunity {opportunity_id}" if opportunity_id else "profile"
            logger.info(f"Added {len(chunks)} chunks to entity {entity_uei} {collection_type} collection")
            return ids
            
        except Exception as e:
            logger.error(f"Error adding entity chunks to vector store: {e}")
            return []
    
    async def search_entity(
        self,
        entity_uei: str,
        query: str,
        opportunity_id: Optional[int] = None,
        top_k: int = 10,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """
        Semantic search within an entity's collection.
        
        Args:
            entity_uei: The entity's UEI
            query: Search query text
            opportunity_id: Optional opportunity ID to search within
            top_k: Number of results to return
            filter_metadata: Optional metadata filters
            
        Returns:
            List of SearchResult objects
        """
        if not self._ensure_initialized():
            logger.warning("Vector store not available")
            return []
        
        collection = self._get_or_create_entity_collection(entity_uei, opportunity_id)
        if not collection:
            return []
        
        try:
            query_params = {
                "query_texts": [query],
                "n_results": top_k
            }
            
            if filter_metadata:
                query_params["where"] = filter_metadata
            
            results = collection.query(**query_params)
            
            search_results = []
            if results and results['ids'] and results['ids'][0]:
                for i, chunk_id in enumerate(results['ids'][0]):
                    search_results.append(SearchResult(
                        chunk_id=int(chunk_id),
                        content=results['documents'][0][i] if results['documents'] else "",
                        score=1 - results['distances'][0][i] if results['distances'] else 0.0,
                        metadata=results['metadatas'][0][i] if results['metadatas'] else {}
                    ))
            
            return search_results
            
        except Exception as e:
            logger.error(f"Error searching entity vector store: {e}")
            return []
    
    async def get_entity_stats(self, entity_uei: str) -> Dict[str, Any]:
        """
        Get statistics for all collections belonging to an entity.
        
        Returns dict with collection counts and total chunks.
        """
        if not self._ensure_initialized():
            return {"error": "Vector store not available"}
        
        try:
            # List all collections and filter by entity prefix
            safe_uei = entity_uei.replace('-', '_').replace(' ', '_').lower()[:20]
            prefix = f"entity_{safe_uei}"
            
            all_collections = self._client.list_collections()
            entity_collections = [c for c in all_collections if c.name.startswith(prefix)]
            
            stats = {
                "entity_uei": entity_uei,
                "total_collections": len(entity_collections),
                "total_chunks": 0,
                "collections": []
            }
            
            for collection in entity_collections:
                count = collection.count()
                stats["total_chunks"] += count
                stats["collections"].append({
                    "name": collection.name,
                    "count": count,
                    "metadata": collection.metadata
                })
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting entity stats: {e}")
            return {"error": str(e)}
    
    async def delete_entity_data(self, entity_uei: str) -> bool:
        """
        Delete all vector collections for an entity.
        
        WARNING: This permanently removes all embeddings for this entity.
        
        Returns:
            True if successful
        """
        if not self._ensure_initialized():
            return False
        
        try:
            safe_uei = entity_uei.replace('-', '_').replace(' ', '_').lower()[:20]
            prefix = f"entity_{safe_uei}"
            
            all_collections = self._client.list_collections()
            deleted_count = 0
            
            for collection in all_collections:
                if collection.name.startswith(prefix):
                    self._client.delete_collection(collection.name)
                    deleted_count += 1
            
            logger.info(f"Deleted {deleted_count} vector collections for entity {entity_uei}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting entity vector data: {e}")
            return False
    
    async def list_entity_collections(self, entity_uei: str) -> List[str]:
        """List all collection names for an entity."""
        if not self._ensure_initialized():
            return []
        
        try:
            safe_uei = entity_uei.replace('-', '_').replace(' ', '_').lower()[:20]
            prefix = f"entity_{safe_uei}"
            
            all_collections = self._client.list_collections()
            return [c.name for c in all_collections if c.name.startswith(prefix)]
            
        except Exception as e:
            logger.error(f"Error listing entity collections: {e}")
            return []

