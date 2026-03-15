"""
search_service.py - Search Service

Business logic for semantic and keyword-based paper search.
Supports multiple search methods for comparison.
"""

from enum import Enum
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.paper_repository import PaperRepository
from src.services.embedding_service import EmbeddingService


class SearchMethod(str, Enum):
    """Available search methods."""
    SEMANTIC = "semantic"
    KEYWORD = "keyword"
    HYBRID = "hybrid"


class SearchService:
    """
    Service for paper search operations.
    
    Supports semantic, keyword (TF-IDF), and hybrid search modes.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = PaperRepository(db)
        self.embedding_service = EmbeddingService()
    
    async def search(
        self,
        query: str,
        method: SearchMethod = SearchMethod.SEMANTIC,
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Main search entry point.
        
        Dispatches to appropriate search method based on method parameter.
        
        Args:
            query: Search query text
            method: Search method (semantic, keyword, hybrid)
            top_k: Number of results to return
            filters: Optional filters (year, venue, etc.)
            
        Returns:
            Search results with scores and metadata
        """
        if method == SearchMethod.SEMANTIC:
            return await self._semantic_search(query, top_k, filters)
        elif method == SearchMethod.KEYWORD:
            return await self._keyword_search(query, top_k, filters)
        else:
            return await self._hybrid_search(query, top_k, filters)
    
    async def _semantic_search(
        self,
        query: str,
        top_k: int,
        filters: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Perform semantic search using embeddings.
        
        Uses sentence-transformers to embed query, then
        finds similar papers via pgvector cosine distance.
        """
        normalized_filters = filters.model_dump() if hasattr(filters, "model_dump") else filters
        query_vector = self.embedding_service.encode_text(query)
        matches = await self.repository.search_by_embedding(
            embedding=query_vector,
            top_k=top_k,
            filters=normalized_filters,
        )

        results = [
            {
                "paper": item["paper"],
                "score": item["score"],
                "highlights": None,
            }
            for item in matches
        ]
        
        return {
            "results": results,
            "method": "semantic",
            "total": len(results),
            "query": query,
        }
    
    async def _keyword_search(
        self,
        query: str,
        top_k: int,
        filters: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Perform keyword-based search using TF-IDF.
        
        Uses packages/nlp/baselines for traditional search.
        Good baseline for comparison in evaluation.
        """
        # TODO: Implement using packages/nlp baselines
        
        return {
            "results": [],
            "method": "keyword",
            "total": 0,
            "query": query,
        }
    
    async def _hybrid_search(
        self,
        query: str,
        top_k: int,
        filters: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Combine semantic and keyword search results.
        
        Uses reciprocal rank fusion to merge results from
        both search methods with configurable weights.
        """
        # Get results from both methods
        semantic_results = await self._semantic_search(query, top_k * 2, filters)
        keyword_results = await self._keyword_search(query, top_k * 2, filters)
        
        # TODO: Implement score fusion (e.g., reciprocal rank fusion)
        # combined = self._fuse_results(semantic_results, keyword_results, top_k)
        
        return {
            "results": [],
            "method": "hybrid",
            "total": 0,
            "query": query,
        }
