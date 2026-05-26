# backend/rag/embedder.py  — LOCAL embeddings via sentence-transformers (no OpenAI required)
"""
Embedder using sentence-transformers/all-MiniLM-L6-v2 (local, free, fast).
Dim = 384 (not 1536). FAISS index and ChromaDB are re-created with this dim.
Falls back gracefully if model not loaded.
"""
import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor

import numpy as np

logger = logging.getLogger(__name__)

# ── Model config ──────────────────────────────────────────────────────────────
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
EMBEDDING_DIM   = 384       # MiniLM produces 384-dim vectors

_model     = None
_executor  = ThreadPoolExecutor(max_workers=1)
_model_lock = asyncio.Lock()


def _load_model():
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            _model = SentenceTransformer(EMBEDDING_MODEL)
            logger.info("Sentence-transformer loaded: %s (dim=%d)", EMBEDDING_MODEL, EMBEDDING_DIM)
        except Exception as e:
            logger.error("Failed to load sentence-transformer: %s", e)
            _model = None
    return _model


def _encode_sync(texts: list[str]) -> np.ndarray:
    """Runs in thread executor — SentenceTransformer.encode is blocking."""
    model = _load_model()
    if model is None:
        # Return zero vectors as last-resort fallback
        return np.zeros((len(texts), EMBEDDING_DIM), dtype=np.float32)
    return model.encode(texts, normalize_embeddings=True, show_progress_bar=False).astype(np.float32)


async def embed_texts(texts: list[str]) -> np.ndarray:
    """
    Embed a list of texts locally using sentence-transformers.
    Returns float32 numpy array of shape (len(texts), EMBEDDING_DIM).
    """
    if not texts:
        return np.empty((0, EMBEDDING_DIM), dtype=np.float32)

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_executor, _encode_sync, texts)


async def embed_single(text: str) -> np.ndarray:
    """Convenience wrapper. Returns shape (EMBEDDING_DIM,)."""
    result = await embed_texts([text])
    return result[0]
