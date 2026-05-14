"""
Script to get paper statistics from the database.
Displays categories and source counts.
"""

import asyncio
import sys
import os
from collections import defaultdict

# Add apps/api to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'apps', 'api'))

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.base import engine
from src.models.paper import Paper


async def get_paper_stats():
    """Fetch and display paper statistics."""
    
    async with AsyncSession(engine) as session:
        # Get count by category
        print("\n" + "="*70)
        print("PAPER CATEGORIES DISTRIBUTION")
        print("="*70)
        
        category_query = select(
            Paper.category,
            func.count(Paper.id).label('count')
        ).group_by(Paper.category).order_by(func.count(Paper.id).desc())
        
        result = await session.execute(category_query)
        categories = result.fetchall()
        
        if categories:
            print(f"\n{'Category':<40} {'Count':>10}")
            print("-" * 52)
            total_papers = 0
            for category, count in categories:
                print(f"{category:<40} {count:>10}")
                total_papers += count
            print("-" * 52)
            print(f"{'TOTAL':<40} {total_papers:>10}\n")
        else:
            print("\nNo papers found in database.\n")
        
        # Get count by source
        print("="*70)
        print("PAPERS BY SOURCE (CLIENT)")
        print("="*70)
        
        source_query = select(
            Paper.source,
            func.count(Paper.id).label('count')
        ).group_by(Paper.source).order_by(func.count(Paper.id).desc())
        
        result = await session.execute(source_query)
        sources = result.fetchall()
        
        if sources:
            print(f"\n{'Source':<40} {'Count':>10}")
            print("-" * 52)
            total_papers = 0
            for source, count in sources:
                print(f"{source:<40} {count:>10}")
                total_papers += count
            print("-" * 52)
            print(f"{'TOTAL':<40} {total_papers:>10}\n")
        else:
            print("\nNo papers found in database.\n")
        
        print("="*70 + "\n")


async def main():
    try:
        await get_paper_stats()
    except Exception as e:
        print(f"\n❌ Error: {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
