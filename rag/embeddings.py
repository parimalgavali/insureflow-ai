"""Multilingual sentence embeddings for policy clauses and user questions.

Default model: intfloat/multilingual-e5-small (384 dims, CPU-friendly, DE/EN). e5 models expect
``query:`` / ``passage:`` prefixes — see the model card — so callers use ``embed_queries`` and
``embed_passages`` rather than a raw ``encode``.
"""

from __future__ import annotations

import os
from collections.abc import Sequence
from typing import Protocol

import numpy as np

DEFAULT_MODEL = "intfloat/multilingual-e5-small"
EMBEDDING_DIM = 384


class EmbedderProtocol(Protocol):
    dim: int

    def embed_passages(self, texts: Sequence[str]) -> np.ndarray: ...

    def embed_queries(self, texts: Sequence[str]) -> np.ndarray: ...


class Embedder:
    """Lazy-loading sentence-transformers wrapper; vectors are L2-normalised (cosine = dot)."""

    def __init__(self, model_name: str | None = None, batch_size: int = 32):
        self.model_name = model_name or os.environ.get("EMBEDDING_MODEL", DEFAULT_MODEL)
        self.batch_size = batch_size
        self._model = None
        self.dim = EMBEDDING_DIM

    def _load(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.model_name, device="cpu")
            self.dim = int(self._model.get_sentence_embedding_dimension())
        return self._model

    def _encode(self, texts: Sequence[str], prefix: str) -> np.ndarray:
        if not texts:
            return np.zeros((0, self.dim), dtype=np.float32)
        model = self._load()
        vectors = model.encode(
            [f"{prefix}{t}" for t in texts],
            batch_size=self.batch_size,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return np.asarray(vectors, dtype=np.float32)

    def embed_passages(self, texts: Sequence[str]) -> np.ndarray:
        return self._encode(texts, "passage: ")

    def embed_queries(self, texts: Sequence[str]) -> np.ndarray:
        return self._encode(texts, "query: ")


class BagOfWordsEmbedder:
    """Deterministic, dependency-free embedder for tests: hashed bag of lower-cased words."""

    def __init__(self, dim: int = 64):
        self.dim = dim

    def _encode(self, texts: Sequence[str]) -> np.ndarray:
        out = np.zeros((len(texts), self.dim), dtype=np.float32)
        for i, text in enumerate(texts):
            for word in text.lower().split():
                out[i, hash(word) % self.dim] += 1.0
            norm = np.linalg.norm(out[i])
            if norm:
                out[i] /= norm
        return out

    embed_passages = _encode
    embed_queries = _encode
