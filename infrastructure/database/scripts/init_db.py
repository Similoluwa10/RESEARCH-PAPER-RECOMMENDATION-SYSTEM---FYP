"""
Initialize Database

Creates all tables and enables pgvector extension.
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'apps', 'api'))

from sqlalchemy import text
from src.models.base import engine, Base
from src.models import Paper, User, Interaction, Embedding


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
