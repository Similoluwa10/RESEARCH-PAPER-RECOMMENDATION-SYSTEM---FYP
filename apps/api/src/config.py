"""
config.py - Application Configuration

Centralized configuration management using pydantic-settings.
Loads settings from environment variables and .env files.
"""

import json
from functools import lru_cache
from pathlib import Path
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parents[3]

ROOT_ENV_FILE = ROOT_DIR / ".env"

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=ROOT_ENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore extra fields in .env
    )
    
    
    # Application
    APP_NAME: str = "Research Paper Recommender API"
    APP_ENV: str = "development"
    DEBUG: bool 
    API_V1_PREFIX: str 
    
    # Database
    DATABASE_URL: str
    DB_POOL_SIZE: int 
    DB_MAX_OVERFLOW: int
    
    # Redis (optional - for caching)
    REDIS_URL: str = ""
    
    # JWT Authentication
    JWT_SECRET_KEY: str 
    JWT_ALGORITHM: str 
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int 
    GOOGLE_CLIENT_ID: str = ""
    
    # CORS
    # Accepts a JSON list ('["https://a.app","https://b.app"]') or a
    # comma-separated string ("https://a.app,https://b.app").
    CORS_ORIGINS: str = ""
    # Optional regex for extra origins, e.g. Vercel preview deployments:
    # r"https://.*\.vercel\.app"
    CORS_ORIGIN_REGEX: str = ""

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS_ORIGINS into a clean list (no quotes, spaces or trailing slashes)."""
        raw = (self.CORS_ORIGINS or "").strip()
        if not raw:
            return []
        items: List[str]
        if raw.startswith("["):
            try:
                items = [str(x) for x in json.loads(raw)]
            except json.JSONDecodeError:
                items = raw.strip("[]").split(",")
        else:
            items = raw.split(",")
        cleaned = []
        for item in items:
            origin = item.strip().strip("'\"").strip().rstrip("/")
            if origin:
                cleaned.append(origin)
        return cleaned
    
    # NLP/Embeddings
    EMBEDDING_MODEL_NAME: str 
    EMBEDDING_DIMENSION: int
    # "auto" (ONNX/fastembed if installed, else sentence-transformers), "onnx" or "torch"
    EMBEDDING_BACKEND: str = "auto"
    # Load the embedding model during startup (set False on very small instances
    # to load it on the first request instead)
    PREWARM_EMBEDDING_MODEL: bool = True
    # Fit the TF-IDF keyword-search index during startup (memory heavy; off by default)
    PREWARM_TFIDF_BASELINE: bool = False

    # Caching Configuration
    EMBEDDING_CACHE_TTL_SECONDS: int
    EMBEDDING_CACHE_MAX_ITEMS: int 
    RECOMMENDATION_CACHE_TTL_SECONDS: int 
    RECOMMENDATION_CACHE_MAX_ITEMS: int 
    
    # Concurrency Configuration for Explanation Generation
    MAX_CONCURRENT_EXPLANATIONS: int = 5  # Max concurrent LLM calls for explanations
    
    # Query Optimization
    EMBEDDING_BATCH_SIZE: int
    
    # Logging
    LOG_LEVEL: str
    
    SEMANTIC_SCHOLAR_API_KEY: str = ""
    
    # Hugging Face API (for higher rate limits on model downloads and inference)
    HUGGINGFACE_API_KEY: str = ""
    
    # LangChain Configuration for Explainability
    LANGCHAIN_PROVIDER: str = "groq"  # "openai", "ollama", "anthropic", or "groq"
    LANGCHAIN_CHAT_MODEL: str = "gpt-3.5-turbo"  # For OpenAI provider
    LANGCHAIN_TEMPERATURE: float = 0.3  # Lower for consistency
    
    # Provider-specific API keys/configurations
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "openai/gpt-oss-20b"  # Groq model
    #OLLAMA_BASE_URL: str = "http://localhost:11434"  # Default Ollama endpoint
    #OLLAMA_MODEL: str = "mistral"  # Default Ollama model 


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance (singleton pattern)."""
    return Settings()


# Global settings instance
settings = get_settings()
