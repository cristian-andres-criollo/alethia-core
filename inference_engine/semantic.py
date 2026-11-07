"""
Capa semántica multilingüe compartida (Aletheia 2.0).

Usa embeddings de oraciones (intfloat/multilingual-e5-small, ~100 idiomas incl. bn, sw, jv)
para comparar textos por significado en lugar de palabras clave. El modelo se carga una
sola vez y de forma perezosa; si no está disponible, `available()` devuelve False y los
componentes que dependen de él caen a su versión léxica (y lo informan).
"""
from __future__ import annotations

import os
import threading

MODEL_NAME = os.getenv("ALETHEIA_EMBED_MODEL", "intfloat/multilingual-e5-small")

_lock = threading.Lock()
_model = None
_load_error: str | None = None


def _load():
    global _model, _load_error
    with _lock:
        if _model is not None or _load_error is not None:
            return
        try:
            from sentence_transformers import SentenceTransformer
            _model = SentenceTransformer(MODEL_NAME, device="cpu")
        except Exception as e:  # sin red, sin modelo, sin torch...
            _load_error = f"{type(e).__name__}: {e}"


def available() -> bool:
    _load()
    return _model is not None


def load_error() -> str | None:
    _load()
    return _load_error


def embed(texts: list[str]):
    """Embeddings normalizados (numpy, shape [n, d]). Prefijo 'query: ' requerido por e5."""
    _load()
    if _model is None:
        raise RuntimeError(f"Modelo semántico no disponible: {_load_error}")
    return _model.encode([f"query: {t}" for t in texts], normalize_embeddings=True,
                         batch_size=32, show_progress_bar=False)


class PrototypeMatcher:
    """Similitud coseno máxima de un texto contra un conjunto de prototipos."""

    def __init__(self, prototypes: list[str]):
        self.prototypes = list(prototypes)
        self._emb = None

    def _ensure(self):
        if self._emb is None:
            self._emb = embed(self.prototypes)

    def scores(self, texts: list[str]):
        self._ensure()
        return (embed(texts) @ self._emb.T).max(axis=1)

    def score(self, text: str) -> float:
        return float(self.scores([text])[0])
