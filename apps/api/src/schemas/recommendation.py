"""
Recommendation Schemas

Pydantic models for recommendation request/response validation.
"""

from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from src.schemas.paper import PaperResponse


class SimilarityBreakdown(BaseModel):
    """Breakdown of similarity scores."""
    
    semantic: float = Field(..., ge=0, le=1)
    keyword: float = Field(..., ge=0, le=1)
    overall: float = Field(..., ge=0, le=1)


class RecommendationExplanation(BaseModel):
    """Explanation for a recommendation."""
    
    summary: str
    key_terms: List[str]
    similarity_breakdown: SimilarityBreakdown


class RecommendationWithExplanation(BaseModel):
    """A single recommendation with explanation."""
    
    paper: PaperResponse
    score: float = Field(..., ge=0, le=1)
    explanation: Optional[RecommendationExplanation] = None


class RecommendationRequest(BaseModel):
    """Request schema for recommendations."""
    
    query_text: Optional[str] = Field(
        None,
        min_length=10,
        description="Text to find similar papers for",
    )
    paper_id: Optional[UUID] = Field(
        None,
        description="Paper ID to find similar papers for",
    )
    top_k: int = Field(10, ge=1, le=50)
    include_explanation: bool = Field(True)
    
    class Config:
        json_schema_extra = {
            "example": {
                "query_text": "machine learning approaches for software bug detection",
                "top_k": 10,
                "include_explanation": True,
            }
        }


class RecommendationResponse(BaseModel):
    """Response schema for recommendations."""
    
    recommendations: List[RecommendationWithExplanation]
    total: int
