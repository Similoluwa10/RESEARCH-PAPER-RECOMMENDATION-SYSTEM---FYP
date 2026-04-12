"""
Sentence Transformer Embedding

Embedding generation using sentence-transformers library.
"""

from typing import List, Optional, Union

import numpy as np

from .base import BaseEmbedding


class SentenceTransformerEmbedding(BaseEmbedding):
    """
    Text embeddings using Sentence Transformers.
    
    Uses pre-trained models from Hugging Face for semantic text embeddings.
    Default model: all-MiniLM-L6-v2 (384 dimensions, fast inference)
    
    When a Hugging Face API token is provided, it enables authenticated requests
    which allow higher rate limits and access to private models.
    """
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", hf_token: Optional[str] = None):
        """
        Initialize the embedding model.
        
        Args:
            model_name: Name of the sentence-transformers model
            hf_token: Optional Hugging Face API token for authenticated requests
                     (higher rate limits and access to private models)
        """
        self._model_name = model_name
        self._hf_token = hf_token
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
        """Lazy load the model with Hugging Face authentication if available."""
        if self._model is None:
            # Import here to avoid loading torch on import
            from sentence_transformers import SentenceTransformer
            
            # Pass HF token to SentenceTransformer for authenticated requests
            # This allows higher rate limits and access to private models
            self._model = SentenceTransformer(
                self._model_name,
                use_auth_token=self._hf_token
            )
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
