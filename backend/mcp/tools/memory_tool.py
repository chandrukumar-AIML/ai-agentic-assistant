# backend/mcp/tools/memory_tool.py
"""
MCP wrapper for Mem0 memory operations.
"""
from backend.mcp.schemas import MCPTool, MCPToolInputSchema, MCPToolCallResult, MCPContentItem

TOOL_DEFINITION = MCPTool(
    name="recall_memory",
    description=(
        "Search and retrieve memories stored about a user. "
        "Memories include: past conversation topics (episodic), "
        "user facts and preferences (semantic), "
        "and effective strategies learned (procedural). "
        "Best for: personalising responses, remembering context across sessions, "
        "retrieving what was discussed previously."
    ),
    inputSchema=MCPToolInputSchema(
        properties={
            "query": {
                "type":        "string",
                "description": "What to search for in memory.",
            },
            "user_id": {
                "type":        "string",
                "description": "User ID to retrieve memories for.",
            },
            "memory_type": {
                "type":        "string",
                "enum":        ["all", "episodic", "semantic", "procedural"],
                "description": "Type of memory to retrieve (default: all).",
                "default":     "all",
            },
            "limit": {
                "type":        "integer",
                "description": "Maximum memories to return (1-20, default 10).",
                "default":     10,
                "maximum":     20,
            },
        },
        required=["query", "user_id"],
    ),
)


async def execute(arguments: dict, workspace_slug: str = "default") -> MCPToolCallResult:
    query       = arguments.get("query", "")
    user_id     = arguments.get("user_id", "")
    memory_type = arguments.get("memory_type", "all")
    limit       = min(int(arguments.get("limit", 10)), 20)

    if not query or not user_id:
        return MCPToolCallResult(
            content=[MCPContentItem(type="text", text="Error: query and user_id are required")],
            isError=True,
        )

    try:
        from backend.memory.memory_store import (
            search_memories, get_all_memories, MemoryType
        )

        if memory_type == "all":
            memories = await get_all_memories(user_id=user_id, limit=limit)
        else:
            mem_type = MemoryType(memory_type)
            memories = await search_memories(
                query=query,
                user_id=user_id,
                memory_type=mem_type,
                limit=limit,
            )

        if not memories:
            return MCPToolCallResult(
                content=[MCPContentItem(
                    type="text",
                    text=f"No memories found for user '{user_id}'. "
                         "This may be a new user or the memory store is empty.",
                )],
            )

        # Group and format
        grouped: dict[str, list[str]] = {"episodic": [], "semantic": [], "procedural": []}
        for m in memories:
            content  = m.get("memory") or m.get("content", "")
            mem_type_str = m.get("metadata", {}).get("memory_type", "semantic")
            if mem_type_str in grouped and content:
                grouped[mem_type_str].append(content)

        lines = [f"Memories for user '{user_id}':\n"]
        type_labels = {"episodic": "Past Sessions", "semantic": "User Facts", "procedural": "Effective Strategies"}

        for t, mems in grouped.items():
            if mems:
                lines.append(f"\n**{type_labels[t]}:**")
                for mem in mems:
                    lines.append(f"  • {mem}")

        return MCPToolCallResult(
            content=[MCPContentItem(type="text", text="\n".join(lines))],
        )

    except Exception as e:
        return MCPToolCallResult(
            content=[MCPContentItem(type="text", text=f"Memory recall failed: {str(e)}")],
            isError=True,
        )