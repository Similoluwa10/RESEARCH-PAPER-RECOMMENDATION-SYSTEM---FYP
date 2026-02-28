"""
Feature Importance

Compute feature importance for recommendations.
"""

from typing import Dict, List, Tuple

import numpy as np


class FeatureImportance:
    """
    Compute feature importance for recommendation explanations.
    
    Analyzes which terms contribute most to similarity scores.
    """
    
    def __init__(self):
        pass
    
    def compute_term_contributions(
        self,
        query_embedding: np.ndarray,
        doc_embedding: np.ndarray,
        query_terms: List[str],
        term_embeddings: Dict[str, np.ndarray],
    ) -> List[Tuple[str, float]]:
        """
        Compute contribution of each query term to the similarity.
        
        Args:
            query_embedding: Full query embedding
            doc_embedding: Document embedding
            query_terms: List of query terms
            term_embeddings: Embeddings for each term
            
        Returns:
            List of (term, contribution) sorted by importance
        """
        contributions = []
        
        for term in query_terms:
            if term not in term_embeddings:
                continue
            
            term_emb = term_embeddings[term]
            
            # Compute how much this term contributes to overall similarity
            term_sim = float(np.dot(term_emb, doc_embedding))
            contributions.append((term, term_sim))
        
        # Sort by contribution
        contributions.sort(key=lambda x: x[1], reverse=True)
        
        return contributions
    
    def get_top_contributing_terms(
        self,
        contributions: List[Tuple[str, float]],
        top_k: int = 5,
    ) -> List[str]:
        """Get top-k most contributing terms."""
        return [term for term, _ in contributions[:top_k]]
    
    def normalize_contributions(
        self,
        contributions: List[Tuple[str, float]],
    ) -> List[Tuple[str, float]]:
        """Normalize contributions to sum to 1."""
        total = sum(abs(score) for _, score in contributions)
        
        if total == 0:
            return contributions
        
        return [(term, score / total) for term, score in contributions]
