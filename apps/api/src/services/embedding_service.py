"""
embedding_service.py - Shared Embedding Service

Centralized service for text embedding generation and embedding quality scoring.

This service wraps the NLP package implementation used across API services,
and keeps paper-text formatting, vector encoding, and quality heuristics in
one reusable component.
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

import numpy as np
from scipy.spatial.distance import cosine

from src.config import settings

logger = logging.getLogger(__name__)


PROJECT_ROOT = Path(__file__).resolve().parents[4]
NLP_SRC_PATH = PROJECT_ROOT / "packages" / "nlp" / "src"

if str(NLP_SRC_PATH) not in sys.path:
    sys.path.insert(0, str(NLP_SRC_PATH))

from embeddings.sentence_transformer import SentenceTransformerEmbedding


class EmbeddingService:
    """
    Service for generating normalized sentence embeddings.

    The implementation uses the local NLP package's
    `SentenceTransformerEmbedding`, which lazily loads the underlying model.
    """

    def __init__(self, model_name: str | None = None):
        """
        Initialize embedding service.

        Args:
            model_name: Optional model override. If omitted, uses
                `settings.EMBEDDING_MODEL_NAME`.
        """
        self.model_name = model_name or settings.EMBEDDING_MODEL_NAME
        self.model = SentenceTransformerEmbedding(self.model_name)

    @property
    def dimension(self) -> int:
        """Return embedding dimension for the configured model."""
        return self.model.dimension

    def build_paper_text(self, title: str, abstract: str) -> str:
        """
        Build canonical text payload used for paper embeddings.

        The output intentionally follows a labeled format to keep input
        structure consistent across offline scripts and API requests.

        Args:
            title: Paper title.
            abstract: Paper abstract.

        Returns:
            Labeled text with normalized whitespace.
        """
        title = (title or "").strip()
        abstract = (abstract or "").strip()
        return f"Title: {title}\n\nAbstract: {abstract}"

    def encode_text(self, text: str) -> List[float]:
        """
        Encode one text into a normalized embedding vector.

        Args:
            text: Input text to embed.

        Returns:
            Dense embedding as a Python list of floats.
        """
        embedding = self.model.encode(text)[0]
        return embedding.tolist()

    def encode_texts(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """
        Encode multiple texts in batches.

        Args:
            texts: Input texts to embed.
            batch_size: Batch size passed to the model encoder.

        Returns:
            List of embedding vectors in the same order as `texts`.
        """
        embeddings = self.model.encode_batch(texts, batch_size=batch_size, show_progress=False)
        return [vector.tolist() for vector in embeddings]

    # def compute_quality_score(self, title: str, abstract: str) -> float:
    #     """
    #     Compute lightweight heuristic quality from text richness only.

    #     This compatibility method is used by existing write paths that do not
    #     have access to a corpus of peer embeddings.

    #     Args:
    #         title: Paper title.
    #         abstract: Paper abstract.

    #     Returns:
    #         Float in [0.0, 1.0], rounded to 4 decimals.
    #     """
    #     title_tokens = len((title or "").split())
    #     abstract_tokens = len((abstract or "").split())
    #     total_chars = len((title or "")) + len((abstract or ""))

    #     title_score = min(title_tokens / 12.0, 1.0)
    #     abstract_score = min(abstract_tokens / 220.0, 1.0)
    #     length_score = min(total_chars / 2000.0, 1.0)

    #     return round((0.25 * title_score) + (0.55 * abstract_score) + (0.20 * length_score), 4)

    @staticmethod
    def compute_embedding_quality_score(
        embedding: np.ndarray,
        title: str,
        abstract: str,
        all_embeddings: np.ndarray,
        all_titles: List[str],
        all_abstracts: List[str],
        top_k: int = 10,
    ) -> float:
        """
        Evaluate quality score for a single embedding.

        Measures whether this embedding is most similar to papers that are also
        textually similar by title/abstract overlap.

        Args:
            embedding: Single embedding vector to evaluate.
            title: Title for the evaluated paper.
            abstract: Abstract for the evaluated paper.
            all_embeddings: Corpus embeddings, shape (n_papers, embedding_dim).
            all_titles: Titles for corpus embeddings.
            all_abstracts: Abstracts for corpus embeddings.
            top_k: Number of nearest neighbors used for scoring.

        Returns:
            Quality score in [0.0, 1.0].
        """
        preview = (title or "")[:50]
        logger.info(f"Computing embedding quality for: {preview}...")

        if len(all_embeddings) < 5:
            logger.warning("Not enough papers to compute quality score")
            return 0.0

        if len(all_titles) != len(all_embeddings) or len(all_abstracts) != len(all_embeddings):
            logger.warning("Metadata length mismatch for embedding quality score")
            return 0.0

        similarities: List[Tuple[int, float]] = []
        for idx in range(len(all_embeddings)):
            sim = 1 - cosine(embedding, all_embeddings[idx])
            if np.isnan(sim):
                sim = 0.0
            similarities.append((idx, float(sim)))

        similarities.sort(key=lambda item: item[1], reverse=True)

        # Exclude potential self match by near-1.0 similarity threshold.
        top_similar = [sim for sim in similarities if sim[1] < 0.9999][:top_k]

        this_text = f"{title or ''} {abstract or ''}".lower()
        this_words = set(this_text.split())

        text_similarities: List[float] = []
        embedding_similarities: List[float] = []

        for idx, emb_sim in top_similar:
            other_text = f"{all_titles[idx] or ''} {all_abstracts[idx] or ''}".lower()
            other_words = set(other_text.split())

            common_words = len(this_words & other_words)
            total_words = len(this_words | other_words)
            text_sim = (common_words / total_words) if total_words > 0 else 0.0

            text_similarities.append(float(text_sim))
            embedding_similarities.append(float(emb_sim))

        correlation = 0.0
        if text_similarities and embedding_similarities:
            meaningful_indices = [i for i, t in enumerate(text_similarities) if t > 0.2]
            if meaningful_indices:
                correlation = float(np.mean([embedding_similarities[i] for i in meaningful_indices]))
            else:
                correlation = 0.5

        quality_score = min(max(correlation, 0.0), 1.0)

        avg_text_similarity = float(np.mean(text_similarities)) if text_similarities else 0.0
        avg_embedding_similarity = (
            float(np.mean(embedding_similarities)) if embedding_similarities else 0.0
        )

        logger.info(f"Quality score: {quality_score:.4f}")
        logger.info(f"  Top similar papers: {len(top_similar)}")
        logger.info(f"  Avg text similarity: {avg_text_similarity:.4f}")
        logger.info(f"  Avg embedding similarity: {avg_embedding_similarity:.4f}")

        return round(quality_score, 4)


