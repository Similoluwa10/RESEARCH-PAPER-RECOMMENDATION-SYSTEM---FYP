"""
recommendations.py - Recommendations Router

Provides paper recommendation endpoints with explainability features.
The core feature of the intelligent recommendation system.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.dependencies import get_current_user, get_db
from src.schemas.recommendation import (
    RecommendationRequest,
    RecommendationResponse,
)
from src.services.recommendation_service import RecommendationService

router = APIRouter(prefix="/recommendations")


@router.post("", response_model=RecommendationResponse)
async def get_recommendations(
    request: RecommendationRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Get paper recommendations from text or paper ID.
    
    Supports:
    - query_text: Find papers similar to input text
    - paper_id: Find papers similar to a specific paper
    
    Returns recommendations with explainability data.
    """
    service = RecommendationService(db)
    
    if request.paper_id:
        result = await service.get_similar_papers(
            paper_id=request.paper_id,
            top_k=request.top_k,
        )
    else:
        result = await service.get_recommendations_for_text(
            text=request.query_text,
            top_k=request.top_k,
        )
    
    recommendations = result.get("recommendations", [])
    return {
        "recommendations": recommendations,
        "total": len(recommendations),
    }


@router.get("/similar/{paper_id}", response_model=RecommendationResponse)
async def get_similar_papers(
    paper_id: UUID,
    top_k: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """
    Get papers similar to a specific paper.
    
    Uses semantic similarity based on paper embeddings.
    """
    service = RecommendationService(db)
    result = await service.get_similar_papers(paper_id, top_k=top_k)
    recommendations = result.get("recommendations", [])
    return {
        "recommendations": recommendations,
        "total": len(recommendations),
    }


@router.get("/personalized", response_model=RecommendationResponse)
async def get_personalized_recommendations(
    top_k: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Get personalized recommendations based on user history.
    
    Requires authentication. Uses user's interaction history
    to generate tailored recommendations.
    """
    service = RecommendationService(db)
    result = await service.get_personalized(
        user_id=current_user.id,
        top_k=top_k,
    )
    recommendations = result.get("recommendations", [])
    return {
        "recommendations": recommendations,
        "total": len(recommendations),
    }
