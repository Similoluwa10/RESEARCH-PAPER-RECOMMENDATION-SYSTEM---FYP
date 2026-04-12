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
import time
from collections import OrderedDict
from pathlib import Path
from threading import Lock
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

#from packages.nlp.src.embeddings.sentence_transformer import SentenceTransformerEmbedding


class EmbeddingService:
    """
    Service for generating normalized sentence embeddings.

    The implementation uses the local NLP package's
    `SentenceTransformerEmbedding`, which lazily loads the underlying model.
    
    Implements multi-level caching:
    - Model cache: Reuses loaded models across instances
    - Embedding cache: LRU cache for computed embeddings (1 hour TTL, 5000 items)
    - Batch caching: Intelligently caches batch operations
    """

    _model_cache: Dict[str, SentenceTransformerEmbedding] = {}
    _model_cache_lock = Lock()

    _embedding_cache: "OrderedDict[str, tuple[float, List[float]]]" = OrderedDict()
    _embedding_cache_lock = Lock()
    
    # Stats for cache performance monitoring
    _cache_hits: int = 0
    _cache_misses: int = 0
    _stats_lock = Lock()

    def __init__(self, model_name: str | None = None):
        """
        Initialize embedding service.

        Args:
            model_name: Optional model override. If omitted, uses
                `settings.EMBEDDING_MODEL_NAME`.
        """
        self.model_name = model_name or settings.EMBEDDING_MODEL_NAME
        self.model = self._get_or_create_model(self.model_name)
        
        # Use configurable cache settings
        self._embedding_cache_ttl = settings.EMBEDDING_CACHE_TTL_SECONDS
        self._embedding_cache_max = settings.EMBEDDING_CACHE_MAX_ITEMS

    @classmethod
    def _get_or_create_model(cls, model_name: str) -> SentenceTransformerEmbedding:
        with cls._model_cache_lock:
            model = cls._model_cache.get(model_name)
            if model is None:
                # Pass Hugging Face API token for authenticated requests
                # This avoids rate limits when downloading models
                hf_token = settings.HUGGINGFACE_API_KEY if settings.HUGGINGFACE_API_KEY else None
                model = SentenceTransformerEmbedding(model_name, hf_token=hf_token)
                cls._model_cache[model_name] = model
            return model

    @staticmethod
    def _normalize_text_for_cache(text: str) -> str:
        return " ".join((text or "").strip().split())

    @classmethod
    def _get_cached_embedding(cls, cache_key: str) -> List[float] | None:
        now = time.monotonic()
        with cls._embedding_cache_lock:
            cached = cls._embedding_cache.get(cache_key)
            if cached is None:
                with cls._stats_lock:
                    cls._cache_misses += 1
                return None

            created_at, vector = cached
            # Use configurable TTL from settings
            ttl = settings.EMBEDDING_CACHE_TTL_SECONDS
            if now - created_at > ttl:
                cls._embedding_cache.pop(cache_key, None)
                with cls._stats_lock:
                    cls._cache_misses += 1
                return None

            cls._embedding_cache.move_to_end(cache_key)
            with cls._stats_lock:
                cls._cache_hits += 1
            logger.debug(f"Embedding cache HIT for key: {cache_key[:50]}...")
            return list(vector)

    @classmethod
    def _set_cached_embedding(cls, cache_key: str, vector: List[float]) -> None:
        now = time.monotonic()
        with cls._embedding_cache_lock:
            cls._embedding_cache[cache_key] = (now, list(vector))
            cls._embedding_cache.move_to_end(cache_key)

            # Use configurable max items from settings
            max_items = settings.EMBEDDING_CACHE_MAX_ITEMS
            while len(cls._embedding_cache) > max_items:
                cls._embedding_cache.popitem(last=False)
            
            logger.debug(f"Embedding cache SET: {len(cls._embedding_cache)} items in cache")

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
        cache_key = self._normalize_text_for_cache(text)
        cached_vector = self._get_cached_embedding(cache_key)
        if cached_vector is not None:
            return cached_vector

        embedding = self.model.encode(text)[0]
        vector = embedding.tolist()
        self._set_cached_embedding(cache_key, vector)
        return vector

    def encode_texts(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """
        Encode multiple texts in batches with intelligent caching.

        Checks cache for each text first, encoding only uncached texts.
        Significantly improves performance for repeated or overlapping queries.

        Args:
            texts: Input texts to embed.
            batch_size: Batch size passed to the model encoder.

        Returns:
            List of embedding vectors in the same order as `texts`.
        """
        # Normalize cache keys for all texts
        cache_keys = [self._normalize_text_for_cache(text) for text in texts]
        
        # Check which texts are already cached
        cached_vectors = []
        uncached_indices = []
        uncached_texts = []
        
        for idx, (text, cache_key) in enumerate(zip(texts, cache_keys)):
            cached = self._get_cached_embedding(cache_key)
            if cached is not None:
                cached_vectors.append((idx, cached))
            else:
                uncached_indices.append(idx)
                uncached_texts.append(text)
        
        # Initialize result list
        result = [None] * len(texts)
        
        # Add cached vectors to result
        for idx, vector in cached_vectors:
            result[idx] = vector
        
        # Encode only uncached texts if any
        if uncached_texts:
            logger.info(
                f"Batch encoding {len(uncached_texts)}/{len(texts)} texts "
                f"({len(cached_vectors)} from cache)"
            )
            embeddings = self.model.encode_batch(
                uncached_texts,
                batch_size=batch_size,
                show_progress=False,
            )
            
            # Cache the newly encoded embeddings
            for idx_in_uncached, (text_idx, text) in enumerate(
                zip(uncached_indices, uncached_texts)
            ):
                vector = embeddings[idx_in_uncached].tolist()
                cache_key = cache_keys[text_idx]
                self._set_cached_embedding(cache_key, vector)
                result[text_idx] = vector
        
        return result

    @classmethod
    def get_cache_stats(cls) -> Dict[str, Any]:
        """
        Get current embedding cache statistics.
        
        Returns:
            Dict with cache hit/miss stats and current cache size
        """
        with cls._stats_lock:
            total_requests = cls._cache_hits + cls._cache_misses
            hit_rate = (
                (cls._cache_hits / total_requests * 100)
                if total_requests > 0
                else 0
            )
        
        return {
            "cache_hits": cls._cache_hits,
            "cache_misses": cls._cache_misses,
            "total_requests": total_requests,
            "hit_rate_percent": round(hit_rate, 2),
            "cache_size": len(cls._embedding_cache),
            "max_cache_size": settings.EMBEDDING_CACHE_MAX_ITEMS,
        }

    @classmethod
    def reset_cache_stats(cls) -> None:
        """Reset cache statistics counters."""
        with cls._stats_lock:
            cls._cache_hits = 0
            cls._cache_misses = 0
        logger.info("Cache statistics reset")

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


