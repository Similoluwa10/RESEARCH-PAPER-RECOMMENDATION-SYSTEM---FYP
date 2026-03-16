"""
Search Schemas

Pydantic models for search request/response validation.
"""

from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from src.schemas.paper import PaperResponse

from src.core.enums import SearchMethod


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
    
    @classmethod
    def from_model(cls, result: dict) -> "SearchResult":
        """Build search result model from service-layer payload."""
        if isinstance(result, SearchResult):
            return result
        return cls(
            paper=result.get("paper"),
            score=float(result.get("score", 0)),
            highlights=result.get("highlights"),
        )


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
    query: Optional[str] = None

    @classmethod
    def from_model(cls, result: dict) -> "SearchResponse":
        """Build response model from service-layer result payload."""
        results = result.get("results", [])
        method = result.get("method", SearchMethod.SEMANTIC)
        
        if isinstance(method, str):
            method = SearchMethod(method)
            
        return cls(
            results=[SearchResult.from_model(r) for r in results],
            method=method,
            total=result.get("total", len(results)),
            query=result.get("query"),
        )
