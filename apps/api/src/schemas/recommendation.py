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
    # key_terms: List[str]
    # similarity_breakdown: SimilarityBreakdown

    @classmethod
    def from_model(cls, result: dict) -> "RecommendationExplanation":
        """Build explanation model from service-layer payload."""
        return cls(summary=result.get("summary", ""))


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
    include_explanation: bool = Field(True)
    
    class Config:
        json_schema_extra = {
            "example": {
                "query_text": "machine learning approaches for software bug detection",
                "include_explanation": True,
            }
        }


class RecommendationResponse(BaseModel):
    """Response schema for recommendations."""
    
    recommendations: List[RecommendationWithExplanation]
    total: int

    @classmethod
    def from_model(cls, result: dict) -> "RecommendationResponse":
        """Build response model from service-layer result payload."""
        recommendations = result.get("recommendations", [])
        return RecommendationResponse(
            recommendations=recommendations,
            total=len(recommendations),
        )
        

class PersonalizedRecommendationResponse(BaseModel):
    """Response schema for recommendations."""
    
    recommendations: List[RecommendationWithExplanation]
    total: int
    user_id: str

    @classmethod
    def from_model(cls, result: dict) -> "PersonalizedRecommendationResponse":
        """Build response model from service-layer result payload."""
        recommendations = result.get("recommendations", [])
        user_id = result.get("user_id", "no user found")
        return PersonalizedRecommendationResponse(
            recommendations=recommendations,
            total=len(recommendations),
            user_id=str(user_id),
        )