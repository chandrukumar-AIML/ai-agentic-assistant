"""
Shared helper for creating ToolResult dicts.
All tool nodes should use make_tool_result() for consistent output shape.
"""
from typing import Any


def make_tool_result(
    tool_name:  str,
    content:    str,
    source:     str = "",
    confidence: float = 0.5,
    metadata:   dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return a ToolResult-compatible dict."""
    return {
        "tool_name":  tool_name,
        "content":    content,
        "source":     source,
        "confidence": max(0.0, min(1.0, confidence)),
        "metadata":   metadata or {},
    }
