import time
import logging

from backend.agent.state import AgentState  # FIXED: wrong import path
from backend.agent.tools.base_tool import make_tool_result  # FIXED: wrong import path
from backend.rag.embedder import embed_single  # FIXED: wrong import path
from backend.rag.hyde import generate_hypothetical_document  # FIXED: wrong import path
from backend.rag.faiss_store import search as faiss_search  # FIXED: wrong import path
from backend.rag.chroma_store import search as chroma_search  # FIXED: wrong import path
from backend.rag.reranker import rerank  # FIXED: wrong import path

logger = logging.getLogger(__name__)


def _merge_and_deduplicate(
    faiss_results:  list[dict],
    chroma_results: list[dict],
) -> list[dict]:
    seen: dict[str, dict] = {}
    for r in faiss_results + chroma_results:
        key = f"{r.get('source', '')}::{r.get('chunk_idx', r.get('id', ''))}"
        if key not in seen or r.get("score", 0) > seen[key].get("score", 0):
            seen[key] = r
    return list(seen.values())


def _format_chunks_for_output(chunks: list[dict]) -> str:
    parts = []
    for i, chunk in enumerate(chunks, 1):
        source = chunk.get("source", "unknown")
        text   = chunk.get("content") or chunk.get("document", "")
        score  = chunk.get("rerank_score", chunk.get("score", 0))
        parts.append(f"[{i}] (source: {source}, score: {score:.3f})\n{text}")
    return "\n\n".join(parts)


async def rag_retriever_node(state: AgentState) -> dict:
    """
    Full RAG pipeline:
    1. HyDE: generate hypothetical answer → embed it (falls back to raw query on failure)
    2. Dual retrieval: FAISS (top-20) + ChromaDB (top-20)
    3. Merge + deduplicate
    4. FlashRank rerank → top-5
    5. Return formatted chunks as ToolResult
    """
    start = time.monotonic()
    query = state["user_query"]

    try:
        # Step 1: HyDE with graceful fallback
        try:
            hypothetical_doc = await generate_hypothetical_document(query)
            hyde_vector = await embed_single(hypothetical_doc)
        except Exception as e:
            logger.warning(f"HyDE failed, falling back to raw query embedding: {e}")
            hypothetical_doc = query
            hyde_vector = await embed_single(query)

        query_vector = await embed_single(query)

        # Step 2: Dual retrieval
        faiss_results  = faiss_search(hyde_vector, top_k=20)
        chroma_results = chroma_search(query_vector.tolist(), top_k=20, where=None)

        # Step 3: Merge
        candidates = _merge_and_deduplicate(faiss_results, chroma_results)
        logger.info(f"RAG: {len(candidates)} candidates after merge")

        if not candidates:
            result = make_tool_result(
                tool_name="rag_tool",
                content=(
                    "No relevant documents found in the knowledge base. "
                    "Consider ingesting documents via the /ingest endpoint."
                ),
                confidence=0.1,
                metadata={"empty_index": True},
            )
        else:
            # Step 4: Rerank
            top_chunks = rerank(query=query, candidates=candidates, top_k=5)

            # Step 5: Format
            content   = _format_chunks_for_output(top_chunks)
            top_source = top_chunks[0].get("source", "") if top_chunks else ""
            avg_score  = (
                sum(c.get("rerank_score", 0) for c in top_chunks) / len(top_chunks)
                if top_chunks else 0.0
            )

            # Honest confidence — no artificial +0.3 inflation
            result = make_tool_result(
                tool_name="rag_tool",
                content=content,
                source=top_source,
                confidence=min(avg_score, 1.0),
                metadata={
                    "hypothetical_doc": hypothetical_doc[:200],
                    "faiss_hits":       len(faiss_results),
                    "chroma_hits":      len(chroma_results),
                    "candidates":       len(candidates),
                    "returned":         len(top_chunks),
                    # dict.fromkeys preserves insertion order (vs set())
                    "all_sources": list(dict.fromkeys(
                        c.get("source", "") for c in top_chunks
                    )),
                },
            )

    except Exception as e:
        logger.error(f"RAG pipeline failed: {e}", exc_info=True)
        result = make_tool_result(
            tool_name="rag_tool",
            content=f"RAG retrieval failed: {str(e)}",
            confidence=0.0,
            metadata={"error": str(e)},
        )

    elapsed = (time.monotonic() - start) * 1000
    return {
        "tool_results": state.get("tool_results", []) + [result],
        "latency_ms":   {"rag_retriever": round(elapsed, 2)},
    }