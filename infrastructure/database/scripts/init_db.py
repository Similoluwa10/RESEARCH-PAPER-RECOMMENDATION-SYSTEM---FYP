"""
Initialize Database

Creates all tables and enables pgvector extension.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the apps/api directory to Python path
PROJECT_ROOT = Path(__file__).resolve().parents[3]
API_PATH = PROJECT_ROOT / "apps" / "api"
sys.path.insert(0, str(API_PATH))

from sqlalchemy import text
from src.models.base import engine, Base
from src.models import Paper, User, Interaction, Embedding, Explanation, Recommendation


async def init_db():
    """Initialize the database."""
    async with engine.begin() as conn:
        # Enable pgvector extension
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        print("✓ pgvector extension enabled")
        
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
        print("✓ All tables created")
    
    print("\nDatabase initialization complete!")


if __name__ == "__main__":
    asyncio.run(init_db())
