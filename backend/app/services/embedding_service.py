"""Sentence-Transformer embedding service.

The model is loaded ONCE (lazily, thread-safe) and reused for every request.

`all-MiniLM-L6-v2` truncates input at ~256 word-pieces, so long resumes would silently lose
their tail. `embed_document` therefore splits text into overlapping word windows, embeds each
chunk and mean-pools the (normalised) chunk vectors.
"""
import logging
import threading
from typing import Optional, Protocol

import numpy as np

from app.core.config import get_settings
from app.core.exceptions import ModelUnavailableError

logger = logging.getLogger(__name__)


class Encoder(Protocol):
    def encode(self, texts: list[str]) -> np.ndarray: ...


class SentenceTransformerEncoder:
    """Lazy singleton wrapper around SentenceTransformer."""

    def __init__(self, model_name: str):
        self.model_name = model_name
        self._model = None
        self._lock = threading.Lock()
        self.load_error: Optional[str] = None

    @property
    def loaded(self) -> bool:
        return self._model is not None

    def load(self):
        if self._model is not None:
            return self._model
        with self._lock:
            if self._model is None:
                try:
                    from sentence_transformers import SentenceTransformer

                    logger.info("Loading embedding model '%s' (first use)...", self.model_name)
                    self._model = SentenceTransformer(self.model_name)
                    self.load_error = None
                    logger.info("Embedding model initialised")
                except Exception as exc:  # network failure, missing package, corrupt cache...
                    self.load_error = exc.__class__.__name__
                    logger.error("Embedding model failed to load: %s", exc.__class__.__name__)
                    raise ModelUnavailableError() from exc
        return self._model

    def encode(self, texts: list[str]) -> np.ndarray:
        model = self.load()
        return np.asarray(model.encode(texts, normalize_embeddings=True, show_progress_bar=False), dtype=np.float32)


class EmbeddingService:
    def __init__(self, encoder: Encoder, chunk_words: int = 180, overlap_words: int = 30):
        self.encoder = encoder
        self.chunk_words = chunk_words
        self.overlap_words = overlap_words

    # ---------------------------------------------------------------- basics
    def embed_texts(self, texts: list[str]) -> np.ndarray:
        """Batch-encode short texts (lines/sentences). Returns an (n, d) array of unit vectors."""
        if not texts:
            return np.zeros((0, 0), dtype=np.float32)
        return _normalize(np.asarray(self.encoder.encode(texts), dtype=np.float32))

    def embed_document(self, text: str) -> np.ndarray:
        chunks = self._chunk(text)
        vectors = self.embed_texts(chunks)
        return _normalize(vectors.mean(axis=0, keepdims=True))[0]

    def _chunk(self, text: str) -> list[str]:
        words = text.split()
        if not words:
            return [""]
        step = max(1, self.chunk_words - self.overlap_words)
        return [" ".join(words[i:i + self.chunk_words]) for i in range(0, len(words), step)
                if i == 0 or i + self.overlap_words < len(words)]

    # ------------------------------------------------------------- similarity
    @staticmethod
    def cosine(a: np.ndarray, b: np.ndarray) -> float:
        """Cosine similarity of two vectors (robust to un-normalised input)."""
        na, nb = np.linalg.norm(a), np.linalg.norm(b)
        if na == 0 or nb == 0:
            return 0.0
        return float(np.dot(a, b) / (na * nb))

    @property
    def status(self) -> dict:
        enc = self.encoder
        return {
            "model": getattr(enc, "model_name", enc.__class__.__name__),
            "loaded": getattr(enc, "loaded", True),
            "error": getattr(enc, "load_error", None),
        }


def _normalize(m: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(m, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return m / norms


_service: Optional[EmbeddingService] = None
_service_lock = threading.Lock()


def get_embedding_service() -> EmbeddingService:
    """Process-wide singleton (also used as a FastAPI dependency; tests override it)."""
    global _service
    if _service is None:
        with _service_lock:
            if _service is None:
                _service = EmbeddingService(SentenceTransformerEncoder(get_settings().embedding_model_name))
    return _service
