import asyncio
import json
import logging
import numpy as np
import faiss
from pathlib import Path
from backend.config import get_settings  # FIXED: use package-relative import

logger = logging.getLogger(__name__)
settings = get_settings()

INDEX_PATH    = Path(settings.faiss_index_path)
META_PATH     = INDEX_PATH.with_suffix(".meta.json")
EMBEDDING_DIM = 384   # sentence-transformers/all-MiniLM-L6-v2 (was 1536 for OpenAI)

_index:      faiss.Index | None = None
_metadata:   list[dict]         = []
_write_lock: asyncio.Lock | None = None


def _get_lock() -> asyncio.Lock:
    global _write_lock
    if _write_lock is None:
        _write_lock = asyncio.Lock()
    return _write_lock


def _ensure_dir():
    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)


def load_or_create() -> tuple[faiss.Index, list[dict]]:
    global _index, _metadata
    if _index is not None:
        return _index, _metadata

    _ensure_dir()

    if INDEX_PATH.exists() and META_PATH.exists():
        _index    = faiss.read_index(str(INDEX_PATH))
        _metadata = json.loads(META_PATH.read_text())
        logger.info(f"FAISS: loaded {_index.ntotal} vectors from {INDEX_PATH}")
    else:
        _index    = faiss.IndexFlatIP(EMBEDDING_DIM)
        _metadata = []
        logger.info("FAISS: created fresh index")

    return _index, _metadata


def save():
    if _index is None:
        return
    _ensure_dir()
    faiss.write_index(_index, str(INDEX_PATH))
    META_PATH.write_text(json.dumps(_metadata, ensure_ascii=False, indent=2))
    logger.info(f"FAISS: saved {_index.ntotal} vectors")


async def add_vectors(vectors: np.ndarray, metadata_list: list[dict]):
    """Thread-safe vector addition with asyncio lock."""
    async with _get_lock():
        index, meta = load_or_create()
        faiss.normalize_L2(vectors)
        index.add(vectors)
        meta.extend(metadata_list)
        save()


def search(query_vector: np.ndarray, top_k: int = 20) -> list[dict]:
    index, meta = load_or_create()
    if index.ntotal == 0:
        logger.warning("FAISS index is empty")
        return []

    qv = query_vector.reshape(1, -1).astype(np.float32)
    faiss.normalize_L2(qv)
    k = min(top_k, index.ntotal)
    scores, indices = index.search(qv, k)

    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx == -1:
            continue
        entry = {**meta[idx], "score": float(score)}
        entry.setdefault("source", "unknown")  # FIXED: ensure source key always present
        results.append(entry)
    return results


def get_index_size() -> int:
    index, _ = load_or_create()
    return index.ntotal