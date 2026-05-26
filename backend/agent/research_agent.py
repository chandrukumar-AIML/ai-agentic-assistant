# backend/agents/research_agent.py
"""
Research Agent: web search + RAG + Neo4j knowledge graph.
Best for: factual queries, document retrieval, entity relationships.
"""
import time
import logging
from typing import Any

from backend.agent.base_agent    import BaseWorkerAgent, WorkerResult
from backend.agent.tools.web_search_tool import _tavily_search
from backend.agent.tools.base_tool       import make_tool_result
from backend.rag.embedder                import embed_single
from backend.rag.hyde                    import generate_hypothetical_document
from backend.rag.faiss_store             import search as faiss_search
from backend.rag.chroma_store            import search as chroma_search
from backend.rag.reranker                import rerank
from backend.graph_db.neo4j_client       import run_query
from backend.utils.text                  import deduplicate_ordered

logger = logging.getLogger(__name__)


class ResearchAgent(BaseWorkerAgent):
    name        = "research_agent"
    description = (
        "Expert at finding information from web, internal documents, "
        "and knowledge graph. Best for factual queries, research, "
        "multi-source synthesis, and entity relationship questions."
    )

    @property
    def system_prompt(self) -> str:
        return """You are a Research Specialist Agent. Your job is to find, verify, and synthesise information from multiple sources.

You have access to:
- Web search (Tavily) for current information
- Internal knowledge base (RAG) for ingested documents
- Knowledge graph (Neo4j) for entity relationships

Your response must:
1. Cite every claim with its source
2. Distinguish between web results and internal documents
3. Flag any conflicting information between sources
4. Synthesise a coherent answer — not just list sources
5. Include confidence level based on source quality

Be thorough but concise. Prefer primary sources."""

    async def run(
        self,
        query:          str,
        context:        dict[str, Any],
        memory_context: str = "",
    ) -> WorkerResult:
        start   = time.monotonic()
        sources = []
        parts   = []

        # ── 1. Web search ──────────────────────────────────────────────────
        try:
            web_results = await _tavily_search(query, max_results=4)
            if web_results:
                web_parts = []
                for r in web_results:
                    url     = r.get("url", "")
                    snippet = r.get("content", "")[:400]
                    if snippet:
                        web_parts.append(f"[Web: {url}]\n{snippet}")
                        sources.append(url)
                parts.append("=== Web Search ===\n" + "\n\n".join(web_parts))
        except Exception as e:
            logger.warning(f"Research agent web search failed: {e}")

        # ── 2. RAG retrieval ───────────────────────────────────────────────
        try:
            hypothetical  = await generate_hypothetical_document(query)
            hyde_vector   = await embed_single(hypothetical)
            query_vector  = await embed_single(query)
            faiss_results = faiss_search(hyde_vector, top_k=15)
            chroma_results = chroma_search(query_vector.tolist(), top_k=15)

            # Merge + deduplicate
            seen = {}
            for r in faiss_results + chroma_results:
                key = f"{r.get('source','')}::{r.get('chunk_idx','')}"
                if key not in seen or r.get("score", 0) > seen[key].get("score", 0):
                    seen[key] = r
            candidates = list(seen.values())

            if candidates:
                top_chunks = rerank(query=query, candidates=candidates, top_k=4)
                rag_parts  = []
                for chunk in top_chunks:
                    src  = chunk.get("source", "internal")
                    text = chunk.get("content") or chunk.get("document", "")
                    rag_parts.append(f"[Doc: {src}]\n{text[:400]}")
                    sources.append(src)
                parts.append("=== Knowledge Base ===\n" + "\n\n".join(rag_parts))
        except Exception as e:
            logger.warning(f"Research agent RAG failed: {e}")

        # ── 3. Neo4j graph query ───────────────────────────────────────────
        try:
            graph_cypher = f"""
            CALL db.index.fulltext.queryNodes('entity_search', $term)
            YIELD node, score
            RETURN labels(node)[0] AS label, node.name AS name, score
            ORDER BY score DESC LIMIT 5
            """
            # Extract key terms from query (first 3 capitalised words)
            import re
            terms = re.findall(r'\b[A-Z][a-zA-Z]+\b', query)[:3]
            if terms:
                search_term = " OR ".join(terms)
                graph_results = await run_query(graph_cypher, {"term": search_term})
                if graph_results:
                    graph_text = "\n".join(
                        f"  • {r.get('label','')}: {r.get('name','')}"
                        for r in graph_results
                    )
                    parts.append(f"=== Knowledge Graph ===\n{graph_text}")
                    sources.append("neo4j")
        except Exception as e:
            logger.warning(f"Research agent graph query failed: {e}")

        if not parts:
            return WorkerResult(
                worker_name="research_agent",
                content="No relevant information found from any source.",
                confidence=0.1,
                latency_ms=(time.monotonic() - start) * 1000,
            )

        # ── 4. Synthesise with LLM ─────────────────────────────────────────
        raw_context = "\n\n".join(parts)
        system      = self.system_prompt + (f"\n{memory_context}" if memory_context else "")
        user_prompt = (
            f"Query: {query}\n\n"
            f"Sources:\n{raw_context}\n\n"
            f"Synthesise a comprehensive answer with citations."
        )

        answer = await self._call_llm(
            user_content=user_prompt,
            system_content=system,
            temperature=0.2,
            max_tokens=1500,
        )

        return WorkerResult(
            worker_name="research_agent",
            content=answer,
            sources=deduplicate_ordered(sources),
            confidence=0.85,
            metadata={
                "web_results":   len(web_results) if 'web_results' in dir() else 0,
                "rag_chunks":    len(candidates)  if 'candidates'  in dir() else 0,
            },
            latency_ms=(time.monotonic() - start) * 1000,
        )