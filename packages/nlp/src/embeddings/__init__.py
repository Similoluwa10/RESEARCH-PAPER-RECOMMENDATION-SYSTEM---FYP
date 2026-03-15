"""
Embeddings Package

Text embedding generation using various models.
"""

from .base import BaseEmbedding
from .sentence_transformer import SentenceTransformerEmbedding

__all__ = ["BaseEmbedding", "SentenceTransformerEmbedding"]
