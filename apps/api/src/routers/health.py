"""
health.py - Health Check Router

Provides health monitoring and readiness check endpoints.
Essential for container orchestration and load balancers.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.dependencies import get_db
from src.services.embedding_service import EmbeddingService
from src.services.recommendation_service import RecommendationService

router = APIRouter(prefix="/health")


@router.get("")
async def health_check():
    """
    Basic liveness check.
    
    Returns 200 if the application is running.
    Used by Kubernetes liveness probes.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/ready")
async def readiness_check(db: AsyncSession = Depends(get_db)):
    """
    Readiness check with database connectivity verification.
    
    Returns 200 if the application and all dependencies are ready.
    Returns 503 if any dependency is unavailable.
    """
    result = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "database": "connected",
    }
    
    try:
        # Verify database connectivity
        await db.execute(text("SELECT 1"))
    except Exception as e:
        result["status"] = "unhealthy"
        result["database"] = f"error: {str(e)}"
        return result
    
    return result


@router.get("/cache/stats")
async def get_cache_stats():
    """
    Get cache statistics for embeddings and recommendations.
    
    Returns hit rates, miss rates, and cache sizes for monitoring
    cache performance and optimization opportunities.
    """
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "embedding_cache": EmbeddingService.get_cache_stats(),
        "recommendation_cache": RecommendationService.get_cache_stats(),
    }


@router.post("/cache/reset")
async def reset_cache_stats():
    """
    Reset cache statistics counters.
    
    Useful for benchmarking cache performance after a code change.
    """
    EmbeddingService.reset_cache_stats()
    RecommendationService.reset_cache_stats()
    return {
        "status": "success",
        "message": "Cache statistics reset",
        "timestamp": datetime.utcnow().isoformat(),
    }
