"""
NLP Package

Core NLP components for the research paper recommendation system.

Components are imported lazily to keep process memory low: heavy libraries
(scikit-learn, NLTK, PyTorch) are only loaded when actually used.
"""

import importlib

_LAZY = {
    "SentenceTransformerEmbedding": ".embeddings",
    "OnnxEmbedding": ".embeddings",
    "CosineSimilarity": ".similarity",
    "TFIDFBaseline": ".baselines",
    "BM25Baseline": ".baselines",
}

__all__ = list(_LAZY)


def __getattr__(name):
    if name in _LAZY:
        module = importlib.import_module(_LAZY[name], __name__)
        return getattr(module, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
