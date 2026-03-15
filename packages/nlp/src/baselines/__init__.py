"""
Baselines Package

Baseline methods for comparison with semantic search.
"""

from .tfidf import TFIDFBaseline
from .bm25 import BM25Baseline
from .keyword import KeywordMatcher

__all__ = ["TFIDFBaseline", "BM25Baseline", "KeywordMatcher"]
