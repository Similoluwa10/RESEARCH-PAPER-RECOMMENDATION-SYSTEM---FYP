#!/usr/bin/env python
"""
fetch_papers.py - Paper Fetching Script

Main script to fetch research papers from multiple APIs and populate
the PostgreSQL database. This is used for initial database population.

Usage:
    python infrastructure/database/scripts/fetch_papers.py
    python infrastructure/database/scripts/fetch_papers.py --topics software_testing devops
    python infrastructure/database/scripts/fetch_papers.py --limit 50 --dry-run
"""

import argparse
import asyncio
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from dotenv import load_dotenv

# Add project paths for imports
project_root = Path(__file__).parent.parent.parent.parent

# Add data_ingestion package to path
sys.path.insert(0, str(project_root / "packages" / "data_ingestion"))

# Add apps/api to path and change to that context for proper relative imports
api_path = project_root / "apps" / "api"
sys.path.insert(0, str(api_path))
os.chdir(api_path)

from sqlalchemy import select, String, Text, Integer, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import DateTime, func
import uuid

from src.config import settings
from ingestion.clients import ArxivClient, DBLPClient, PaperData, SemanticScholarClient
from ingestion.processors import PaperCategorizer, PaperProcessor

# Change back to project root for relative paths
os.chdir(project_root)


# Database setup - create engine and session maker
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class Paper(Base):
    """Research paper entity for data ingestion."""
    
    __tablename__ = "papers"
    
    title: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    abstract: Mapped[str] = mapped_column(Text, nullable=False)
    authors: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    venue: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    keywords: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String), nullable=True)
    doi: Mapped[Optional[str]] = mapped_column(String(100), unique=True, nullable=True)
    url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler("fetch_papers.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


class PaperFetcher:
    """
    Orchestrates paper fetching from multiple APIs.
    
    Coordinates between API clients, processors,
    and the database layer.
    """
    
    def __init__(self, semantic_scholar_api_key: Optional[str] = None):
        """
        Initialize fetcher with API clients and processors.
        
        Args:
            semantic_scholar_api_key: Optional API key for Semantic Scholar
                                      (higher rate limits when provided)
        """
        logger.info("Initializing PaperFetcher...")
        
        # Initialize API clients
        self.arxiv = ArxivClient()
        self.semantic_scholar = SemanticScholarClient(api_key=semantic_scholar_api_key)
        self.dblp = DBLPClient()
        
        # Initialize processors
        self.processor = PaperProcessor()
        self.categorizer = PaperCategorizer()
        
        # Log API key status
        if semantic_scholar_api_key:
            logger.info("Semantic Scholar API key configured (higher rate limits)")
        else:
            logger.info("Using Semantic Scholar free tier (100 req/5 min)")
        
        logger.info("PaperFetcher initialized")
    
    def load_queries(self, query_file: Path) -> Dict[str, List[str]]:
        """
        Load search queries from YAML configuration file.
        
        Args:
            query_file: Path to queries.yaml
            
        Returns:
            Dict mapping topic names to lists of queries
        """
        logger.info(f"Loading queries from {query_file}")
        
        if not query_file.exists():
            logger.error(f"Query file not found: {query_file}")
            raise FileNotFoundError(f"Query file not found: {query_file}")
        
        with open(query_file, "r", encoding="utf-8") as f:
            queries = yaml.safe_load(f)
        
        logger.info(f"Loaded {len(queries)} topics")
        return queries
    
    def fetch_for_topic(
        self,
        topic: str,
        queries: List[str],
        papers_per_query: int = 100,
    ) -> Dict[str, Any]:
        """
        Fetch papers for a single topic using multiple queries and APIs.
        
        Args:
            topic: Topic name (e.g., "software_testing")
            queries: List of search queries for this topic
            papers_per_query: Target papers per query
            
        Returns:
            Dict with topic, papers list, and count
        """
        logger.info("=" * 60)
        logger.info(f"FETCHING: {topic}")
        logger.info("=" * 60)
        logger.info(f"Queries: {len(queries)}, Target per query: {papers_per_query}")
        
        all_papers: List[PaperData] = []
        papers_per_source = papers_per_query // 3
        
        for query in queries:
            logger.info(f"  Query: {query}")
            
            # Fetch from arXiv
            try:
                papers = self.arxiv.search(query, max_results=papers_per_source)
                all_papers.extend(papers)
            except Exception as e:
                logger.error(f"    arXiv error: {e}")
            
            # Fetch from Semantic Scholar
            try:
                papers = self.semantic_scholar.search(query, max_results=papers_per_source)
                all_papers.extend(papers)
            except Exception as e:
                logger.error(f"    Semantic Scholar error: {e}")
            
            # Fetch from DBLP
            try:
                papers = self.dblp.search(query, max_results=papers_per_source)
                all_papers.extend(papers)
            except Exception as e:
                logger.error(f"    DBLP error: {e}")
        
        logger.info(f"  Total before processing: {len(all_papers)}")
        
        # Process papers (clean and deduplicate)
        processed = self.processor.process_papers(all_papers)
        logger.info(f"  Total after processing: {len(processed)}")
        
        return {
            "topic": topic,
            "papers": processed,
            "count": len(processed),
        }
    
    async def save_to_database(
        self,
        topic_results: List[Dict[str, Any]],
        dry_run: bool = False,
    ) -> int:
        """
        Save processed papers to the database.
        
        Args:
            topic_results: List of topic result dicts
            dry_run: If True, don't actually save (just report)
            
        Returns:
            Total number of papers inserted
        """
        logger.info("=" * 60)
        logger.info(f"SAVING TO DATABASE {'(DRY RUN)' if dry_run else ''}")
        logger.info("=" * 60)
        
        total_inserted = 0
        
        async with async_session_maker() as session:
            for result in topic_results:
                topic = result["topic"]
                papers = result["papers"]
                
                logger.info(f"  Topic: {topic}")
                logger.info(f"  Papers to insert: {len(papers)}")
                
                inserted, skipped, errors = await self._insert_papers(
                    session,
                    papers,
                    topic,
                    dry_run,
                )
                
                total_inserted += inserted
                
                logger.info(f"    Inserted: {inserted}")
                logger.info(f"    Skipped (duplicates): {skipped}")
                logger.info(f"    Errors: {errors}")
        
        return total_inserted
    
    async def _insert_papers(
        self,
        session: AsyncSession,
        papers: List[PaperData],
        topic: str,
        dry_run: bool,
    ) -> tuple:
        """Insert papers into database."""
        inserted = 0
        skipped = 0
        errors = 0
        
        for paper in papers:
            try:
                # Check for existing paper by DOI
                existing = None
                if paper.doi:
                    result = await session.execute(
                        select(Paper).where(Paper.doi == paper.doi)
                    )
                    existing = result.scalar_one_or_none()
                
                # Check by similar title if no DOI match
                if not existing:
                    title_prefix = paper.title[:100]
                    result = await session.execute(
                        select(Paper).where(Paper.title.ilike(f"{title_prefix}%"))
                    )
                    existing = result.scalar_one_or_none()
                
                if existing:
                    skipped += 1
                    continue
                
                if not dry_run:
                    # Categorize the paper
                    category = self.categorizer.categorize(paper)
                    
                    # Create paper record
                    db_paper = Paper(
                        title=paper.title,
                        abstract=paper.abstract,
                        authors=paper.authors,
                        year=paper.year or datetime.now().year,
                        venue=paper.venue or topic,
                        doi=paper.doi,
                        url=paper.url,
                    )
                    session.add(db_paper)
                    
                    # Commit periodically
                    if inserted % 50 == 0:
                        await session.commit()
                
                inserted += 1
                
            except Exception as e:
                logger.debug(f"Error inserting paper: {e}")
                errors += 1
                if not dry_run:
                    await session.rollback()
        
        # Final commit
        if not dry_run:
            try:
                await session.commit()
            except Exception as e:
                logger.error(f"Final commit error: {e}")
                await session.rollback()
        
        return inserted, skipped, errors


async def main() -> None:
    """Main entry point for paper fetching."""
    parser = argparse.ArgumentParser(
        description="Fetch research papers from APIs and populate database"
    )
    
    parser.add_argument(
        "--query-file",
        default="infrastructure/database/seeds/queries.yaml",
        help="Path to queries YAML file",
    )
    parser.add_argument(
        "--topics",
        nargs="+",
        help="Specific topics to fetch (e.g., software_testing devops)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=100,
        help="Papers per topic query (default: 100)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run without saving to database",
    )
    
    args = parser.parse_args()
    
    # Load environment variables from .env file
    env_file = project_root / "apps" / "api" / ".env"
    if env_file.exists():
        load_dotenv(env_file)
        logger.info(f"Loaded environment from {env_file}")
    
    # Get Semantic Scholar API key (optional)
    semantic_scholar_api_key = os.getenv("SEMANTIC_SCHOLAR_API_KEY")
    
    # Resolve query file path
    query_file = Path(args.query_file)
    if not query_file.is_absolute():
        query_file = project_root / query_file
    
    # Initialize fetcher with API key
    fetcher = PaperFetcher(semantic_scholar_api_key=semantic_scholar_api_key)
    
    # Load queries
    all_queries = fetcher.load_queries(query_file)
    
    # Filter topics if specified
    if args.topics:
        queries = {k: v for k, v in all_queries.items() if k in args.topics}
        logger.info(f"Filtered to {len(queries)} specific topics: {args.topics}")
    else:
        queries = all_queries
    
    logger.info(f"Selected {len(queries)} topics for fetching")
    
    # Ensure database tables exist
    logger.info("Ensuring database tables exist...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Phase 1: Fetch papers from APIs
    logger.info("\n" + "=" * 60)
    logger.info("PHASE 1: FETCHING PAPERS FROM APIs")
    logger.info("=" * 60)
    
    topic_results = []
    for topic, topic_queries in queries.items():
        result = fetcher.fetch_for_topic(
            topic,
            topic_queries,
            papers_per_query=args.limit,
        )
        topic_results.append(result)
    
    # Phase 2: Save to database
    logger.info("\n" + "=" * 60)
    logger.info("PHASE 2: SAVING TO DATABASE")
    logger.info("=" * 60)
    
    total = await fetcher.save_to_database(topic_results, dry_run=args.dry_run)
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info(f"COMPLETE {'(DRY RUN)' if args.dry_run else ''}")
    logger.info("=" * 60)
    
    total_fetched = sum(r["count"] for r in topic_results)
    logger.info(f"Total papers fetched: {total_fetched}")
    logger.info(f"Total papers inserted: {total}")
    
    if not args.dry_run:
        logger.info("\nPapers by topic:")
        for result in topic_results:
            logger.info(f"  - {result['topic']}: {result['count']} papers")
    
    logger.info("\nDone!")


if __name__ == "__main__":
    asyncio.run(main())
