"""
Similarity Package

Similarity computation between embeddings and texts.
"""

from .cosine import CosineSimilarity
from .vector_search import VectorSearch

__all__ = ["CosineSimilarity", "VectorSearch"]
