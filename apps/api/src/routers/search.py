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

from src.core.enums import SearchMethod

router = APIRouter(prefix="/search")


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
        search_request=request,
    )
    return results


@router.post("/semantic", response_model=SearchResponse)
async def semantic_search(
    request: SearchRequest, 
    db: AsyncSession = Depends(get_db),
):
    """
    Quick semantic search via query parameters.
    
    Uses sentence-transformer embeddings and pgvector cosine similarity.
    """
    service = SearchService(db)
    results = await service.search(
        search_request=request
    )
    return results

#TODO: fix keyword search, endpoint request and response format
# @router.post("/keyword", response_model=SearchResponse)
# async def keyword_search(
#     request: SearchRequest,
#     db: AsyncSession = Depends(get_db),
# ):
#     """
#     Traditional keyword/TF-IDF search.
    
#     Used as baseline for comparison with semantic search.
#     """
#     service = SearchService(db)
#     results = await service.search(
#         search_request=request
#     )
#     return results
