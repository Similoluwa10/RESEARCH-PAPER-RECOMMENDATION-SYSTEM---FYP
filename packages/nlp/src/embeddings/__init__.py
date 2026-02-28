"""
Embeddings Package

Text embedding generation using various models.
"""

from src.embeddings.base import BaseEmbedding
from src.embeddings.sentence_transformer import SentenceTransformerEmbedding

__all__ = ["BaseEmbedding", "SentenceTransformerEmbedding"]
