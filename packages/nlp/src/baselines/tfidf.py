"""
TF-IDF Baseline

Traditional TF-IDF based text similarity.
"""

from typing import List, Tuple

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class TFIDFBaseline:
    """
    TF-IDF based text similarity baseline.
    
    Used for comparison against semantic search methods.
    """
    
    def __init__(
        self,
        max_features: int = 10000,
        ngram_range: Tuple[int, int] = (1, 2),
        min_df: int = 2,
        max_df: float = 0.95,
    ):
        """
        Initialize TF-IDF vectorizer.
        
        Args:
            max_features: Maximum vocabulary size
            ngram_range: N-gram range (min, max)
            min_df: Minimum document frequency
            max_df: Maximum document frequency
        """
        self.vectorizer = TfidfVectorizer(
            max_features=max_features,
            ngram_range=ngram_range,
            min_df=min_df,
            max_df=max_df,
            stop_words="english",
        )
        self._corpus_vectors = None
        self._is_fitted = False
    
    def fit(self, corpus: List[str]) -> "TFIDFBaseline":
        """
        Fit the vectorizer on a corpus.
        
        Args:
            corpus: List of documents
            
        Returns:
            Self for chaining
        """
        self._corpus_vectors = self.vectorizer.fit_transform(corpus)
        self._is_fitted = True
        return self

    def fit_low_memory(
        self,
        corpus: List[str],
        chunk_size: int = 1000,
        candidate_factor: int = 3,
        max_tracked_terms: int = 400_000,
    ) -> "TFIDFBaseline":
        """
        Fit with bounded peak memory.

        A plain ``fit`` first builds the vocabulary of *every* n-gram in the
        corpus (millions of bigrams) before trimming it to ``max_features``,
        which can need 500 MB+. This variant:

        1. streams over the corpus in chunks, keeping approximate term counts
           for at most ``max_tracked_terms`` terms (rare terms are pruned);
        2. recounts the most frequent candidates exactly and applies the same
           ``min_df`` / ``max_df`` / ``max_features`` rules as scikit-learn;
        3. fits the TF-IDF vectorizer on that fixed vocabulary.

        The resulting vocabulary, IDF weights and document vectors match
        ``fit`` except for possible tie-breaks at the ``max_features`` cutoff.
        """
        import gc
        from collections import Counter

        from sklearn.feature_extraction.text import CountVectorizer

        params = self.vectorizer.get_params()
        n_docs = len(corpus)
        max_features = params["max_features"]
        min_df, max_df = params["min_df"], params["max_df"]
        min_doc_count = min_df if isinstance(min_df, int) else min_df * n_docs
        max_doc_count = max_df if isinstance(max_df, int) else max_df * n_docs

        counter_params = {
            k: params[k]
            for k in (
                "lowercase", "preprocessor", "tokenizer", "analyzer", "stop_words",
                "token_pattern", "ngram_range", "strip_accents", "input",
                "encoding", "decode_error",
            )
        }

        # Pass 1: approximate corpus term frequencies with pruning.
        approx_tf: Counter = Counter()
        threshold = 1
        for start in range(0, n_docs, chunk_size):
            cv = CountVectorizer(**counter_params)
            X = cv.fit_transform(corpus[start:start + chunk_size])
            tfs = np.asarray(X.sum(axis=0)).ravel()
            for term, idx in cv.vocabulary_.items():
                approx_tf[term] += int(tfs[idx])
            del cv, X, tfs
            while len(approx_tf) > max_tracked_terms:
                approx_tf = Counter({t: c for t, c in approx_tf.items() if c > threshold})
                threshold += 1
            gc.collect()

        if max_features:
            n_candidates = max_features * candidate_factor
            candidates = sorted(t for t, _ in approx_tf.most_common(n_candidates))
        else:
            candidates = sorted(approx_tf)
        del approx_tf
        gc.collect()

        # Pass 2: exact tf / df for candidates, then sklearn's selection rules.
        cv = CountVectorizer(vocabulary=candidates, **counter_params)
        tfs = np.zeros(len(candidates), dtype=np.int64)
        dfs = np.zeros(len(candidates), dtype=np.int64)
        for start in range(0, n_docs, chunk_size):
            X = cv.transform(corpus[start:start + chunk_size])
            tfs += np.asarray(X.sum(axis=0)).ravel()
            X.data[:] = 1
            dfs += np.asarray(X.sum(axis=0)).ravel()
        del cv

        mask = (dfs >= min_doc_count) & (dfs <= max_doc_count)
        kept = np.flatnonzero(mask)
        if max_features and len(kept) > max_features:
            order = (-tfs[kept]).argsort(kind="stable")[:max_features]
            kept = np.sort(kept[order])
        vocabulary = [candidates[i] for i in kept]
        del candidates, tfs, dfs
        gc.collect()

        # Pass 3: TF-IDF on the fixed vocabulary (no full n-gram dictionary).
        params.update(vocabulary=vocabulary, max_features=None, min_df=1, max_df=1.0)
        self.vectorizer = TfidfVectorizer(**params)
        self._corpus_vectors = self.vectorizer.fit_transform(corpus)
        self._is_fitted = True
        return self

    def search(
        self,
        query: str,
        top_k: int = 10,
    ) -> List[Tuple[int, float]]:
        """
        Search for similar documents.
        
        Args:
            query: Query text
            top_k: Number of results
            
        Returns:
            List of (index, score) tuples
        """
        if not self._is_fitted:
            raise ValueError("Must call fit() before search()")
        
        query_vector = self.vectorizer.transform([query])
        similarities = cosine_similarity(query_vector, self._corpus_vectors).flatten()
        
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        
        return [(int(idx), float(similarities[idx])) for idx in top_indices]
    
    def get_feature_names(self) -> List[str]:
        """Get vocabulary terms."""
        return self.vectorizer.get_feature_names_out().tolist()
