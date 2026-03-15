"""
NLP Package

Core NLP components for the research paper recommendation system.
"""

from .embeddings import SentenceTransformerEmbedding
from .similarity import CosineSimilarity
from .baselines import TFIDFBaseline, BM25Baseline

__all__ = [
    "SentenceTransformerEmbedding",
    "CosineSimilarity",
    "TFIDFBaseline",
    "BM25Baseline",
]
