import time
import logging
from typing import Any

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from tavily import AsyncTavilyClient

from backend.agent.state import AgentState  # FIXED: wrong import path
from backend.agent.tools.base_tool import make_tool_result  # FIXED: wrong import path
from backend.config import get_settings  # FIXED: wrong import path (was `from config import get_settings`)

logger = logging.getLogger(__name__)
settings = get_settings()

# Module-level singleton — not re-created per call
_tavily_client = AsyncTavilyClient(api_key=settings.tavily_api_key)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    retry=retry_if_exception_type(Exception),
    reraise=True,
)
async def _tavily_search(query: str, max_results: int = 5) -> list[dict[str, Any]]:
    response = await _tavily_client.search(
        query=query,
        max_results=max_results,
        search_depth="advanced",
        include_raw_content=False,
        include_answer=True,
    )
    return response.get("results", [])


async def web_searcher_node(state: AgentState) -> dict:
    start = time.monotonic()

    # Last plan item is most specific subtask
    query = (
        state["plan"][-1]
        if state.get("plan")
        else state["user_query"]
    )

    try:
        results = await _tavily_search(query, max_results=5)

        content_parts = []
        sources = []

        for r in results:
            snippet = r.get("content") or r.get("raw_content") or ""
            url = r.get("url", "")
            if snippet:
                content_parts.append(f"[{url}]\n{snippet}")
                sources.append(url)

        content = "\n\n---\n\n".join(content_parts) if content_parts else "No results found."
        avg_score = (
            sum(float(r.get("score", 0.5)) for r in results) / len(results)
            if results else 0.3
        )

        result = make_tool_result(
            tool_name="web_search_tool",
            content=content,
            source=sources[0] if sources else "",
            confidence=min(avg_score, 1.0),
            metadata={"query": query, "result_count": len(results), "all_sources": sources},
        )

    except Exception as e:
        logger.error(f"Web search failed: {e}")
        result = make_tool_result(
            tool_name="web_search_tool",
            content=f"Web search unavailable: {str(e)}",
            confidence=0.0,
            metadata={"error": str(e)},
        )

    elapsed = (time.monotonic() - start) * 1000

    return {
        "tool_results": state.get("tool_results", []) + [result],
        "latency_ms":   {"web_searcher": round(elapsed, 2)},
    }