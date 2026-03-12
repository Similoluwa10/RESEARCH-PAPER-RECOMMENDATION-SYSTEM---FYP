#!/usr/bin/env python
"""
fetch_papers.py - Paper Fetching Script

Main script to fetch research papers from multiple APIs and populate
the PostgreSQL database. This is used for initial database population.

Usage:
    python infrastructure/database/scripts/fetch_papers.py
    python infrastructure/database/scripts/fetch_papers.py --topics software_testing devops
    python infrastructure/database/scripts/fetch_papers.py --limit 50 --dry-run
    python infrastructure/database/scripts/fetch_papers.py --limit 100 --batch-size 3
    python infrastructure/database/scripts/fetch_papers.py --start-batch 3  # resume from batch 3
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

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from src.config import settings
from src.models.base import Base
from src.models.paper import Paper
from ingestion.clients import ArxivClient, DBLPClient, PaperData, SemanticScholarClient, ZenodoClient, DOAJClient
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler("fetch_papers.log", mode="w"),
        logging.StreamHandler(sys.stdout),
    ],
)
# Force flush after every log line so terminal shows real-time progress
for handler in logging.getLogger().handlers:
    if isinstance(handler, logging.StreamHandler):
        handler.flush = lambda h=handler: (h.stream.flush(),)
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
        self.zenodo = ZenodoClient()
        self.doaj = DOAJClient()
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
        sources: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Fetch papers for a single topic using multiple queries and APIs.
        
        Fetches from each API client separately (all queries per client)
        to respect rate limits and avoid context-switching between APIs.
        
        Args:
            topic: Topic name (e.g., "software_testing")
            queries: List of search queries for this topic
            papers_per_query: Target papers per query per source
            sources: List of sources to fetch from (default: all)
            
        Returns:
            Dict with topic, papers list, and count
        """
        if sources is None:
            sources = ["arxiv", "zenodo", "doaj", "semantic_scholar", "dblp"]
        
        logger.info("=" * 60)
        logger.info(f"FETCHING: {topic}")
        logger.info("=" * 60)
        logger.info(f"Queries: {len(queries)}, Target per query per source: {papers_per_query}")
        logger.info(f"Sources: {', '.join(sources)}")
        
        all_papers: List[PaperData] = []
        
        # --- arXiv (all queries) ---
        if "arxiv" in sources:
            logger.info(f"\n  [arXiv] Fetching {len(queries)} queries...")
            arxiv_count = 0
            for i, query in enumerate(queries, 1):
                logger.info(f"    [{i}/{len(queries)}] arXiv: '{query}'")
                try:
                    papers = self.arxiv.search(query, max_results=papers_per_query)
                    all_papers.extend(papers)
                    arxiv_count += len(papers)
                except Exception as e:
                    logger.error(f"      arXiv error: {e}")
            logger.info(f"  [arXiv] Total: {arxiv_count} papers")
        
        # --- Zenodo (all queries) ---
        if "zenodo" in sources:
            logger.info(f"\n  [Zenodo] Fetching {len(queries)} queries...")
            zenodo_count = 0
            for i, query in enumerate(queries, 1):
                logger.info(f"    [{i}/{len(queries)}] Zenodo: '{query}'")
                try:
                    papers = self.zenodo.search(query, max_results=papers_per_query)
                    all_papers.extend(papers)
                    zenodo_count += len(papers)
                except Exception as e:
                    logger.error(f"      Zenodo error: {e}")
            logger.info(f"  [Zenodo] Total: {zenodo_count} papers")
        
        # --- DOAJ (all queries) ---
        if "doaj" in sources:
            logger.info(f"\n  [DOAJ] Fetching {len(queries)} queries...")
            doaj_count = 0
            for i, query in enumerate(queries, 1):
                logger.info(f"    [{i}/{len(queries)}] DOAJ: '{query}'")
                try:
                    papers = self.doaj.search(query, max_results=papers_per_query)
                    all_papers.extend(papers)
                    doaj_count += len(papers)
                except Exception as e:
                    logger.error(f"      DOAJ error: {e}")
            logger.info(f"  [DOAJ] Total: {doaj_count} papers")
        
        # --- Semantic Scholar (all queries) ---
        if "semantic_scholar" in sources:
            logger.info(f"\n  [Semantic Scholar] Fetching {len(queries)} queries...")
            ss_count = 0
            for i, query in enumerate(queries, 1):
                logger.info(f"    [{i}/{len(queries)}] Semantic Scholar: '{query}'")
                try:
                    papers = self.semantic_scholar.search(query, max_results=papers_per_query)
                    all_papers.extend(papers)
                    ss_count += len(papers)
                except Exception as e:
                    logger.error(f"      Semantic Scholar error: {e}")
            logger.info(f"  [Semantic Scholar] Total: {ss_count} papers")
        
        # --- DBLP (all queries) ---
        # Note: DBLP doesn't provide abstracts, so most papers will be
        # filtered during validation (abstract is required for NLP).
        if "dblp" in sources:
            logger.info(f"\n  [DBLP] Fetching {len(queries)} queries...")
            dblp_count = 0
            for i, query in enumerate(queries, 1):
                logger.info(f"    [{i}/{len(queries)}] DBLP: '{query}'")
                try:
                    papers = self.dblp.search(query, max_results=papers_per_query)
                    all_papers.extend(papers)
                    dblp_count += len(papers)
                except Exception as e:
                    logger.error(f"      DBLP error: {e}")
            logger.info(f"  [DBLP] Total: {dblp_count} papers")
        
        logger.info(f"\n  Total raw papers: {len(all_papers)}")
        
        # Process papers (clean and deduplicate)
        processed = self.processor.process_papers(all_papers)
        logger.info(f"  After processing: {len(processed)} papers")
        
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
            dry_run: If True, don't actually save to database
            
        Returns:
            Total number of papers inserted
        """
        async with async_session_maker() as session:
            total_inserted = 0
            
            for result in topic_results:
                topic = result["topic"]
                papers = result["papers"]
                
                logger.info(f"  Topic: {topic}")
                logger.info(f"  Papers to insert: {len(papers)}")
                
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
                            
                            # Create paper record with all required fields
                            db_paper = Paper(
                                title=paper.title,
                                abstract=paper.abstract,
                                authors=paper.authors,
                                category=category,
                                source=paper.source,
                                year=paper.year,
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
                
                logger.info(f"    Inserted: {inserted}")
                logger.info(f"    Skipped (duplicates): {skipped}")
                logger.info(f"    Errors: {errors}")
                
                total_inserted += inserted
            
            return total_inserted


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
    parser.add_argument(
        "--batch-size",
        type=int,
        default=3,
        help="Number of topics per batch (default: 3, ~1000 papers/batch)",
    )
    parser.add_argument(
        "--start-batch",
        type=int,
        default=1,
        help="Batch number to start from (1-indexed, for resuming)",
    )
    parser.add_argument(
        "--sources",
        nargs="+",
        choices=["arxiv", "zenodo", "doaj", "semantic_scholar", "dblp"],
        default=None,
        help="Which API sources to fetch from (default: all). e.g. --sources arxiv zenodo doaj semantic_scholar",
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
    
    # Split topics into batches
    topic_list = list(queries.items())
    batch_size = args.batch_size
    total_batches = (len(topic_list) + batch_size - 1) // batch_size
    start_batch = max(1, args.start_batch)
    
    logger.info(f"Batch size: {batch_size} topics/batch")
    logger.info(f"Total batches: {total_batches}")
    logger.info(f"Starting from batch: {start_batch}")
    
    grand_total_fetched = 0
    grand_total_inserted = 0
    
    for batch_num in range(start_batch, total_batches + 1):
        batch_start = (batch_num - 1) * batch_size
        batch_end = min(batch_start + batch_size, len(topic_list))
        batch_topics = topic_list[batch_start:batch_end]
        
        logger.info("\n" + "#" * 60)
        logger.info(f"BATCH {batch_num}/{total_batches}")
        logger.info(f"Topics: {[t[0] for t in batch_topics]}")
        logger.info("#" * 60)
        
        # Phase 1: Fetch papers for this batch
        logger.info("\n" + "=" * 60)
        logger.info(f"BATCH {batch_num} - PHASE 1: FETCHING PAPERS FROM APIs")
        logger.info("=" * 60)
        
        topic_results = []
        for topic, topic_queries in batch_topics:
            result = fetcher.fetch_for_topic(
                topic,
                topic_queries,
                papers_per_query=args.limit,
                sources=args.sources,
            )
            topic_results.append(result)
        
        batch_fetched = sum(r["count"] for r in topic_results)
        grand_total_fetched += batch_fetched
        
        # Phase 2: Save this batch to database
        logger.info("\n" + "=" * 60)
        logger.info(f"BATCH {batch_num} - PHASE 2: SAVING TO DATABASE")
        logger.info("=" * 60)
        
        batch_inserted = await fetcher.save_to_database(topic_results, dry_run=args.dry_run)
        grand_total_inserted += batch_inserted
        
        # Batch summary
        logger.info("\n" + "-" * 60)
        logger.info(f"BATCH {batch_num}/{total_batches} COMPLETE")
        logger.info(f"  Fetched this batch: {batch_fetched}")
        logger.info(f"  Inserted this batch: {batch_inserted}")
        logger.info(f"  Running total fetched: {grand_total_fetched}")
        logger.info(f"  Running total inserted: {grand_total_inserted}")
        logger.info("-" * 60)
        sys.stdout.flush()
        
        # Brief pause between batches to be kind to APIs
        if batch_num < total_batches:
            logger.info("Pausing 10s before next batch...")
            await asyncio.sleep(10)
    
    # Final summary
    logger.info("\n" + "=" * 60)
    logger.info(f"ALL BATCHES COMPLETE {'(DRY RUN)' if args.dry_run else ''}")
    logger.info("=" * 60)
    
    logger.info(f"Grand total papers fetched: {grand_total_fetched}")
    logger.info(f"Grand total papers inserted: {grand_total_inserted}")
    logger.info(f"Batches completed: {total_batches - start_batch + 1}")
    
    logger.info("\nDone!")


if __name__ == "__main__":
    asyncio.run(main())



# #!/usr/bin/env python
# """
# fetch_papers.py - Paper Fetching Script

# Main script to fetch research papers from multiple APIs and populate
# the PostgreSQL database. This is used for initial database population.

# Usage:
#     python infrastructure/database/scripts/fetch_papers.py
#     python infrastructure/database/scripts/fetch_papers.py --topics software_testing devops
#     python infrastructure/database/scripts/fetch_papers.py --limit 50 --dry-run
#     python infrastructure/database/scripts/fetch_papers.py --limit 100 --batch-size 3
#     python infrastructure/database/scripts/fetch_papers.py --start-batch 3  # resume from batch 3
# """

# import argparse
# import asyncio
# import logging
# import os
# import sys
# from datetime import datetime
# from pathlib import Path
# from typing import Any, Dict, List, Optional

# import yaml
# from dotenv import load_dotenv

# # Add project paths for imports
# project_root = Path(__file__).parent.parent.parent.parent

# # Add data_ingestion package to path
# sys.path.insert(0, str(project_root / "packages" / "data_ingestion"))

# # Add apps/api to path and change to that context for proper relative imports
# api_path = project_root / "apps" / "api"
# sys.path.insert(0, str(api_path))
# os.chdir(api_path)

# from sqlalchemy import select
# from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

# from src.config import settings
# from src.models.base import Base
# from src.models.paper import Paper
# from ingestion.clients import ArxivClient, DBLPClient, PaperData, SemanticScholarClient
# from ingestion.processors import PaperCategorizer, PaperProcessor

# # Change back to project root for relative paths
# os.chdir(project_root)


# # Database setup - create engine and session maker
# engine = create_async_engine(
#     settings.DATABASE_URL,
#     echo=False,
#     pool_size=settings.DB_POOL_SIZE,
#     max_overflow=settings.DB_MAX_OVERFLOW,
# )

# async_session_maker = async_sessionmaker(
#     engine,
#     class_=AsyncSession,
#     expire_on_commit=False,
#     autocommit=False,
#     autoflush=False,
# )

# # Configure logging
# logging.basicConfig(
#     level=logging.INFO,
#     format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
#     datefmt="%Y-%m-%d %H:%M:%S",
#     handlers=[
#         logging.FileHandler("fetch_papers.log", mode="w"),
#         logging.StreamHandler(sys.stdout),
#     ],
# )
# # Force flush after every log line so terminal shows real-time progress
# for handler in logging.getLogger().handlers:
#     if isinstance(handler, logging.StreamHandler):
#         handler.flush = lambda h=handler: (h.stream.flush(),)
# logger = logging.getLogger(__name__)


# class PaperFetcher:
#     """
#     Orchestrates paper fetching from multiple APIs.
    
#     Coordinates between API clients, processors,
#     and the database layer.
#     """
    
#     def __init__(self, semantic_scholar_api_key: Optional[str] = None):
#         """
#         Initialize fetcher with API clients and processors.
        
#         Args:
#             semantic_scholar_api_key: Optional API key for Semantic Scholar
#                                       (higher rate limits when provided)
#         """
#         logger.info("Initializing PaperFetcher...")
        
#         # Initialize API clients
#         self.arxiv = ArxivClient()
#         self.semantic_scholar = SemanticScholarClient(api_key=semantic_scholar_api_key)
#         self.dblp = DBLPClient()
        
#         # Initialize processors
#         self.processor = PaperProcessor()
#         self.categorizer = PaperCategorizer()
        
#         # Log API key status
#         if semantic_scholar_api_key:
#             logger.info("Semantic Scholar API key configured (higher rate limits)")
#         else:
#             logger.info("Using Semantic Scholar free tier (100 req/5 min)")
        
#         logger.info("PaperFetcher initialized")
    
#     def load_queries(self, query_file: Path) -> Dict[str, List[str]]:
#         """
#         Load search queries from YAML configuration file.
        
#         Args:
#             query_file: Path to queries.yaml
            
#         Returns:
#             Dict mapping topic names to lists of queries
#         """
#         logger.info(f"Loading queries from {query_file}")
        
#         if not query_file.exists():
#             logger.error(f"Query file not found: {query_file}")
#             raise FileNotFoundError(f"Query file not found: {query_file}")
        
#         with open(query_file, "r", encoding="utf-8") as f:
#             queries = yaml.safe_load(f)
        
#         logger.info(f"Loaded {len(queries)} topics")
#         return queries
    
#     def fetch_for_topic(
#         self,
#         topic: str,
#         queries: List[str],
#         papers_per_query: int = 100,
#         sources: Optional[List[str]] = None,
#     ) -> Dict[str, Any]:
#         """
#         Fetch papers for a single topic using multiple queries and APIs.
        
#         Fetches from each API client separately (all queries per client)
#         to respect rate limits and avoid context-switching between APIs.
        
#         Args:
#             topic: Topic name (e.g., "software_testing")
#             queries: List of search queries for this topic
#             papers_per_query: Target papers per query per source
#             sources: List of sources to fetch from (default: all)
            
#         Returns:
#             Dict with topic, papers list, and count
#         """
#         if sources is None:
#             sources = ["arxiv", "semantic_scholar", "dblp"]
        
#         logger.info("=" * 60)
#         logger.info(f"FETCHING: {topic}")
#         logger.info("=" * 60)
#         logger.info(f"Queries: {len(queries)}, Target per query per source: {papers_per_query}")
#         logger.info(f"Sources: {', '.join(sources)}")
        
#         all_papers: List[PaperData] = []
        
#         # --- arXiv (all queries) ---
#         if "arxiv" in sources:
#             logger.info(f"\n  [arXiv] Fetching {len(queries)} queries...")
#             arxiv_count = 0
#             for i, query in enumerate(queries, 1):
#                 logger.info(f"    [{i}/{len(queries)}] arXiv: '{query}'")
#                 try:
#                     papers = self.arxiv.search(query, max_results=papers_per_query)
#                     all_papers.extend(papers)
#                     arxiv_count += len(papers)
#                 except Exception as e:
#                     logger.error(f"      arXiv error: {e}")
#             logger.info(f"  [arXiv] Total: {arxiv_count} papers")
        
#         # --- Semantic Scholar (all queries) ---
#         if "semantic_scholar" in sources:
#             logger.info(f"\n  [Semantic Scholar] Fetching {len(queries)} queries...")
#             ss_count = 0
#             for i, query in enumerate(queries, 1):
#                 logger.info(f"    [{i}/{len(queries)}] Semantic Scholar: '{query}'")
#                 try:
#                     papers = self.semantic_scholar.search(query, max_results=papers_per_query)
#                     all_papers.extend(papers)
#                     ss_count += len(papers)
#                 except Exception as e:
#                     logger.error(f"      Semantic Scholar error: {e}")
#             logger.info(f"  [Semantic Scholar] Total: {ss_count} papers")
        
#         # --- DBLP (all queries) ---
#         # Note: DBLP doesn't provide abstracts, so most papers will be
#         # filtered during validation (abstract is required for NLP).
#         if "dblp" in sources:
#             logger.info(f"\n  [DBLP] Fetching {len(queries)} queries...")
#             dblp_count = 0
#             for i, query in enumerate(queries, 1):
#                 logger.info(f"    [{i}/{len(queries)}] DBLP: '{query}'")
#                 try:
#                     papers = self.dblp.search(query, max_results=papers_per_query)
#                     all_papers.extend(papers)
#                     dblp_count += len(papers)
#                 except Exception as e:
#                     logger.error(f"      DBLP error: {e}")
#             logger.info(f"  [DBLP] Total: {dblp_count} papers")
        
#         logger.info(f"\n  Total raw papers: {len(all_papers)}")
        
#         # Process papers (clean and deduplicate)
#         processed = self.processor.process_papers(all_papers)
#         logger.info(f"  After processing: {len(processed)} papers")
        
#         return {
#             "topic": topic,
#             "papers": processed,
#             "count": len(processed),
#         }
    
#     async def save_to_database(
#         self,
#         topic_results: List[Dict[str, Any]],
#         dry_run: bool = False,
#     ) -> int:
#         """
#         Save processed papers to the database.
        
#         Args:
#             topic_results: List of topic result dicts
#             dry_run: If True, don't actually save (just report)
            
#         Returns:
#             Total number of papers inserted
#         """
#         logger.info("=" * 60)
#         logger.info(f"SAVING TO DATABASE {'(DRY RUN)' if dry_run else ''}")
#         logger.info("=" * 60)
        
#         total_inserted = 0
        
#         async with async_session_maker() as session:
#             for result in topic_results:
#                 topic = result["topic"]
#                 papers = result["papers"]
                
#                 logger.info(f"  Topic: {topic}")
#                 logger.info(f"  Papers to insert: {len(papers)}")
                
#                 inserted, skipped, errors = await self._insert_papers(
#                     session,
#                     papers,
#                     topic,
#                     dry_run,
#                 )
                
#                 total_inserted += inserted
                
#                 logger.info(f"    Inserted: {inserted}")
#                 logger.info(f"    Skipped (duplicates): {skipped}")
#                 logger.info(f"    Errors: {errors}")
        
#         return total_inserted
    
#     async def _insert_papers(
#         self,
#         session: AsyncSession,
#         papers: List[PaperData],
#         topic: str,
#         dry_run: bool,
#     ) -> tuple:
#         """Insert papers into database."""
#         inserted = 0
#         skipped = 0
#         errors = 0
        
#         for paper in papers:
#             try:
#                 # Check for existing paper by DOI
#                 existing = None
#                 if paper.doi:
#                     result = await session.execute(
#                         select(Paper).where(Paper.doi == paper.doi)
#                     )
#                     existing = result.scalar_one_or_none()
                
#                 # Check by similar title if no DOI match
#                 if not existing:
#                     title_prefix = paper.title[:100]
#                     result = await session.execute(
#                         select(Paper).where(Paper.title.ilike(f"{title_prefix}%"))
#                     )
#                     existing = result.scalar_one_or_none()
                
#                 if existing:
#                     skipped += 1
#                     continue
                
#                 if not dry_run:
#                     # Categorize the paper
#                     category = self.categorizer.categorize(paper)
                    
#                     # Create paper record with all required fields
#                     db_paper = Paper(
#                         title=paper.title,
#                         abstract=paper.abstract,
#                         authors=paper.authors,
#                         category=category,
#                         source=paper.source,
#                         year=paper.year,
#                         venue=paper.venue or topic,
#                         doi=paper.doi,
#                         url=paper.url,
#                     )
#                     session.add(db_paper)
                    
#                     # Commit periodically
#                     if inserted % 50 == 0:
#                         await session.commit()
                
#                 inserted += 1
                
#             except Exception as e:
#                 logger.debug(f"Error inserting paper: {e}")
#                 errors += 1
#                 if not dry_run:
#                     await session.rollback()
        
#         # Final commit
#         if not dry_run:
#             try:
#                 await session.commit()
#             except Exception as e:
#                 logger.error(f"Final commit error: {e}")
#                 await session.rollback()
        
#         return inserted, skipped, errors


# async def main() -> None:
#     """Main entry point for paper fetching."""
#     parser = argparse.ArgumentParser(
#         description="Fetch research papers from APIs and populate database"
#     )
    
#     parser.add_argument(
#         "--query-file",
#         default="infrastructure/database/seeds/queries.yaml",
#         help="Path to queries YAML file",
#     )
#     parser.add_argument(
#         "--topics",
#         nargs="+",
#         help="Specific topics to fetch (e.g., software_testing devops)",
#     )
#     parser.add_argument(
#         "--limit",
#         type=int,
#         default=100,
#         help="Papers per topic query (default: 100)",
#     )
#     parser.add_argument(
#         "--dry-run",
#         action="store_true",
#         help="Run without saving to database",
#     )
#     parser.add_argument(
#         "--batch-size",
#         type=int,
#         default=3,
#         help="Number of topics per batch (default: 3, ~1000 papers/batch)",
#     )
#     parser.add_argument(
#         "--start-batch",
#         type=int,
#         default=1,
#         help="Batch number to start from (1-indexed, for resuming)",
#     )
#     parser.add_argument(
#         "--sources",
#         nargs="+",
#         choices=["arxiv", "semantic_scholar", "dblp"],
#         default=None,
#         help="Which API sources to fetch from (default: all). e.g. --sources arxiv semantic_scholar",
#     )
    
#     args = parser.parse_args()
    
#     # Load environment variables from .env file
#     env_file = project_root / "apps" / "api" / ".env"
#     if env_file.exists():
#         load_dotenv(env_file)
#         logger.info(f"Loaded environment from {env_file}")
    
#     # Get Semantic Scholar API key (optional)
#     semantic_scholar_api_key = os.getenv("SEMANTIC_SCHOLAR_API_KEY")
    
#     # Resolve query file path
#     query_file = Path(args.query_file)
#     if not query_file.is_absolute():
#         query_file = project_root / query_file
    
#     # Initialize fetcher with API key
#     fetcher = PaperFetcher(semantic_scholar_api_key=semantic_scholar_api_key)
    
#     # Load queries
#     all_queries = fetcher.load_queries(query_file)
    
#     # Filter topics if specified
#     if args.topics:
#         queries = {k: v for k, v in all_queries.items() if k in args.topics}
#         logger.info(f"Filtered to {len(queries)} specific topics: {args.topics}")
#     else:
#         queries = all_queries
    
#     logger.info(f"Selected {len(queries)} topics for fetching")
    
#     # Split topics into batches
#     topic_list = list(queries.items())
#     batch_size = args.batch_size
#     total_batches = (len(topic_list) + batch_size - 1) // batch_size
#     start_batch = max(1, args.start_batch)
    
#     logger.info(f"Batch size: {batch_size} topics/batch")
#     logger.info(f"Total batches: {total_batches}")
#     logger.info(f"Starting from batch: {start_batch}")
    
#     grand_total_fetched = 0
#     grand_total_inserted = 0
    
#     for batch_num in range(start_batch, total_batches + 1):
#         batch_start = (batch_num - 1) * batch_size
#         batch_end = min(batch_start + batch_size, len(topic_list))
#         batch_topics = topic_list[batch_start:batch_end]
        
#         logger.info("\n" + "#" * 60)
#         logger.info(f"BATCH {batch_num}/{total_batches}")
#         logger.info(f"Topics: {[t[0] for t in batch_topics]}")
#         logger.info("#" * 60)
        
#         # Phase 1: Fetch papers for this batch
#         logger.info("\n" + "=" * 60)
#         logger.info(f"BATCH {batch_num} - PHASE 1: FETCHING PAPERS FROM APIs")
#         logger.info("=" * 60)
        
#         topic_results = []
#         for topic, topic_queries in batch_topics:
#             result = fetcher.fetch_for_topic(
#                 topic,
#                 topic_queries,
#                 papers_per_query=args.limit,
#                 sources=args.sources,
#             )
#             topic_results.append(result)
        
#         batch_fetched = sum(r["count"] for r in topic_results)
#         grand_total_fetched += batch_fetched
        
#         # Phase 2: Save this batch to database
#         logger.info("\n" + "=" * 60)
#         logger.info(f"BATCH {batch_num} - PHASE 2: SAVING TO DATABASE")
#         logger.info("=" * 60)
        
#         batch_inserted = await fetcher.save_to_database(topic_results, dry_run=args.dry_run)
#         grand_total_inserted += batch_inserted
        
#         # Batch summary
#         logger.info("\n" + "-" * 60)
#         logger.info(f"BATCH {batch_num}/{total_batches} COMPLETE")
#         logger.info(f"  Fetched this batch: {batch_fetched}")
#         logger.info(f"  Inserted this batch: {batch_inserted}")
#         logger.info(f"  Running total fetched: {grand_total_fetched}")
#         logger.info(f"  Running total inserted: {grand_total_inserted}")
#         logger.info("-" * 60)
#         sys.stdout.flush()
        
#         # Brief pause between batches to be kind to APIs
#         if batch_num < total_batches:
#             logger.info("Pausing 10s before next batch...")
#             await asyncio.sleep(10)
    
#     # Final summary
#     logger.info("\n" + "=" * 60)
#     logger.info(f"ALL BATCHES COMPLETE {'(DRY RUN)' if args.dry_run else ''}")
#     logger.info("=" * 60)
    
#     logger.info(f"Grand total papers fetched: {grand_total_fetched}")
#     logger.info(f"Grand total papers inserted: {grand_total_inserted}")
#     logger.info(f"Batches completed: {total_batches - start_batch + 1}")
    
#     logger.info("\nDone!")


# if __name__ == "__main__":
#     asyncio.run(main())
