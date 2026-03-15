#!/usr/bin/env python
"""
generate_embeddings.py - Backfill and refresh paper embeddings.

This script reads papers from the database, builds text from title + abstract,
encodes that text into vectors, and upserts records in the embeddings table.

It can process all papers or only papers without embeddings, and can optionally
ensure the pgvector cosine index used by similarity search.

Usage:
    python infrastructure/database/scripts/generate_embeddings.py
    python infrastructure/database/scripts/generate_embeddings.py --only-missing
    python infrastructure/database/scripts/generate_embeddings.py --batch-size 128
    python infrastructure/database/scripts/generate_embeddings.py --skip-index
"""

import argparse
import asyncio
import sys
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np

from dotenv import load_dotenv
from sqlalchemy import select, text


PROJECT_ROOT = Path(__file__).resolve().parents[3]
API_PATH = PROJECT_ROOT / "apps" / "api"
NLP_SRC_PATH = PROJECT_ROOT / "packages" / "nlp" / "src"

sys.path.insert(0, str(API_PATH))
sys.path.insert(0, str(NLP_SRC_PATH))

# Load environment before importing settings
load_dotenv(PROJECT_ROOT / ".env")
load_dotenv(API_PATH / ".env")

from src.models.base import async_session_maker
from src.models.embedding import Embedding
from src.models.paper import Paper
from src.services.embedding_service import EmbeddingService


class EmbeddingGenerator:
    """
    Orchestrates embedding generation and persistence.

    This class keeps the end-to-end flow explicit:
    1. Select target papers.
    2. Generate vectors in batches.
    3. Upsert embeddings.
    4. Optionally ensure the vector index.
    """

    def __init__(self, model_name: str, model_version: str):
        """Initialize generator with model metadata and embedding service."""
        self.model_name = model_name
        self.model_version = model_version
        self.embedding_service = EmbeddingService(model_name=model_name)

    @staticmethod
    def chunked(items: Sequence[tuple], size: int) -> Iterable[Sequence[tuple]]:
        """Yield fixed-size chunks from a sequence."""
        for i in range(0, len(items), size):
            yield items[i : i + size]

    @staticmethod
    async def ensure_vector_index(session) -> None:
        """Create pgvector cosine index used by similarity search queries."""
        await session.execute(
            text(
                """
                CREATE INDEX IF NOT EXISTS ix_embeddings_vector_cosine
                ON embeddings
                USING ivfflat (vector vector_cosine_ops)
                WITH (lists = 100)
                """
            )
        )
        await session.execute(text("ANALYZE embeddings"))

    @staticmethod
    def build_papers_query(only_missing: bool):
        """
        Build paper selection query.

        Logic is unchanged:
        - default: all papers ordered by creation time
        - only_missing: only papers with no embedding row
        """
        stmt = select(Paper.id, Paper.title, Paper.abstract).order_by(Paper.created_at)
        if only_missing:
            stmt = (
                select(Paper.id, Paper.title, Paper.abstract)
                .outerjoin(Embedding, Embedding.paper_id == Paper.id)
                .where(Embedding.paper_id.is_(None))
                .order_by(Paper.created_at)
            )
        return stmt

    async def generate(self, batch_size: int, only_missing: bool, ensure_index: bool) -> None:
        """Generate and upsert embeddings for selected papers."""
        async with async_session_maker() as session:
            stmt = self.build_papers_query(only_missing=only_missing)
            paper_rows = list((await session.execute(stmt)).all())
            total = len(paper_rows)

            if total == 0:
                print("No papers found for embedding generation.")
                return

            print(f"Found {total} papers to process.")
            processed = 0

            for batch in self.chunked(paper_rows, batch_size):
                # Build canonical text representation for each paper in this batch.
                texts = [
                    self.embedding_service.build_paper_text(
                        title=row.title,
                        abstract=row.abstract,
                    )
                    for row in batch
                ]

                # Encode all texts at once for efficient model inference.
                vectors = self.embedding_service.encode_texts(texts, batch_size=batch_size)
                vectors_np = np.array(vectors)

                batch_titles = [row.title for row in batch]
                batch_abstracts = [row.abstract for row in batch]

                # Fetch existing embeddings for this batch so we can upsert in-memory.
                batch_ids = [row.id for row in batch]
                existing_rows = await session.execute(
                    select(Embedding).where(Embedding.paper_id.in_(batch_ids))
                )
                existing_map = {
                    embedding.paper_id: embedding
                    for embedding in existing_rows.scalars().all()
                }

                for row, vector in zip(batch, vectors):
                    # Prefer corpus-relative quality when peer vectors are available.
                    quality = self.embedding_service.compute_embedding_quality_score(
                        embedding=np.array(vector),
                        title=row.title,
                        abstract=row.abstract,
                        all_embeddings=vectors_np,
                        all_titles=batch_titles,
                        all_abstracts=batch_abstracts,
                        top_k=min(10, max(len(batch) - 1, 1)),
                    )         
                               
                    embedding = existing_map.get(row.id)

                    if embedding is None:
                        session.add(
                            Embedding(
                                paper_id=row.id,
                                vector=vector,
                                model_name=self.model_name,
                                model_version=self.model_version,
                                embedding_quality_score=quality,
                            )
                        )
                    else:
                        embedding.vector = vector
                        embedding.model_name = self.model_name
                        embedding.model_version = self.model_version
                        embedding.embedding_quality_score = quality

                await session.commit()
                processed += len(batch)
                print(f"Processed {processed}/{total} papers")

            if ensure_index:
                await self.ensure_vector_index(session)
                await session.commit()
                print("Vector index ensured: ix_embeddings_vector_cosine")

            print("Embedding generation completed successfully.")


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for embedding generation."""
    parser = argparse.ArgumentParser(description="Generate embeddings for papers table")
    parser.add_argument(
        "--batch-size",
        type=int,
        default=64,
        help="Batch size for embedding generation",
    )
    parser.add_argument(
        "--model-name",
        type=str,
        default="all-MiniLM-L6-v2",
        help="Sentence transformer model",
    )
    parser.add_argument("--model-version", type=str, default="1.0", help="Model version metadata")
    parser.add_argument(
        "--only-missing",
        action="store_true",
        help="Generate only for papers without existing embeddings",
    )
    parser.add_argument(
        "--skip-index",
        action="store_true",
        help="Skip pgvector index creation/analyze step",
    )
    return parser.parse_args()


async def main() -> None:
    """Main entry point for embedding generation."""
    args = parse_args()

    generator = EmbeddingGenerator(
        model_name=args.model_name,
        model_version=args.model_version,
    )

    await generator.generate(
        batch_size=args.batch_size,
        only_missing=args.only_missing,
        ensure_index=not args.skip_index,
    )


if __name__ == "__main__":
    asyncio.run(main())