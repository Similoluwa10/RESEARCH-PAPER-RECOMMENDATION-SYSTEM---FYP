"""
ONNX Embedding

Lightweight embedding generation using fastembed (ONNX Runtime).

Produces the same vectors as the sentence-transformers version of the model
(mean pooling + L2 normalisation) but without importing PyTorch, which keeps
process memory roughly 300-400 MB lower. This is what lets the API run on
small instances such as Render's 512 MB free tier.
"""

import os
from typing import List, Optional, Union

import numpy as np

from .base import BaseEmbedding


def _to_fastembed_name(model_name: str) -> str:
    """fastembed expects the fully qualified Hugging Face repo id."""
    if "/" not in model_name:
        return f"sentence-transformers/{model_name}"
    return model_name


class OnnxEmbedding(BaseEmbedding):
    """Text embeddings computed with fastembed / ONNX Runtime (CPU)."""

    def __init__(
        self,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        hf_token: Optional[str] = None,
        cache_dir: Optional[str] = None,
        threads: Optional[int] = None,
    ):
        self._model_name = _to_fastembed_name(model_name)
        self._hf_token = hf_token
        self._cache_dir = cache_dir or os.getenv("FASTEMBED_CACHE_PATH")
        self._threads = threads or int(os.getenv("EMBEDDING_THREADS", "1"))
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
        if self._model is None:
            if self._hf_token:
                os.environ.setdefault("HF_TOKEN", self._hf_token)
            from fastembed import TextEmbedding

            self._model = TextEmbedding(
                model_name=self._model_name,
                cache_dir=self._cache_dir,
                threads=self._threads,
            )
            self._dimension = len(next(iter(self._model.embed(["dimension probe"]))))

    def _embed(self, texts: List[str], batch_size: int) -> np.ndarray:
        self._load_model()
        vectors = np.asarray(
            list(self._model.embed(texts, batch_size=batch_size)), dtype=np.float32
        )
        # fastembed already normalises; re-normalise defensively for parity
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        return vectors / norms

    def encode(self, texts: Union[str, List[str]]) -> np.ndarray:
        if isinstance(texts, str):
            texts = [texts]
        return self._embed(texts, batch_size=32)

    def encode_batch(
        self,
        texts: List[str],
        batch_size: int = 32,
        show_progress: bool = False,
    ) -> np.ndarray:
        return self._embed(texts, batch_size=batch_size)
