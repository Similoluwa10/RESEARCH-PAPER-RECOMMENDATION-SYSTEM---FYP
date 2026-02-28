"""
Sentence Transformer Embedding

Embedding generation using sentence-transformers library.
"""

from typing import List, Union

import numpy as np

from src.embeddings.base import BaseEmbedding


class SentenceTransformerEmbedding(BaseEmbedding):
    """
    Text embeddings using Sentence Transformers.
    
    Uses pre-trained models from Hugging Face for semantic text embeddings.
    Default model: all-MiniLM-L6-v2 (384 dimensions, fast inference)
    """
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the embedding model.
        
        Args:
            model_name: Name of the sentence-transformers model
        """
        self._model_name = model_name
        self._model = None
        self._dimension = None
    
    @property
    def model_name(self) -> str:
        return self._model_name
    
    @property
    def dimension(self) -> int:
        if self._dimension is None:
            self._load_model()
        return self._dimension
    
    def _load_model(self):
        """Lazy load the model."""
        if self._model is None:
            # Import here to avoid loading torch on import
            from sentence_transformers import SentenceTransformer
            
            self._model = SentenceTransformer(self._model_name)
            self._dimension = self._model.get_sentence_embedding_dimension()
    
    def encode(self, texts: Union[str, List[str]]) -> np.ndarray:
        """
        Encode text(s) into embeddings.
        
        Args:
            texts: Single text or list of texts
            
        Returns:
            Numpy array of embeddings
        """
        self._load_model()
        
        if isinstance(texts, str):
            texts = [texts]
        
        embeddings = self._model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )
        
        return embeddings
    
    def encode_batch(
        self,
        texts: List[str],
        batch_size: int = 32,
        show_progress: bool = False,
    ) -> np.ndarray:
        """
        Encode texts in batches.
        
        Args:
            texts: List of texts to encode
            batch_size: Batch size for encoding
            show_progress: Show progress bar
            
        Returns:
            Numpy array of embeddings
        """
        self._load_model()
        
        embeddings = self._model.encode(
            texts,
            batch_size=batch_size,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=show_progress,
        )
        
        return embeddings
