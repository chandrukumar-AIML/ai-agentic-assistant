# backend/mcp/schemas.py
"""
MCP protocol types.
Based on the Model Context Protocol specification:
https://spec.modelcontextprotocol.io/

We implement the core subset needed for tool calling:
  - tools/list
  - tools/call
  - server info
"""
from __future__ import annotations
from typing import Any, Optional, Literal
from pydantic import BaseModel


# ── MCP JSON-RPC base ────────────────────────────────────────────────────────

class MCPRequest(BaseModel):
    jsonrpc: str      = "2.0"
    id:      Any      = None
    method:  str
    params:  dict     = {}


class MCPError(BaseModel):
    code:    int
    message: str
    data:    Any = None


class MCPResponse(BaseModel):
    jsonrpc: str         = "2.0"
    id:      Any         = None
    result:  Any         = None
    error:   Optional[MCPError] = None


# ── Tool schemas ─────────────────────────────────────────────────────────────

class MCPToolInputSchema(BaseModel):
    """JSON Schema for a tool's input parameters."""
    type:       str              = "object"
    properties: dict[str, Any]  = {}
    required:   list[str]       = []


class MCPTool(BaseModel):
    """A single MCP tool definition."""
    name:        str
    description: str
    inputSchema: MCPToolInputSchema


class MCPToolsListResult(BaseModel):
    tools: list[MCPTool]


# ── Tool call ────────────────────────────────────────────────────────────────

class MCPToolCallParams(BaseModel):
    name:      str
    arguments: dict[str, Any] = {}


class MCPContentItem(BaseModel):
    type:     Literal["text", "image", "resource"]
    text:     Optional[str]   = None
    data:     Optional[str]   = None    # base64 for images
    mimeType: Optional[str]   = None


class MCPToolCallResult(BaseModel):
    content:    list[MCPContentItem]
    isError:    bool = False


# ── Server info ──────────────────────────────────────────────────────────────

class MCPServerInfo(BaseModel):
    name:    str = "ai-agentic-assistant"
    version: str = "2.0.0"


class MCPCapabilities(BaseModel):
    tools: dict = {"listChanged": False}


class MCPInitializeResult(BaseModel):
    protocolVersion: str              = "2024-11-05"
    capabilities:    MCPCapabilities  = MCPCapabilities()
    serverInfo:      MCPServerInfo    = MCPServerInfo()