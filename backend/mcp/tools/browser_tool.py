# backend/mcp/tools/browser_tool.py
"""
MCP wrapper for the Playwright browser agent.
"""
import asyncio
import logging
from backend.mcp.schemas import MCPTool, MCPToolInputSchema, MCPToolCallResult, MCPContentItem

logger = logging.getLogger(__name__)

_BROWSER_TASK_TIMEOUT_S = 120  # FIXED: timeout on browser task at MCP layer

TOOL_DEFINITION = MCPTool(
    name="browse_web",
    description=(
        "Navigate to a URL and extract content using a real browser (Playwright/Chromium). "
        "Handles JavaScript-rendered pages that simple HTTP requests cannot access. "
        "Can navigate, click, scroll, and extract content autonomously. "
        "Only whitelisted domains are accessible (arxiv.org, github.com, wikipedia.org, etc.). "
        "Best for: research sites, documentation, news, dynamic web apps."
    ),
    inputSchema=MCPToolInputSchema(
        properties={
            "url": {
                "type":        "string",
                "description": "Starting URL to navigate to (must be https:// or http://).",
            },
            "task": {
                "type":        "string",
                "description": "What you want to extract or accomplish on this page.",
            },
            "max_actions": {
                "type":        "integer",
                "description": "Maximum browser actions to take (1-10, default 5).",
                "default":     5,
                "minimum":     1,
                "maximum":     10,
            },
            "return_screenshot": {
                "type":        "boolean",
                "description": "Include final screenshot in response (default false).",
                "default":     False,
            },
        },
        required=["url", "task"],
    ),
)


async def execute(arguments: dict, workspace_slug: str = "default") -> MCPToolCallResult:
    url              = arguments.get("url", "")
    task             = arguments.get("task", "")
    max_actions      = min(int(arguments.get("max_actions", 5)), 10)
    return_screenshot = bool(arguments.get("return_screenshot", False))

    if not url or not task:
        return MCPToolCallResult(
            content=[MCPContentItem(type="text", text="Error: url and task are required")],
            isError=True,
        )

    try:
        from backend.browser.domain_whitelist import is_allowed
        allowed, reason = is_allowed(url)
        if not allowed:
            return MCPToolCallResult(
                content=[MCPContentItem(
                    type="text",
                    text=f"URL not allowed: {reason}\n\nAllowed domains include: "
                         "arxiv.org, github.com, wikipedia.org, stackoverflow.com, "
                         "and other research/documentation sites.",
                )],
                isError=True,
            )

        from backend.browser.browser_tool import run_browser_task
        # FIXED: added timeout to prevent indefinite hang on slow/unresponsive sites
        result = await asyncio.wait_for(
            run_browser_task(
                task=task,
                start_url=url,
                workspace_slug=workspace_slug,
                max_actions=max_actions,
            ),
            timeout=_BROWSER_TASK_TIMEOUT_S,
        )

        if not result["success"]:
            return MCPToolCallResult(
                content=[MCPContentItem(type="text", text=f"Browser error: {result.get('error')}")],
                isError=True,
            )

        content_items = [
            MCPContentItem(
                type="text",
                text=(
                    f"Page: {result.get('page_title')} ({result.get('final_url')})\n"
                    f"Actions taken: {len(result.get('actions_log', []))}\n\n"
                    f"Extracted content:\n{result.get('content', '')[:8000]}"
                ),
            )
        ]

        # Optionally include final screenshot
        if return_screenshot and result.get("screenshots"):
            last_screenshot = result["screenshots"][-1]
            content_items.append(
                MCPContentItem(
                    type="image",
                    data=last_screenshot,
                    mimeType="image/png",
                )
            )

        return MCPToolCallResult(content=content_items)

    except asyncio.TimeoutError:
        logger.error(f"Browser task timed out after {_BROWSER_TASK_TIMEOUT_S}s for url={url}")  # FIXED: log timeout
        return MCPToolCallResult(
            content=[MCPContentItem(type="text", text=f"Browser task timed out after {_BROWSER_TASK_TIMEOUT_S} seconds.")],
            isError=True,
        )
    except Exception as e:
        return MCPToolCallResult(
            content=[MCPContentItem(type="text", text=f"Browser task failed: {str(e)}")],
            isError=True,
        )