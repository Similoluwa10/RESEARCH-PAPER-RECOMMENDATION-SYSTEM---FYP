"""
recommendation_service.py - Recommendation Service

Core business logic for generating paper recommendations.
Orchestrates embedding generation, similarity search, and explanations.
"""

from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.paper_repository import PaperRepository
from src.services.explanation_service import ExplanationService
from src.services.embedding_service import EmbeddingService


class RecommendationService:
    """
    Service for paper recommendations.
    
    Provides semantic similarity-based recommendations
    with optional explainability features.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = PaperRepository(db)
        self.explanation_service = ExplanationService()
        self.embedding_service = EmbeddingService()
    
    async def get_recommendations_for_text(
        self,
        text: str,
        top_k: int = 10,
        include_explanations: bool = True,
    ) -> Dict[str, Any]:
        """
        Get recommendations based on input text.
        
        Generates embedding for text and finds similar papers.
        
        Args:
            text: Query text to find similar papers for
            top_k: Number of recommendations to return
            include_explanations: Whether to generate XAI explanations
            
        Returns:
            Recommendations with scores and optional explanations
        """
        query_vector = self.embedding_service.encode_text(text)
        matches = await self.repository.search_by_embedding(query_vector, top_k=top_k)

        recommendations = []
        for item in matches:
            score = float(item["score"])
            recommendation = {
                "paper": item["paper"],
                "score": max(0.0, min(1.0, score)),
                "explanation": None,
            }
            recommendations.append(recommendation)
        
        return {
            "recommendations": recommendations,
            "method": "semantic",
            "query": text,
        }
    
    async def get_similar_papers(
        self,
        paper_id: UUID,
        top_k: int = 10,
        include_explanations: bool = True,
    ) -> Dict[str, Any]:
        """
        Find papers similar to a specific paper.
        
        Uses the paper's embedding to find semantically similar papers.
        
        Args:
            paper_id: ID of the paper to find similar papers for
            top_k: Number of results to return
            include_explanations: Whether to generate explanations
            
        Returns:
            Similar papers with similarity scores
        """
        # Get the source paper
        paper = await self.repository.get_by_id(paper_id)
        if not paper:
            return {"recommendations": [], "error": "Paper not found"}
        
        matches = await self.repository.find_similar(paper_id, top_k=top_k)
        recommendations = [
            {
                "paper": item["paper"],
                "score": item["score"],
                "explanation": None,
            }
            for item in matches
        ]
        
        return {
            "recommendations": recommendations,
            "source_paper_id": str(paper_id),
            "method": "paper_similarity",
        }
    
    async def get_personalized(
        self,
        user_id: UUID,
        top_k: int = 10,
    ) -> Dict[str, Any]:
        """
        Get personalized recommendations for a user.
        
        Based on user's interaction history (viewed, bookmarked papers).
        
        Args:
            user_id: ID of the user
            top_k: Number of recommendations
            
        Returns:
            Personalized paper recommendations
        """
        # TODO: Implement personalized recommendations
        # 1. Get user's interaction history
        # 2. Aggregate embeddings of interacted papers
        # 3. Find similar papers not yet seen
        
        return {
            "recommendations": [],
            "user_id": str(user_id),
            "method": "personalized",
        }
