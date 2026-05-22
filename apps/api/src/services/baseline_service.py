"""
baseline_service.py - Baseline Service

TF-IDF baseline service for comparing against semantic search.
Used for evaluation and performance benchmarking.
"""

import logging
import sys
import os
from typing import List, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.paper_repository import PaperRepository
from src.schemas.search import SearchResponse

# Import TF-IDF baseline
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'packages'))
from nlp.src.baselines import TFIDFBaseline

logger = logging.getLogger(__name__)


class BaselineService:
    """
    Service for baseline search methods.
    
    Provides TF-IDF based search for comparison with semantic methods.
    Used for evaluation and benchmarking.
    """
    
    def __init__(self, db: AsyncSession):
        """Initialize baseline service."""
        self.db = db
        self.repository = PaperRepository(db)
        self.tfidf_model = None
        self._corpus_papers = []
        self._is_fitted = False
    
    async def initialize(self) -> None:
        """
        Initialize and fit the TF-IDF model on all papers.
        
        This should be called once during application startup
        or when the corpus changes.
        """
        try:
            logger.info("Initializing TF-IDF baseline...")
            
            # Fetch all papers
            papers = await self.repository.get_all(limit=100000)
            self._corpus_papers = papers
            
            if not papers:
                logger.warning("No papers found for TF-IDF initialization")
                return
            
            # Create document strings (combine title, abstract, keywords)
            documents = []
            for paper in papers:
                doc = f"{paper.title} {paper.abstract}"
                if paper.keywords:
                    doc += f" {' '.join(paper.keywords)}"
                documents.append(doc)
            
            # Initialize and fit TF-IDF
            self.tfidf_model = TFIDFBaseline(
                max_features=10000,
                ngram_range=(1, 2),
                min_df=2,
                max_df=0.95,
            )
            self.tfidf_model.fit(documents)
            self._is_fitted = True
            
            logger.info(f"TF-IDF baseline initialized with {len(papers)} papers")
            
        except Exception as e:
            logger.error(f"Error initializing TF-IDF baseline: {e}")
            self._is_fitted = False
    
    async def search(
        self,
        query: str,
        top_k: int = 10,
        filters: dict = None,
    ) -> SearchResponse:
        """
        Perform TF-IDF based search.
        
        Args:
            query: Query text
            top_k: Number of results
            filters: Optional filters (category, year, venue)
            
        Returns:
            SearchResponse with results
        """
        if not self._is_fitted:
            await self.initialize()
        
        if not self._is_fitted:
            return SearchResponse.from_model({
                "results": [],
                "method": "keyword",
                "total": 0,
                "query": query,
                "error": "TF-IDF model not initialized",
            })
        
        try:
            # Get TF-IDF results
            results = self.tfidf_model.search(query, top_k=top_k * 2)  # Get extra for filtering
            
            # Build response with paper details
            response_results = []
            for idx, score in results:
                if idx < len(self._corpus_papers):
                    paper = self._corpus_papers[idx]
                    
                    # Apply filters if provided
                    if filters:
                        if filters.get("category") and paper.category != filters["category"]:
                            continue
                        if filters.get("year") and paper.year != filters["year"]:
                            continue
                        if filters.get("venue") and paper.venue != filters.get("venue"):
                            continue
                    
                    response_results.append({
                        "paper": {
                            "id": str(paper.id),
                            "title": paper.title,
                            "abstract": paper.abstract,
                            "authors": paper.authors,
                            "year": paper.year,
                            "venue": paper.venue,
                            "category": paper.category,
                            "source": paper.source,
                            "keywords": paper.keywords,
                            "doi": paper.doi,
                            "url": paper.url,
                            "created_at": paper.created_at.isoformat() if paper.created_at else None,
                            "updated_at": paper.updated_at.isoformat() if paper.updated_at else None,
                        },
                        "score": float(score),
                    })
                    
                    if len(response_results) >= top_k:
                        break
            
            response = {
                "results": response_results,
                "method": "keyword",
                "total": len(response_results),
                "query": query,
            }
            
            return SearchResponse.from_model(response)
            
        except Exception as e:
            logger.error(f"Error in TF-IDF search: {e}")
            return SearchResponse.from_model({
                "results": [],
                "method": "keyword",
                "total": 0,
                "query": query,
                "error": str(e),
            })
    
    async def compare_methods(
        self,
        query: str,
        semantic_results: List[dict],
        top_k: int = 10,
    ) -> dict:
        """
        Compare TF-IDF baseline with semantic search results.
        
        Args:
            query: Query text
            semantic_results: Results from semantic search
            top_k: Number of results to compare
            
        Returns:
            Comparison metrics and results
        """
        # Get TF-IDF results
        tfidf_response = await self.search(query, top_k=top_k)
        tfidf_results = tfidf_response.results
        
        # Extract paper IDs for comparison
        semantic_ids = [r["paper"]["id"] for r in semantic_results[:top_k]]
        tfidf_ids = [r["paper"]["id"] for r in tfidf_results[:top_k]]
        
        # Calculate overlap
        overlap = set(semantic_ids) & set(tfidf_ids)
        
        return {
            "query": query,
            "semantic": {
                "method": "semantic",
                "total": len(semantic_results),
                "paper_ids": semantic_ids,
                "scores": [r["score"] for r in semantic_results[:top_k]],
            },
            "tfidf": {
                "method": "keyword",
                "total": len(tfidf_results),
                "paper_ids": tfidf_ids,
                "scores": [r["score"] for r in tfidf_results[:top_k]],
            },
            "comparison": {
                "overlap_at_k": len(overlap),
                "overlap_percentage": (len(overlap) / top_k) * 100 if top_k > 0 else 0,
                "only_in_semantic": list(set(semantic_ids) - set(tfidf_ids)),
                "only_in_tfidf": list(set(tfidf_ids) - set(semantic_ids)),
            },
        }
    
    async def refit(self) -> None:
        """Refit the TF-IDF model with current papers."""
        self._is_fitted = False
        await self.initialize()
    
    def is_fitted(self) -> bool:
        """Check if model is fitted."""
        return self._is_fitted
