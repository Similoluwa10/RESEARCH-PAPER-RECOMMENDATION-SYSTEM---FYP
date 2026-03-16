"""
search_service.py - Search Service

Business logic for semantic and keyword-based paper search.
Supports multiple search methods for comparison.
"""

from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.paper_repository import PaperRepository
from src.services.embedding_service import EmbeddingService
from src.schemas.search import SearchRequest, SearchResponse
from src.core.enums import SearchMethod

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
        search_request: SearchRequest,
    ) -> SearchResponse:
        """
        Main search entry point.
        
        Dispatches to appropriate search method based on method parameter.
        
        Args:
            search_request: Encapsulated search parameters
            
        Returns:
            Search results with scores and metadata
        """
        if search_request.method == SearchMethod.SEMANTIC:
            return await self._semantic_search(search_request)
        elif search_request.method == SearchMethod.KEYWORD:
            return await self._keyword_search(search_request)
        else:
            return await self._hybrid_search(search_request)

    async def _semantic_search(
        self,
        search_request: SearchRequest,
    ) -> SearchResponse:
        """
        Perform semantic search using embeddings.
        
        Uses sentence-transformers to embed query, then
        finds similar papers via pgvector cosine distance.
        """
        normalized_filters = search_request.filters.model_dump() if hasattr(search_request.filters, "model_dump") else search_request.filters
        query_vector = self.embedding_service.encode_text(search_request.query)
        matches = await self.repository.search_by_embedding(
            embedding=query_vector,
            top_k=search_request.top_k,
            filters=normalized_filters,
        )

        results = [
            {
                "paper": item.get("paper"),
                "score": float(item.get("score", 0.0)),
                "highlights": item.get("highlights"),
            }
            for item in matches
        ]
                
        response = {
            "results": results,
            "method": "semantic",
            "total": len(results),
            "query": search_request.query,
        }
        
        return SearchResponse.from_model(response)
    
    async def _keyword_search(
        self,
        search_request: SearchRequest,
    ) -> SearchResponse:
        """
        Perform keyword-based search using TF-IDF.
        
        Uses packages/nlp/baselines for traditional search.
        Good baseline for comparison in evaluation.
        """
        # TODO: Implement using packages/nlp baselines
        
        result = {
            "results": [],
            "method": "keyword",
            "total": 0,
            "query": search_request.query,
        }
        
        return SearchResponse.from_model(result)
    
    async def _hybrid_search(
        self,
        search_request: SearchRequest,
    ) -> SearchResponse:
        """
        Combine semantic and keyword search results.
        
        Uses reciprocal rank fusion to merge results from
        both search methods with configurable weights.
        """
        search_request.top_k = search_request.top_k * 2
          
        # Get results from both methods
        semantic_results = await self._semantic_search(search_request)
        keyword_results = await self._keyword_search(search_request)
        
        
        
        # TODO: Implement score fusion (e.g., reciprocal rank fusion)
        # combined = self._fuse_results(semantic_results, keyword_results, top_k)
        
        result = {
            "results": [],
            "method": "hybrid",
            "total": 0,
            "query": search_request.query,
        }
        
        return SearchResponse.from_model(result)
