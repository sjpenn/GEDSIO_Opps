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
            metadatas = [chunk.get('metadata', {}) for chunk in chunks]
            
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
