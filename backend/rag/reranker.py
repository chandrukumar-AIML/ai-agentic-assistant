"""
FlashRank reranker — fast cross-encoder reranking with no GPU required.
Uses a singleton ranker instance loaded once at startup.
"""
import logging
import tempfile
from pathlib import Path
from typing import Any

from flashrank import Ranker, RerankRequest

logger = logging.getLogger(__name__)

_ranker: Ranker | None = None


def get_ranker() -> Ranker:
    """Return the singleton Ranker, loading it on first call."""
    global _ranker
    if _ranker is None:
        cache_dir = Path(tempfile.gettempdir()) / "flashrank"
        cache_dir.mkdir(parents=True, exist_ok=True)
        _ranker = Ranker(model_name="ms-marco-MiniLM-L-12-v2", cache_dir=str(cache_dir))
        logger.info(f"FlashRank ranker loaded: ms-marco-MiniLM-L-12-v2, cache={cache_dir}")
    return _ranker


def rerank(
    query: str,
    candidates: list[dict[str, Any]],
    top_k: int = 5,
) -> list[dict[str, Any]]:
    """
    Rerank candidates using FlashRank cross-encoder.

    Args:
        query:      The user query string.
        candidates: List of dicts with at least a 'content' or 'document' key.
        top_k:      Number of top results to return.

    Returns:
        Top-k candidates with an added 'rerank_score' key, sorted descending.
    """
    if not candidates:
        return []

    ranker = get_ranker()

    # FlashRank expects passages as list of dicts with 'text' key
    passages = [
        {
            "id":   i,
            "text": c.get("content") or c.get("document", ""),
            "meta": c,
        }
        for i, c in enumerate(candidates)
    ]

    try:
        request = RerankRequest(query=query, passages=passages)
        results = ranker.rerank(request)

        reranked = []
        for r in results[:top_k]:
            original = r.get("meta", {})
            original["rerank_score"] = float(r.get("score", 0.0))
            reranked.append(original)

        return reranked

    except Exception as e:
        logger.warning(f"Reranking failed, returning candidates unranked: {e}")
        # Fallback: return top_k by original score
        sorted_candidates = sorted(
            candidates,
            key=lambda c: c.get("score", 0.0),
            reverse=True,
        )
        for c in sorted_candidates[:top_k]:
            c.setdefault("rerank_score", c.get("score", 0.0))
        return sorted_candidates[:top_k]
