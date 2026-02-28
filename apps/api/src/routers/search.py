"""
search.py - Search Router

Provides semantic and keyword-based search endpoints.
Core functionality for the research paper discovery feature.
"""

from enum import Enum
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.dependencies import get_db
from src.schemas.search import SearchRequest, SearchResponse
from src.services.search_service import SearchService

router = APIRouter(prefix="/search")


class SearchMethod(str, Enum):
    """Available search methods."""
    SEMANTIC = "semantic"
    KEYWORD = "keyword"
    HYBRID = "hybrid"


@router.post("", response_model=SearchResponse)
async def search(
    request: SearchRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Full search with configurable method.
    
    Supports semantic, keyword (TF-IDF), or hybrid search modes.
    Returns ranked results with relevance scores.
    """
    service = SearchService(db)
    results = await service.search(
        query=request.query,
        method=request.method,
        top_k=request.top_k,
        filters=request.filters,
    )
    return results


@router.get("/semantic", response_model=SearchResponse)
async def semantic_search(
    q: str = Query(..., min_length=3, description="Search query"),
    top_k: int = Query(10, ge=1, le=50, description="Number of results"),
    db: AsyncSession = Depends(get_db),
):
    """
    Quick semantic search via query parameters.
    
    Uses sentence-transformer embeddings and pgvector cosine similarity.
    """
    service = SearchService(db)
    results = await service.search(
        query=q,
        method=SearchMethod.SEMANTIC,
        top_k=top_k,
    )
    return results


@router.get("/keyword", response_model=SearchResponse)
async def keyword_search(
    q: str = Query(..., min_length=3, description="Search query"),
    top_k: int = Query(10, ge=1, le=50, description="Number of results"),
    db: AsyncSession = Depends(get_db),
):
    """
    Traditional keyword/TF-IDF search.
    
    Used as baseline for comparison with semantic search.
    """
    service = SearchService(db)
    results = await service.search(
        query=q,
        method=SearchMethod.KEYWORD,
        top_k=top_k,
    )
    return results
