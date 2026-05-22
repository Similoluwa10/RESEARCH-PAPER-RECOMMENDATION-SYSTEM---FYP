"""
domain_embeddings.py - Domain-Specific Embedding Models

Provides semantic embedding using domain-optimized models.
Supports SPECTER (academic papers) and other specialized models.
"""

import numpy as np
from typing import List, Union
import logging

logger = logging.getLogger(__name__)


class DomainEmbeddingModel:
    """Wrapper for domain-specific embedding models."""
    
    def __init__(self, model_name: str = "allenai/specter"):
        """
        Initialize domain embedding model.
        
        Args:
            model_name: Model identifier (specter, sciBERT, or fallback)
        """
        self.model_name = model_name
        self.model = None
        self.tokenizer = None
        self._load_model()
    
    def _load_model(self):
        """Load the specified embedding model."""
        try:
            if "specter" in self.model_name.lower():
                self._load_specter()
            elif "scibert" in self.model_name.lower():
                self._load_scibert()
            else:
                self._load_default()
        except Exception as e:
            logger.warning(f"Failed to load {self.model_name}: {e}. Falling back to default model.")
            self._load_default()
    
    def _load_specter(self):
        """Load SPECTER model (optimized for academic papers)."""
        try:
            from transformers import AutoTokenizer, AutoModel
            
            logger.info("Loading SPECTER model for academic papers...")
            self.tokenizer = AutoTokenizer.from_pretrained("allenai/specter")
            self.model = AutoModel.from_pretrained("allenai/specter")
            self.model_type = "specter"
            logger.info("SPECTER model loaded successfully")
        except ImportError:
            logger.warning("transformers library not available. Using sentence-transformers instead.")
            self._load_sentence_transformer()
    
    def _load_scibert(self):
        """Load SciBERT (scientific paper embeddings)."""
        try:
            from transformers import AutoTokenizer, AutoModel
            
            logger.info("Loading SciBERT model...")
            self.tokenizer = AutoTokenizer.from_pretrained("allenai/scibert-base-cased")
            self.model = AutoModel.from_pretrained("allenai/scibert-base-cased")
            self.model_type = "scibert"
            logger.info("SciBERT model loaded successfully")
        except ImportError:
            logger.warning("SciBERT loading failed. Falling back to default.")
            self._load_default()
    
    def _load_sentence_transformer(self):
        """Load sentence-transformers (fallback option)."""
        try:
            from sentence_transformers import SentenceTransformer
            
            # Use a larger, more capable model than all-MiniLM
            logger.info("Loading MPNet model (improved sentence-transformers)...")
            self.model = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')
            self.model_type = "sentence_transformer"
            logger.info("MPNet model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load sentence-transformers: {e}")
            raise
    
    def _load_default(self):
        """Load default embedding model."""
        self._load_sentence_transformer()
    
    def encode(self, texts: Union[str, List[str]], **kwargs) -> np.ndarray:
        """
        Encode texts to embeddings.
        
        Args:
            texts: Single text or list of texts
            **kwargs: Additional arguments for the model
            
        Returns:
            Numpy array of embeddings
        """
        if isinstance(texts, str):
            texts = [texts]
        
        if self.model_type == "specter":
            return self._encode_specter(texts, **kwargs)
        elif self.model_type == "scibert":
            return self._encode_transformers(texts, **kwargs)
        else:  # sentence_transformer
            return self._encode_sentence_transformer(texts, **kwargs)
    
    def _encode_specter(self, texts: List[str], **kwargs) -> np.ndarray:
        """Encode using SPECTER."""
        import torch
        
        # SPECTER expects title and abstract
        inputs = self.tokenizer(
            texts,
            padding=True,
            truncation=True,
            return_tensors="pt",
            max_length=512
        )
        
        with torch.no_grad():
            outputs = self.model(**inputs)
        
        # Use [CLS] token representation
        embeddings = outputs.last_hidden_state[:, 0, :].cpu().numpy()
        return embeddings
    
    def _encode_transformers(self, texts: List[str], **kwargs) -> np.ndarray:
        """Encode using transformers (SciBERT, etc.)."""
        import torch
        
        inputs = self.tokenizer(
            texts,
            padding=True,
            truncation=True,
            return_tensors="pt",
            max_length=512
        )
        
        with torch.no_grad():
            outputs = self.model(**inputs)
        
        embeddings = outputs.last_hidden_state[:, 0, :].cpu().numpy()
        return embeddings
    
    def _encode_sentence_transformer(self, texts: List[str], **kwargs) -> np.ndarray:
        """Encode using sentence-transformers."""
        return self.model.encode(texts, convert_to_numpy=True, **kwargs)


class HybridEmbedding:
    """
    Hybrid embedding combining semantic and lexical information.
    
    Uses domain model for semantic understanding + TF-IDF for keyword matching.
    """
    
    def __init__(self, semantic_model: str = "allenai/specter"):
        self.domain_model = DomainEmbeddingModel(semantic_model)
        self.semantic_weight = 0.7
        self.lexical_weight = 0.3
    
    def encode(self, texts: Union[str, List[str]]) -> np.ndarray:
        """Get hybrid embeddings (weighted semantic + lexical)."""
        # For now, return pure semantic embeddings
        # Lexical information is handled by TF-IDF in hybrid search
        return self.domain_model.encode(texts)
