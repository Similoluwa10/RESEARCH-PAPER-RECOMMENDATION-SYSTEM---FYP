"""
Vector Search

Integration with pgvector for efficient similarity search.
"""

from typing import List, Tuple

import numpy as np


class VectorSearch:
    """
    Vector similarity search utilities for pgvector integration.
    
    This class provides helper methods for building pgvector queries.
    """
    
    @staticmethod
    def to_pgvector_string(embedding: np.ndarray) -> str:
        """
        Convert numpy array to pgvector string format.
        
        Args:
            embedding: Numpy array of shape (dimension,)
            
        Returns:
            String formatted for pgvector: '[0.1, 0.2, ...]'
        """
        return "[" + ",".join(map(str, embedding.tolist())) + "]"
    
    @staticmethod
    def from_pgvector_string(vector_str: str) -> np.ndarray:
        """
        Convert pgvector string to numpy array.
        
        Args:
            vector_str: String from pgvector: '[0.1, 0.2, ...]'
            
        Returns:
            Numpy array
        """
        # Remove brackets and parse
        values = vector_str.strip("[]").split(",")
        return np.array([float(v) for v in values])
    
    @staticmethod
    def build_similarity_query(
        table: str = "embeddings",
        vector_column: str = "vector",
        top_k: int = 10,
    ) -> str:
        """
        Build a pgvector similarity search SQL query.
        
        Uses cosine distance operator (<=>).
        
        Args:
            table: Table name
            vector_column: Column containing vectors
            top_k: Number of results
            
        Returns:
            SQL query template with placeholder for query vector
        """
        return f"""
        SELECT paper_id, 1 - ({vector_column} <=> $1::vector) AS similarity
        FROM {table}
        ORDER BY {vector_column} <=> $1::vector
        LIMIT {top_k}
        """
