# backend/mcp/tools/graph_tool.py
"""
MCP wrapper for Neo4j knowledge graph queries.
"""
import logging
from backend.mcp.schemas import MCPTool, MCPToolInputSchema, MCPToolCallResult, MCPContentItem

logger = logging.getLogger(__name__)

TOOL_DEFINITION = MCPTool(
    name="query_knowledge_graph",
    description=(
        "Query the Neo4j knowledge graph using natural language. "
        "The graph contains: People (name, role, email), Companies (name, industry, founded), "
        "Documents (title, source, date), Topics (name, category), Events (name, date, type). "
        "Relationships: WORKS_AT, KNOWS, AUTHORED, MENTIONS, RELATED_TO, INVOLVES, OCCURRED_AT. "
        "Best for: finding connections between entities, relationship queries, "
        "organizational charts, topic associations."
    ),
    inputSchema=MCPToolInputSchema(
        properties={
            "query": {
                "type":        "string",
                "description": "Natural language question about entities and their relationships.",
            },
            "cypher": {
                "type":        "string",
                "description": "Optional: provide raw Cypher query directly (overrides natural language).",
            },
            "limit": {
                "type":        "integer",
                "description": "Maximum results to return (1-50, default 15).",
                "default":     15,
                "maximum":     50,
            },
        },
        required=["query"],
    ),
)


async def execute(arguments: dict, workspace_slug: str = "default") -> MCPToolCallResult:
    query  = arguments.get("query", "")
    cypher = arguments.get("cypher", "")
    limit  = min(int(arguments.get("limit", 15)), 50)

    if not query and not cypher:
        return MCPToolCallResult(
            content=[MCPContentItem(type="text", text="Error: query or cypher is required")],
            isError=True,
        )

    try:
        from backend.graph_db.neo4j_client import run_query

        if cypher:
            # Direct Cypher — validate it's read-only
            cypher_upper = cypher.upper()
            forbidden = {"DELETE", "DETACH DELETE", "CREATE", "SET", "REMOVE", "DROP"}
            if any(op in cypher_upper for op in forbidden):
                return MCPToolCallResult(
                    content=[MCPContentItem(
                        type="text",
                        text="Write operations not allowed via MCP. Use read-only Cypher.",
                    )],
                    isError=True,
                )
            records = await run_query(cypher + f" LIMIT {limit}")
        else:
            # Natural language → Cypher via graph tool
            from backend.agent.research_agent import ResearchAgent
            agent  = ResearchAgent()

            # Use graph querier node
            from backend.agent.state import AgentState
            from backend.agent.tools.graph_tool import _generate_cypher, _fulltext_fallback

            generated_cypher = await _generate_cypher(query)
            cypher_upper     = generated_cypher.upper()
            forbidden        = {"DELETE", "DETACH DELETE", "CREATE", "SET", "REMOVE", "DROP"}

            if any(op in cypher_upper for op in forbidden):
                records = await _fulltext_fallback(query)
            else:
                try:
                    records = await run_query(generated_cypher + f" LIMIT {limit}")
                except Exception as e:  # FIXED: bare except Exception: pass without logging
                    logger.warning(f"Generated Cypher query failed, falling back to fulltext search: {e}")
                    records = await _fulltext_fallback(query)

        if not records:
            return MCPToolCallResult(
                content=[MCPContentItem(
                    type="text",
                    text="No matching entities found in the knowledge graph.",
                )],
            )

        # Format records
        lines = []
        for i, record in enumerate(records, 1):
            parts = [f"{k}: {v}" for k, v in record.items() if v is not None]
            if parts:
                lines.append(f"{i}. {' | '.join(parts)}")

        return MCPToolCallResult(
            content=[MCPContentItem(
                type="text",
                text=f"Knowledge graph results ({len(records)} records):\n\n" + "\n".join(lines),
            )],
        )

    except Exception as e:
        return MCPToolCallResult(
            content=[MCPContentItem(type="text", text=f"Graph query failed: {str(e)}")],
            isError=True,
        )