"""
Similarity Package

Similarity computation between embeddings and texts.
"""

from src.similarity.cosine import CosineSimilarity
from src.similarity.vector_search import VectorSearch

__all__ = ["CosineSimilarity", "VectorSearch"]
