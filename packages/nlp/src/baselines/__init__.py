"""
Baselines Package

Baseline methods for comparison with semantic search.
"""

from src.baselines.tfidf import TFIDFBaseline
from src.baselines.bm25 import BM25Baseline
from src.baselines.keyword import KeywordMatcher

__all__ = ["TFIDFBaseline", "BM25Baseline", "KeywordMatcher"]
