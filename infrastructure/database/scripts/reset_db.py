"""
Reset Database

Drops all tables and recreates them. USE WITH CAUTION.
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'apps', 'api'))

from sqlalchemy import text
from src.models.base import engine, Base
from src.models import Paper, User, Interaction, Embedding


async def reset_db():
    """Reset the database - drops and recreates all tables."""
    confirm = input("This will DELETE ALL DATA. Type 'CONFIRM' to proceed: ")
    
    if confirm != "CONFIRM":
        print("Aborted.")
        return
    
    async with engine.begin() as conn:
        # Drop all tables
        await conn.run_sync(Base.metadata.drop_all)
        print("✓ All tables dropped")
        
        # Enable pgvector extension
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        print("✓ pgvector extension enabled")
        
        # Recreate all tables
        await conn.run_sync(Base.metadata.create_all)
        print("✓ All tables recreated")
    
    print("\nDatabase reset complete!")


if __name__ == "__main__":
    asyncio.run(reset_db())
