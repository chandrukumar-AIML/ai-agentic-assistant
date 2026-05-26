# backend/mcp/tools/search_tool.py
"""
MCP wrapper for Tavily web search.
"""
import asyncio
import logging
from backend.mcp.schemas import MCPTool, MCPToolInputSchema, MCPToolCallResult, MCPContentItem

logger = logging.getLogger(__name__)

_SEARCH_TIMEOUT_S = 30  # FIXED: timeout on external Tavily search call

TOOL_DEFINITION = MCPTool(
    name="web_search",
    description=(
        "Search the web for current information using Tavily's AI-powered search. "
        "Returns relevant snippets and source URLs. "
        "Best for: current events, recent news, factual lookups, "
        "information not available in the knowledge base."
    ),
    inputSchema=MCPToolInputSchema(
        properties={
            "query": {
                "type":        "string",
                "description": "Search query. Be specific for better results.",
            },
            "max_results": {
                "type":        "integer",
                "description": "Number of results to return (1-10, default 5).",
                "default":     5,
                "minimum":     1,
                "maximum":     10,
            },
            "search_depth": {
                "type":        "string",
                "enum":        ["basic", "advanced"],
                "description": "Search depth. 'advanced' is more thorough but slower.",
                "default":     "basic",
            },
        },
        required=["query"],
    ),
)


async def execute(arguments: dict, workspace_slug: str = "default") -> MCPToolCallResult:
    query        = arguments.get("query", "")
    max_results  = min(int(arguments.get("max_results", 5)), 10)
    search_depth = arguments.get("search_depth", "basic")

    if not query:
        return MCPToolCallResult(
            content=[MCPContentItem(type="text", text="Error: query is required")],
            isError=True,
        )

    try:
        from backend.agent.tools.web_search_tool import _tavily_search

        # FIXED: added timeout to prevent indefinite hang on external Tavily API
        results = await asyncio.wait_for(
            _tavily_search(query, max_results=max_results),
            timeout=_SEARCH_TIMEOUT_S,
        )

        if not results:
            return MCPToolCallResult(
                content=[MCPContentItem(type="text", text="No results found.")],
            )

        lines = [f"Web search results for: '{query}'\n"]
        for i, r in enumerate(results, 1):
            url     = r.get("url", "")
            content = r.get("content", "")[:500]
            score   = r.get("score", 0)
            lines.append(f"\n[{i}] {url} (relevance: {score:.2f})\n{content}")

        return MCPToolCallResult(
            content=[MCPContentItem(type="text", text="\n".join(lines))],
        )

    except asyncio.TimeoutError:
        logger.error(f"Web search timed out after {_SEARCH_TIMEOUT_S}s for query='{query}'")  # FIXED: log timeout
        return MCPToolCallResult(
            content=[MCPContentItem(type="text", text=f"Web search timed out after {_SEARCH_TIMEOUT_S} seconds.")],
            isError=True,
        )
    except Exception as e:
        return MCPToolCallResult(
            content=[MCPContentItem(type="text", text=f"Web search failed: {str(e)}")],
            isError=True,
        )