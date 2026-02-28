"""
main.py - FastAPI Application Entry Point

This is the main entry point for the FastAPI backend application.
It creates the FastAPI app instance, configures middleware, and
registers all API routers.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import settings
from src.routers import auth, health, papers, recommendations, search


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    # Startup: Initialize database connections, load models, etc.
    print(f"Starting {settings.APP_NAME}...")
    yield
    # Shutdown: Clean up resources
    print(f"Shutting down {settings.APP_NAME}...")


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
