# backend/mcp/server.py
"""
MCP Server implementation.
Handles the Model Context Protocol JSON-RPC protocol over HTTP.

Supported transport: HTTP POST (Streamable HTTP) — compatible with
Claude Desktop, Cursor, and other MCP clients that support remote servers.

Protocol methods implemented:
  initialize          → server capabilities + info
  tools/list          → available tool definitions
  tools/call          → execute a tool
  ping                → health check
"""
import json
import logging
import time
from typing import Any

from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import JSONResponse, StreamingResponse

from backend.mcp.schemas import (
    MCPRequest, MCPResponse, MCPError,
    MCPInitializeResult, MCPToolsListResult,
    MCPToolCallResult, MCPContentItem,
    MCPTool,
)
from backend.api.auth import verify_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/mcp", tags=["mcp"])

# ── Tool registry ────────────────────────────────────────────────────────────

from backend.mcp.tools import (
    rag_tool, code_tool, vision_tool,
    graph_tool, browser_tool, memory_tool, search_tool,
)

_TOOL_DEFINITIONS: dict[str, MCPTool] = {
    "search_knowledge_base":  rag_tool.TOOL_DEFINITION,
    "run_python_code":        code_tool.TOOL_DEFINITION,
    "analyze_image":          vision_tool.TOOL_DEFINITION,
    "query_knowledge_graph":  graph_tool.TOOL_DEFINITION,
    "browse_web":             browser_tool.TOOL_DEFINITION,
    "recall_memory":          memory_tool.TOOL_DEFINITION,
    "web_search":             search_tool.TOOL_DEFINITION,
}

_TOOL_EXECUTORS = {
    "search_knowledge_base":  rag_tool.execute,
    "run_python_code":        code_tool.execute,
    "analyze_image":          vision_tool.execute,
    "query_knowledge_graph":  graph_tool.execute,
    "browse_web":             browser_tool.execute,
    "recall_memory":          memory_tool.execute,
    "web_search":             search_tool.execute,
}


def _make_error(id: Any, code: int, message: str) -> MCPResponse:
    return MCPResponse(
        id=id,
        error=MCPError(code=code, message=message),
    )


def _make_result(id: Any, result: Any) -> MCPResponse:
    return MCPResponse(id=id, result=result)


async def _handle_request(
    req:            MCPRequest,
    workspace_slug: str,
) -> MCPResponse:
    """Route an MCP JSON-RPC request to the correct handler."""

    # ── initialize ────────────────────────────────────────────────────────────
    if req.method == "initialize":
        return _make_result(req.id, MCPInitializeResult().dict())

    # ── ping ──────────────────────────────────────────────────────────────────
    if req.method == "ping":
        return _make_result(req.id, {})

    # ── tools/list ────────────────────────────────────────────────────────────
    if req.method == "tools/list":
        tools_list = MCPToolsListResult(
            tools=list(_TOOL_DEFINITIONS.values())
        )
        return _make_result(req.id, tools_list.dict())

    # ── tools/call ────────────────────────────────────────────────────────────
    if req.method == "tools/call":
        params    = req.params
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})

        if tool_name not in _TOOL_EXECUTORS:
            return _make_error(
                req.id, -32601,
                f"Tool not found: '{tool_name}'. "
                f"Available: {list(_TOOL_EXECUTORS.keys())}"
            )

        start    = time.monotonic()
        executor = _TOOL_EXECUTORS[tool_name]

        try:
            result: MCPToolCallResult = await executor(
                arguments=arguments,
                workspace_slug=workspace_slug,
            )
            elapsed = (time.monotonic() - start) * 1000
            logger.info(
                f"MCP tool call: {tool_name} "
                f"({'error' if result.isError else 'success'}) "
                f"in {elapsed:.0f}ms"
            )
            return _make_result(req.id, result.dict())

        except Exception as e:
            logger.error(f"MCP tool execution failed: {tool_name} — {e}", exc_info=True)
            error_result = MCPToolCallResult(
                content=[MCPContentItem(type="text", text=f"Tool execution error: {str(e)}")],
                isError=True,
            )
            return _make_result(req.id, error_result.dict())

    # ── Unknown method ────────────────────────────────────────────────────────
    return _make_error(req.id, -32601, f"Method not found: {req.method}")


# ── HTTP endpoints ────────────────────────────────────────────────────────────

@router.post("")
@router.post("/")
async def mcp_endpoint(
    request: Request,
    token:   dict = Depends(verify_token),
):
    """
    Main MCP endpoint.
    Accepts JSON-RPC requests and returns JSON-RPC responses.
    Supports both single requests and batch requests.
    """
    workspace_slug = token.get("workspace_slug", "default")

    try:
        body = await request.json()
    except Exception:
        return JSONResponse(
            status_code=400,
            content=MCPResponse(
                id=None,
                error=MCPError(code=-32700, message="Parse error: invalid JSON"),
            ).dict(),
        )

    # Batch request support
    if isinstance(body, list):
        responses = []
        for item in body:
            try:
                req = MCPRequest(**item)
                res = await _handle_request(req, workspace_slug)
                responses.append(res.dict(exclude_none=True))
            except Exception as e:
                responses.append(MCPResponse(
                    id=item.get("id"),
                    error=MCPError(code=-32603, message=str(e)),
                ).dict(exclude_none=True))
        return JSONResponse(content=responses)

    # Single request
    try:
        req = MCPRequest(**body)
    except Exception as e:
        return JSONResponse(
            content=MCPResponse(
                id=body.get("id"),
                error=MCPError(code=-32600, message=f"Invalid request: {e}"),
            ).dict(exclude_none=True),
        )

    response = await _handle_request(req, workspace_slug)
    return JSONResponse(content=response.dict(exclude_none=True))


@router.get("/tools")
async def list_tools_http(token: dict = Depends(verify_token)):
    """
    Convenience REST endpoint to list tools.
    Not part of MCP protocol — useful for debugging and documentation.
    """
    return {
        "tools":   [t.dict() for t in _TOOL_DEFINITIONS.values()],
        "count":   len(_TOOL_DEFINITIONS),
        "server":  "ai-agentic-assistant v2",
        "protocol": "MCP 2024-11-05",
    }


@router.get("/health")
async def mcp_health():
    """MCP server health check — no auth required."""
    return {
        "status":       "ok",
        "tools_count":  len(_TOOL_DEFINITIONS),
        "tool_names":   list(_TOOL_DEFINITIONS.keys()),
        "protocol":     "MCP 2024-11-05",
        "transport":    "http",
    }