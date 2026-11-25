"""
Baselines Package

Baseline methods for comparison with semantic search.

Submodules are imported lazily so that importing one baseline (e.g. TF-IDF)
does not pull in the dependencies of the others (e.g. NLTK for BM25).
"""

import importlib

_LAZY = {
    "TFIDFBaseline": ".tfidf",
    "BM25Baseline": ".bm25",
    "KeywordMatcher": ".keyword",
}

__all__ = list(_LAZY)


def __getattr__(name):
    if name in _LAZY:
        module = importlib.import_module(_LAZY[name], __name__)
        return getattr(module, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
