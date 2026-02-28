"""
Pydantic Schemas Package

Request/Response schemas for API validation.
"""

from src.schemas.paper import PaperCreate, PaperResponse, PaperUpdate, PaperList
from src.schemas.user import UserCreate, UserResponse, Token
from src.schemas.recommendation import (
    RecommendationRequest,
    RecommendationResponse,
    RecommendationWithExplanation,
)
from src.schemas.search import SearchRequest, SearchResponse, SearchMethod

__all__ = [
    "PaperCreate",
    "PaperResponse",
    "PaperUpdate",
    "PaperList",
    "UserCreate",
    "UserResponse",
    "Token",
    "RecommendationRequest",
    "RecommendationResponse",
    "RecommendationWithExplanation",
    "SearchRequest",
    "SearchResponse",
    "SearchMethod",
]
