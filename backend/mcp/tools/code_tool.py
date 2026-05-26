# backend/mcp/tools/code_tool.py
"""
MCP wrapper for Python code execution in sandbox.
"""
from backend.mcp.schemas import MCPTool, MCPToolInputSchema, MCPToolCallResult, MCPContentItem

TOOL_DEFINITION = MCPTool(
    name="run_python_code",
    description=(
        "Execute Python code in a secure sandbox and return the output. "
        "Supports: standard library, numpy, basic math operations. "
        "Restrictions: no file system access, no network calls, no subprocess. "
        "Best for: calculations, data transformations, algorithm testing, "
        "quick prototypes, and verifying code correctness."
    ),
    inputSchema=MCPToolInputSchema(
        properties={
            "code": {
                "type":        "string",
                "description": "Python code to execute. Use print() to produce output.",
            },
            "timeout_seconds": {
                "type":        "integer",
                "description": "Maximum execution time in seconds (1-30, default 10).",
                "default":     10,
                "minimum":     1,
                "maximum":     30,
            },
        },
        required=["code"],
    ),
)


async def execute(arguments: dict, workspace_slug: str = "default") -> MCPToolCallResult:
    code    = arguments.get("code", "").strip()
    timeout = min(int(arguments.get("timeout_seconds", 10)), 30)

    if not code:
        return MCPToolCallResult(
            content=[MCPContentItem(type="text", text="Error: code is required")],
            isError=True,
        )

    try:
        import asyncio
        from backend.agent.tools.code_runner_tool import _run_sandboxed

        output, error = await asyncio.wait_for(
            asyncio.to_thread(_run_sandboxed, code),
            timeout=timeout,
        )

        if error:
            return MCPToolCallResult(
                content=[MCPContentItem(
                    type="text",
                    text=f"Execution error:\n```\n{error}\n```",
                )],
                isError=True,
            )

        result_text = output if output else "Code executed successfully (no output)."
        return MCPToolCallResult(
            content=[MCPContentItem(
                type="text",
                text=f"Output:\n```\n{result_text}\n```",
            )],
        )

    except asyncio.TimeoutError:
        return MCPToolCallResult(
            content=[MCPContentItem(
                type="text",
                text=f"Execution timed out after {timeout} seconds.",
            )],
            isError=True,
        )
    except Exception as e:
        return MCPToolCallResult(
            content=[MCPContentItem(type="text", text=f"Sandbox error: {str(e)}")],
            isError=True,
        )