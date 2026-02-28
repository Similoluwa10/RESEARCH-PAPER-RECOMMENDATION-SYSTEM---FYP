"""
Base Embedding Interface

Abstract base class for embedding models.
"""

from abc import ABC, abstractmethod
from typing import List, Union

import numpy as np


class BaseEmbedding(ABC):
    """Abstract base class for text embedding models."""
    
    @property
    @abstractmethod
    def model_name(self) -> str:
        """Get the model name."""
        pass
    
    @property
    @abstractmethod
    def dimension(self) -> int:
        """Get the embedding dimension."""
        pass
    
    @abstractmethod
    def encode(self, texts: Union[str, List[str]]) -> np.ndarray:
        """
        Encode text(s) into embeddings.
        
        Args:
            texts: Single text or list of texts to encode
            
        Returns:
            Numpy array of shape (n_texts, dimension)
        """
        pass
    
    @abstractmethod
    def encode_batch(
        self,
        texts: List[str],
        batch_size: int = 32,
    ) -> np.ndarray:
        """
        Encode texts in batches for memory efficiency.
        
        Args:
            texts: List of texts to encode
            batch_size: Batch size for encoding
            
        Returns:
            Numpy array of shape (n_texts, dimension)
        """
        pass
