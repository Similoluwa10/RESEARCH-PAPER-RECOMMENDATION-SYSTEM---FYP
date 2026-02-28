"""
Search Schemas

Pydantic models for search request/response validation.
"""

from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from src.schemas.paper import PaperResponse


class SearchMethod(str, Enum):
    """Available search methods."""
    
    SEMANTIC = "semantic"
    KEYWORD = "keyword"
    HYBRID = "hybrid"


class SearchFilters(BaseModel):
    """Optional filters for search."""
    
    year_min: Optional[int] = Field(None, ge=1900)
    year_max: Optional[int] = Field(None, le=2100)
    venues: Optional[List[str]] = None
    keywords: Optional[List[str]] = None


class SearchResult(BaseModel):
    """A single search result."""
    
    paper: PaperResponse
    score: float = Field(..., ge=0, le=1)
    highlights: Optional[Dict[str, List[str]]] = None


class SearchRequest(BaseModel):
    """Request schema for search."""
    
    query: str = Field(..., min_length=3)
    method: SearchMethod = Field(SearchMethod.SEMANTIC)
    top_k: int = Field(10, ge=1, le=50)
    filters: Optional[SearchFilters] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "deep learning code review",
                "method": "semantic",
                "top_k": 10,
            }
        }


class SearchResponse(BaseModel):
    """Response schema for search."""
    
    results: List[SearchResult]
    method: SearchMethod
    total: int
