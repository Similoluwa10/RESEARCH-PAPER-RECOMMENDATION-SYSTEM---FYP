"""
config.py - Application Configuration

Centralized configuration management using pydantic-settings.
Loads settings from environment variables and .env files.
"""

from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parents[3]

ROOT_ENV_FILE = ROOT_DIR / "apps" / "api" / ".env"

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
    GOOGLE_CLIENT_ID: str 
    
    # CORS
    CORS_ORIGINS: List[str] 
    
    # NLP/Embeddings
    EMBEDDING_MODEL_NAME: str 
    EMBEDDING_DIMENSION: int 
    
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
    HUGGINGFACE_API_KEY: str 
    
    # LangChain Configuration for Explainability
    LANGCHAIN_PROVIDER: str  # "openai", "ollama", "anthropic", or "groq"
    LANGCHAIN_CHAT_MODEL: str # For OpenAI provider
    LANGCHAIN_TEMPERATURE: float # Lower for consistency
    
    # Provider-specific API keys/configurations
    OPENAI_API_KEY: str 
    ANTHROPIC_API_KEY: str
    GROQ_API_KEY: str
    GROQ_MODEL: str  # Groq model
    OLLAMA_BASE_URL: str # Default Ollama endpoint
    OLLAMA_MODEL: str  # Default Ollama model 


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance (singleton pattern)."""
    return Settings()


# Global settings instance
settings = get_settings()
