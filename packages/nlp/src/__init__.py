"""
NLP Package

Core NLP components for the research paper recommendation system.
"""

from src.embeddings import SentenceTransformerEmbedding
from src.similarity import CosineSimilarity
from src.baselines import TFIDFBaseline, BM25Baseline

__all__ = [
    "SentenceTransformerEmbedding",
    "CosineSimilarity",
    "TFIDFBaseline",
    "BM25Baseline",
]
