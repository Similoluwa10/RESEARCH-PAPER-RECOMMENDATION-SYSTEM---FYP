"""
baseline_service.py - Baseline Service

TF-IDF baseline service for comparing against semantic search.
Used for evaluation and performance benchmarking.
"""

import asyncio
import logging
import sys
import os
from typing import List, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.memory import release_memory
from src.models.paper import Paper
from src.repositories.paper_repository import PaperRepository
from src.schemas.search import SearchResponse

# Make packages/ importable; TFIDFBaseline (scikit-learn) is imported lazily
_PACKAGES_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'packages')
)
if _PACKAGES_DIR not in sys.path:
    sys.path.insert(0, _PACKAGES_DIR)

logger = logging.getLogger(__name__)


# Only the columns needed to build TF-IDF documents. After fitting, just the
# paper ids are kept in memory; result details are fetched from the database.
_CORPUS_COLUMNS = (Paper.id, Paper.title, Paper.abstract, Paper.keywords)


class BaselineService:
    """
    Service for baseline search methods.

    Provides TF-IDF based search for comparison with semantic methods.
    Used for evaluation and benchmarking.

    The fitted TF-IDF index is shared by all instances (one per process), so it
    is built once on first use instead of on every request.
    """

    _shared_model = None
    _shared_paper_ids: list = []
    _shared_fitted: bool = False
    _fit_lock: "asyncio.Lock | None" = None

    def __init__(self, db: AsyncSession):
        """Initialize baseline service."""
        self.db = db
        self.repository = PaperRepository(db)

    @property
    def tfidf_model(self):
        return BaselineService._shared_model

    @property
    def _corpus_paper_ids(self) -> list:
        return BaselineService._shared_paper_ids

    @property
    def _is_fitted(self) -> bool:
        return BaselineService._shared_fitted

    @classmethod
    def _get_lock(cls) -> asyncio.Lock:
        if cls._fit_lock is None:
            cls._fit_lock = asyncio.Lock()
        return cls._fit_lock

    async def initialize(self, force: bool = False) -> None:
        """
        Initialize and fit the TF-IDF model on all papers.

        Runs once per process (or again when force=True / refit()).
        """
        async with self._get_lock():
            if BaselineService._shared_fitted and not force:
                return
            await self._fit()

    async def _fit(self) -> None:
        cls = BaselineService
        try:
            logger.info("Initializing TF-IDF baseline...")
            from nlp.src.baselines.tfidf import TFIDFBaseline

            result = await self.db.execute(
                select(*_CORPUS_COLUMNS).order_by(Paper.created_at.desc()).limit(100000)
            )
            papers = result.all()

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
            paper_ids = [paper.id for paper in papers]
            del papers

            # Initialize and fit TF-IDF
            model = TFIDFBaseline(
                max_features=10000,
                ngram_range=(1, 2),
                min_df=2,
                max_df=0.95,
            )
            # Chunked fit: same index as model.fit() with a fraction of the
            # peak memory (a plain fit needs 500 MB+ on ~18k papers)
            model.fit_low_memory(documents)
            del documents

            # Drop the large fitted vocabulary of discarded terms
            if hasattr(model.vectorizer, "stop_words_"):
                model.vectorizer.stop_words_ = None

            cls._shared_model = model
            cls._shared_paper_ids = paper_ids
            cls._shared_fitted = True
            release_memory()

            logger.info(f"TF-IDF baseline initialized with {len(paper_ids)} papers")

        except Exception as e:
            logger.error(f"Error initializing TF-IDF baseline: {e}")
            cls._shared_fitted = False
    
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

            # Fetch details for the matched papers only
            paper_ids = self._corpus_paper_ids
            matched_ids = [paper_ids[idx] for idx, _ in results if idx < len(paper_ids)]
            papers_by_id = {}
            if matched_ids:
                rows = await self.db.execute(select(Paper).where(Paper.id.in_(matched_ids)))
                papers_by_id = {paper.id: paper for paper in rows.scalars().all()}
            
            # Build response with paper details
            response_results = []
            for idx, score in results:
                if idx < len(paper_ids) and paper_ids[idx] in papers_by_id:
                    paper = papers_by_id[paper_ids[idx]]
                    
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
        await self.initialize(force=True)
    
    def is_fitted(self) -> bool:
        """Check if model is fitted."""
        return self._is_fitted
