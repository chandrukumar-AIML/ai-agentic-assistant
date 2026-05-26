from __future__ import annotations
import logging
import threading  # FIXED: added for thread-safe lazy init lock
from typing import Any, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
from backend.config import get_settings  # FIXED: wrong import path — was `config`, must be `backend.config`

logger = logging.getLogger(__name__)
settings = get_settings()

COLLECTION_NAME = "agent_knowledge"

_client:     Optional[Any]                   = None
_collection: Optional[chromadb.Collection]  = None
_init_lock   = threading.Lock()  # FIXED: prevents double-init race when multiple threads call get_collection() simultaneously


def get_collection() -> chromadb.Collection:
    global _client, _collection
    if _collection is not None:
        return _collection

    with _init_lock:  # FIXED: thread-safe double-checked locking
        if _collection is not None:  # FIXED: re-check after acquiring lock
            return _collection

        # Host and port from config — overridden in Docker to use container name
        _client = chromadb.HttpClient(
            host=settings.chroma_host,
            port=settings.chroma_port,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        _collection = _client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(
            f"ChromaDB: collection '{COLLECTION_NAME}' ready "
            f"({_collection.count()} docs) at {settings.chroma_host}:{settings.chroma_port}"
        )
    return _collection


def add_documents(
    ids:        list[str],
    embeddings: list[list[float]],
    documents:  list[str],
    metadatas:  list[dict],
):
    collection = get_collection()
    collection.add(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)
    logger.info(f"ChromaDB: added {len(ids)} documents")


def search(
    query_embedding: list[float],
    top_k:           int = 20,
    where:           dict | None = None,
) -> list[dict]:
    collection = get_collection()
    if collection.count() == 0:
        logger.warning("ChromaDB collection is empty")
        return []

    query_params: dict = {
        "query_embeddings": [query_embedding],
        "n_results":        min(top_k, collection.count()),
        "include":          ["documents", "metadatas", "distances"],
    }
    if where:
        query_params["where"] = where

    results = collection.query(**query_params)
    output = []
    for i, doc_id in enumerate(results["ids"][0]):
        output.append({
            "id":       doc_id,
            "content":  results["documents"][0][i],
            "metadata": results["metadatas"][0][i],
            "score":    1.0 - results["distances"][0][i],
        })
    return output


def get_count() -> int:
    """Return document count, or 0 if ChromaDB server is unreachable."""
    try:
        return get_collection().count()
    except Exception as e:
        logger.warning("ChromaDB unreachable — returning 0: %s", e)
        return 0