"""
recommendation_service.py - Recommendation Service

Core business logic for generating paper recommendations.
Orchestrates embedding generation, similarity search, and explanations.
"""

import time
from collections import OrderedDict
from threading import Lock
from typing import Any, Dict, List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.paper_repository import PaperRepository
from src.schemas.recommendation import RecommendationResponse
from src.services.explanation_service import ExplanationService
from src.services.embedding_service import EmbeddingService


class RecommendationService:
    """
    Service for paper recommendations.
    
    Provides semantic similarity-based recommendations
    with optional explainability features.
    """

    _result_cache: "OrderedDict[str, tuple[float, Dict[str, Any]]]" = OrderedDict()
    _result_cache_lock = Lock()
    _result_cache_ttl_seconds = 120
    _result_cache_max_items = 256
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = PaperRepository(db)
        self.explanation_service = ExplanationService()
        self.embedding_service = EmbeddingService()
        self.min_recommendation_similarity = 0.55

    @classmethod
    def _make_text_cache_key(cls, text: str, include_explanations: bool, min_similarity: float) -> str:
        normalized = " ".join((text or "").split()).lower()
        return f"text::{include_explanations}::{min_similarity:.4f}::{normalized}"

    @classmethod
    def _make_paper_cache_key(
        cls,
        paper_id: UUID,
        include_explanations: bool,
        min_similarity: float,
    ) -> str:
        return f"paper::{paper_id}::{include_explanations}::{min_similarity:.4f}"

    @classmethod
    def _get_cached_result(cls, key: str) -> Dict[str, Any] | None:
        now = time.monotonic()
        with cls._result_cache_lock:
            cached = cls._result_cache.get(key)
            if cached is None:
                return None

            created_at, payload = cached
            if now - created_at > cls._result_cache_ttl_seconds:
                cls._result_cache.pop(key, None)
                return None

            cls._result_cache.move_to_end(key)
            return payload

    @classmethod
    def _set_cached_result(cls, key: str, payload: Dict[str, Any]) -> None:
        now = time.monotonic()
        with cls._result_cache_lock:
            cls._result_cache[key] = (now, payload)
            cls._result_cache.move_to_end(key)

            while len(cls._result_cache) > cls._result_cache_max_items:
                cls._result_cache.popitem(last=False)
    
    async def get_recommendations_for_text(
        self,
        text: str,
        include_explanations: bool = True,
    ) -> RecommendationResponse:
        """
        Get recommendations based on input text.
        
        Generates embedding for text and finds similar papers.
        
        Args:
            text: Query text to find similar papers for
            include_explanations: Whether to generate XAI explanations
            
        Returns:
            Recommendations with scores and optional explanations
        """
        cache_key = self._make_text_cache_key(
            text=text,
            include_explanations=include_explanations,
            min_similarity=self.min_recommendation_similarity,
        )
        cached = self._get_cached_result(cache_key)
        if cached is not None:
            return RecommendationResponse.from_model(cached)

        query_vector = self.embedding_service.encode_text(text)
        matches = await self.repository.search_by_embedding(
            embedding=query_vector,
            top_k=None,
            min_similarity=self.min_recommendation_similarity,
        )

        recommendations = []
        for item in matches:
            score = float(item["score"])
            bounded_score = max(0.0, min(1.0, score))
            explanation = (
                self.explanation_service.generate_explanation(
                    query_text=text,
                    paper=item["paper"],
                    similarity_score=bounded_score,
                )
                if include_explanations
                else None
            )
            recommendation = {
                "paper": item["paper"],
                "score": bounded_score,
                "explanation": explanation,
            }
            recommendations.append(recommendation)
        
        result = {
            "recommendations": recommendations,
            "method": "semantic",
            "query": text,
        }
        self._set_cached_result(cache_key, result)
        return RecommendationResponse.from_model(result)
    
    async def get_similar_papers(
        self,
        paper_id: UUID,
        include_explanations: bool = True,
    ) -> RecommendationResponse:
        """
        Find papers similar to a specific paper.
        
        Uses the paper's embedding to find semantically similar papers.
        
        Args:
            paper_id: ID of the paper to find similar papers for
            include_explanations: Whether to generate explanations
            
        Returns:
            Similar papers with similarity scores
        """
        cache_key = self._make_paper_cache_key(
            paper_id=paper_id,
            include_explanations=include_explanations,
            min_similarity=self.min_recommendation_similarity,
        )
        cached = self._get_cached_result(cache_key)
        if cached is not None:
            return RecommendationResponse.from_model(cached)

        # Get the source paper
        paper = await self.repository.get_by_id(paper_id)
        if not paper:
            return RecommendationResponse.from_model({"recommendations": []})
        
        matches = await self.repository.find_similar(
            paper_id=paper_id,
            top_k=None,
            min_similarity=self.min_recommendation_similarity,
        )
        query_text = f"{paper.title} {paper.abstract}" if paper else ""
        recommendations = [
            {
                "paper": item["paper"],
                "score": item["score"],
                "explanation": (
                    self.explanation_service.generate_explanation(
                        query_text=query_text,
                        paper=item["paper"],
                        similarity_score=max(0.0, min(1.0, float(item["score"]))),
                    )
                    if include_explanations
                    else None
                ),
            }
            for item in matches
        ]
        
        result = {
            "recommendations": recommendations,
            "source_paper_id": str(paper_id),
            "method": "paper_similarity",
        }
        self._set_cached_result(cache_key, result)
        return RecommendationResponse.from_model(result)
    
    async def get_personalized(
        self,
        user_id: UUID,
    ) -> RecommendationResponse:
        """
        Get personalized recommendations for a user.
        
        Based on user's interaction history (viewed, bookmarked papers).
        
        Args:
            user_id: ID of the user
            
        Returns:
            Personalized paper recommendations
        """
        # TODO: Implement personalized recommendations
        # 1. Get user's interaction history
        # 2. Aggregate embeddings of interacted papers
        # 3. Find similar papers not yet seen
        
        result = {
            "recommendations": [],
            "user_id": str(user_id),
            "method": "personalized",
        }
        return RecommendationResponse.from_model(result)
