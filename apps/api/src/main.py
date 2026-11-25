"""
main.py - FastAPI Application Entry Point

This is the main entry point for the FastAPI backend application.
It creates the FastAPI app instance, configures middleware, and
registers all API routers.
"""

import sys
import os
import logging
from contextlib import asynccontextmanager

# Add packages directory to path for nlp module access
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'packages'))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import settings
from src.core.memory import release_memory
from src.routers import auth, health, papers, recommendations, search
from src.services.embedding_service import EmbeddingService
from src.services.baseline_service import BaselineService
from src.models.base import engine
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    # Startup: Initialize database connections, load models, etc.
    logger.info(f"Starting {settings.APP_NAME}...")
    
    # Pre-warm embedding model to avoid slowness on first request
    if settings.PREWARM_EMBEDDING_MODEL:
        logger.info("Pre-warming embedding model...")
        try:
            embedding_service = EmbeddingService()
            # Force model loading with a dummy encode
            embedding_service.encode_text("Warm up embedding model")
            logger.info("✓ Embedding model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to pre-warm embedding model: {e}")
    else:
        logger.info("Embedding model will be loaded on first request")

    # TF-IDF keyword index: built lazily on the first keyword search unless
    # explicitly enabled, since it holds the whole paper corpus in memory.
    if settings.PREWARM_TFIDF_BASELINE:
        logger.info("Initializing TF-IDF baseline model...")
        try:
            async with AsyncSession(engine) as session:
                baseline = BaselineService(session)
                await baseline.initialize()
                logger.info("✓ TF-IDF baseline model initialized successfully")
        except Exception as e:
            logger.warning(f"TF-IDF baseline initialization deferred: {e}")
    else:
        logger.info("TF-IDF baseline will be initialized on first keyword search")

    release_memory()
    yield
    # Shutdown: Clean up resources
    logger.info(f"Shutting down {settings.APP_NAME}...")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="Intelligent and Explainable Semantic Research Paper Recommendation System for Software Engineering",
    version="1.0.0",
    lifespan=lifespan,
    docs_url=f"{settings.API_V1_PREFIX}/docs",
    redoc_url=f"{settings.API_V1_PREFIX}/redoc",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(health.router, prefix=settings.API_V1_PREFIX, tags=["Health"])
app.include_router(auth.router, prefix=settings.API_V1_PREFIX, tags=["Authentication"])
app.include_router(papers.router, prefix=settings.API_V1_PREFIX, tags=["Papers"])
app.include_router(search.router, prefix=settings.API_V1_PREFIX, tags=["Search"])
app.include_router(recommendations.router, prefix=settings.API_V1_PREFIX, tags=["Recommendations"])


@app.get("/")
async def root():
    """Root endpoint - API status."""
    return {
        "name": settings.APP_NAME,
        "status": "running",
        "version": "1.0.0",
        "docs": f"{settings.API_V1_PREFIX}/docs",
    }
