"""
Cosine Similarity

Compute cosine similarity between embeddings.
"""

from typing import List, Tuple

import numpy as np
from numpy.linalg import norm


class CosineSimilarity:
    """Compute cosine similarity between vectors."""
    
    @staticmethod
    def compute(vec1: np.ndarray, vec2: np.ndarray) -> float:
        """
        Compute cosine similarity between two vectors.
        
        Args:
            vec1: First vector
            vec2: Second vector
            
        Returns:
            Cosine similarity score between 0 and 1
        """
        if norm(vec1) == 0 or norm(vec2) == 0:
            return 0.0
        
        return float(np.dot(vec1, vec2) / (norm(vec1) * norm(vec2)))
    
    @staticmethod
    def compute_batch(
        query: np.ndarray,
        corpus: np.ndarray,
    ) -> np.ndarray:
        """
        Compute cosine similarity between query and all corpus vectors.
        
        Args:
            query: Query vector of shape (dimension,)
            corpus: Corpus matrix of shape (n_docs, dimension)
            
        Returns:
            Array of similarity scores
        """
        # Normalize query
        query_norm = query / (norm(query) + 1e-8)
        
        # Normalize corpus rows
        corpus_norms = corpus / (norm(corpus, axis=1, keepdims=True) + 1e-8)
        
        # Compute dot products
        similarities = np.dot(corpus_norms, query_norm)
        
        return similarities
    
    @staticmethod
    def top_k(
        query: np.ndarray,
        corpus: np.ndarray,
        k: int = 10,
    ) -> List[Tuple[int, float]]:
        """
        Find top-k most similar vectors.
        
        Args:
            query: Query vector
            corpus: Corpus matrix
            k: Number of results
            
        Returns:
            List of (index, score) tuples
        """
        similarities = CosineSimilarity.compute_batch(query, corpus)
        
        # Get top-k indices
        top_indices = np.argsort(similarities)[-k:][::-1]
        
        return [(int(idx), float(similarities[idx])) for idx in top_indices]
