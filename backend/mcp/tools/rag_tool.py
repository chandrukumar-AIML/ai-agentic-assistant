# backend/mcp/tools/rag_tool.py
"""
MCP wrapper for the RAG knowledge base search.
Combines FAISS + ChromaDB + HyDE + reranking.
"""
import logging
from backend.mcp.schemas import MCPTool, MCPToolInputSchema, MCPToolCallResult, MCPContentItem

logger = logging.getLogger(__name__)

TOOL_DEFINITION = MCPTool(
    name="search_knowledge_base",
    description=(
        "Search the internal knowledge base using semantic similarity. "
        "Uses HyDE (Hypothetical Document Embeddings) for improved retrieval, "
        "dual-store search (FAISS + ChromaDB), and cross-encoder reranking. "
        "Best for: finding information from ingested documents, internal knowledge, "
        "technical documentation, and research papers that have been indexed."
    ),
    inputSchema=MCPToolInputSchema(
        properties={
            "query": {
                "type":        "string",
                "description": "The search query. Be specific for best results.",
            },
            "top_k": {
                "type":        "integer",
                "description": "Number of results to return (1-10, default 5).",
                "default":     5,
                "minimum":     1,
                "maximum":     10,
            },
            "category": {
                "type":        "string",
                "description": "Filter by document category (e.g. 'legal', 'technical', 'general'). Optional.",
            },
        },
        required=["query"],
    ),
)


async def execute(arguments: dict, workspace_slug: str = "default") -> MCPToolCallResult:
    """Execute RAG search and return results formatted for MCP."""
    query    = arguments.get("query", "")
    top_k    = min(int(arguments.get("top_k", 5)), 10)
    category = arguments.get("category")

    if not query:
        return MCPToolCallResult(
            content=[MCPContentItem(type="text", text="Error: query is required")],
            isError=True,
        )

    try:
        from backend.rag.embedder    import embed_single
        from backend.rag.hyde        import generate_hypothetical_document
        from backend.rag.faiss_store import search as faiss_search
        from backend.rag.chroma_store import search as chroma_search
        from backend.rag.reranker    import rerank

        # HyDE + dual retrieval
        try:
            hypo    = await generate_hypothetical_document(query)
            h_vec   = await embed_single(hypo)
        except Exception as e:  # FIXED: bare except Exception: pass without logging
            logger.warning(f"HyDE generation failed, falling back to direct query embedding: {e}")
            h_vec   = await embed_single(query)

        q_vec          = await embed_single(query)
        faiss_results  = faiss_search(h_vec, top_k=top_k * 3)
        chroma_filter  = {"category": category} if category else None
        chroma_results = chroma_search(q_vec.tolist(), top_k=top_k * 3, where=chroma_filter)

        # Merge + rerank
        seen = {}
        for r in faiss_results + chroma_results:
            key = f"{r.get('source','')}::{r.get('chunk_idx','')}"
            if key not in seen or r.get("score", 0) > seen[key].get("score", 0):
                seen[key] = r
        candidates = list(seen.values())
        top_chunks  = rerank(query=query, candidates=candidates, top_k=top_k)

        if not top_chunks:
            return MCPToolCallResult(
                content=[MCPContentItem(
                    type="text",
                    text="No relevant documents found. Try a different query or ingest more documents.",
                )],
                isError=False,
            )

        # Format results
        parts = []
        for i, chunk in enumerate(top_chunks, 1):
            source  = chunk.get("source", "unknown")
            content = chunk.get("content") or chunk.get("document", "")
            score   = chunk.get("rerank_score", chunk.get("score", 0))
            parts.append(
                f"[{i}] Source: {source} (relevance: {score:.2f})\n{content}"
            )

        return MCPToolCallResult(
            content=[MCPContentItem(
                type="text",
                text=f"Found {len(top_chunks)} relevant chunks:\n\n" + "\n\n---\n\n".join(parts),
            )],
        )

    except Exception as e:
        return MCPToolCallResult(
            content=[MCPContentItem(type="text", text=f"RAG search failed: {str(e)}")],
            isError=True,
        )