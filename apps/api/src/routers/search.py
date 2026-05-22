"""
search.py - Search Router

Provides semantic and keyword-based search endpoints.
Core functionality for the research paper discovery feature.
Includes baseline comparison endpoints for evaluation.
"""

from enum import Enum
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.dependencies import get_db
from src.schemas.search import SearchRequest, SearchResponse
from src.services.search_service import SearchService
from src.services.baseline_service import BaselineService

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


@router.post("/keyword", response_model=SearchResponse)
async def keyword_search(
    request: SearchRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Traditional keyword/TF-IDF search.
    
    Used as baseline for comparison with semantic search.
    Implements TF-IDF vectorization with cosine similarity.
    """
    service = SearchService(db)
    request.method = SearchMethod.KEYWORD
    results = await service.search(
        search_request=request
    )
    return results


@router.post("/compare")
async def compare_methods(
    request: SearchRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Compare semantic vs keyword search results.
    
    Executes both search methods and provides:
    - Side-by-side results
    - Overlap analysis
    - Method comparison metrics
    
    Useful for evaluation and benchmarking.
    """
    service = SearchService(db)
    
    # Get semantic results
    semantic_request = SearchRequest(**request.model_dump())
    semantic_request.method = SearchMethod.SEMANTIC
    semantic_results = await service.search(semantic_request)
    
    # Compare with baseline
    comparison = await service.baseline_service.compare_methods(
        query=request.query,
        semantic_results=semantic_results.results,
        top_k=request.top_k,
    )
    
    return comparison


@router.get("/baseline/status")
async def baseline_status(
    db: AsyncSession = Depends(get_db),
):
    """
    Check TF-IDF baseline status.
    
    Returns whether the baseline model is initialized and ready.
    """
    baseline = BaselineService(db)
    return {
        "status": "ready" if baseline.is_fitted() else "not_initialized",
        "method": "tfidf",
        "message": "TF-IDF baseline is ready for keyword search" if baseline.is_fitted() else "Initialize with first search"
    }


@router.post("/baseline/initialize")
async def initialize_baseline(
    db: AsyncSession = Depends(get_db),
):
    """
    Initialize/refit TF-IDF baseline model.
    
    Loads all papers from database and builds TF-IDF vectorizer.
    This is typically called on application startup.
    """
    baseline = BaselineService(db)
    await baseline.initialize()
    return {
        "status": "initialized",
        "method": "tfidf",
        "message": "TF-IDF baseline has been initialized"
    }
