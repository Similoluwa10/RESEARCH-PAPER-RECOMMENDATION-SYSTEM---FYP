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
