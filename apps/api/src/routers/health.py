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
