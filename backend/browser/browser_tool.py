# backend/browser/browser_tool.py
"""
Browser agent tool — wraps Playwright sessions with:
  - Domain whitelist enforcement
  - LLM-driven action planning
  - Screenshot streaming to WebSocket
  - Content extraction for agent state
"""
import asyncio
import logging
import time
from typing import AsyncGenerator, Callable

from backend.browser.playwright_client  import PlaywrightSession, BrowserActionResult
from backend.browser.domain_whitelist   import is_allowed, get_workspace_whitelist
from backend.llm.router                 import llm_router
from backend.utils.text                 import strip_code_fence
import json

logger = logging.getLogger(__name__)

# Max characters of page text to pass to the agent
MAX_CONTENT_PER_PAGE = 8_000


BROWSER_PLANNER_PROMPT = """You are a browser automation agent. Given a task and the current page state,
decide the NEXT single browser action to take.

Task: {task}
Current URL: {current_url}
Current page title: {page_title}
Current page content (truncated):
{page_content}

Actions completed so far:
{actions_taken}

Choose ONE action from:
  navigate    → go to a URL
  click       → click a CSS selector
  type        → type text into a CSS selector
  scroll      → scroll the page
  extract     → extract specific element content
  done        → task complete, return collected content

Respond with ONLY valid JSON:
{{
  "action": "navigate|click|type|scroll|extract|done",
  "params": {{
    "url": "...",          (for navigate)
    "selector": "...",     (for click/type/extract)
    "text": "...",         (for type)
    "direction": "down",   (for scroll)
    "attribute": null      (for extract — null = innerText)
  }},
  "reasoning": "why this action"
}}"""


async def run_browser_task(
    task:              str,
    start_url:         str,
    workspace_slug:    str      = "default",
    session_id:        str      = "",
    on_screenshot:     Callable | None = None,   # async callback for streaming
    max_actions:       int      = 15,
) -> dict:
    """
    Run a browser task autonomously.
    LLM plans each step, executes via Playwright, streams screenshots.

    Args:
        task:           What the agent should accomplish
        start_url:      Initial URL to navigate to
        workspace_slug: Used to get workspace whitelist
        session_id:     Browser session identifier
        on_screenshot:  Async callback(base64_png, action_description) for UI streaming
        max_actions:    Safety cap on number of browser actions

    Returns:
        dict with: success, content, actions_log, final_url, screenshots
    """
    start       = time.monotonic()
    whitelist   = await get_workspace_whitelist(workspace_slug)
    browser_session = PlaywrightSession(session_id=session_id or None)

    actions_log:   list[dict] = []
    collected_content: list[str] = []
    all_screenshots:   list[str] = []
    current_url   = ""
    page_title    = ""
    page_content  = ""

    # Validate start URL
    allowed, reason = is_allowed(start_url, whitelist)
    if not allowed:
        return {
            "success":  False,
            "error":    f"Start URL not allowed: {reason}",
            "content":  "",
            "actions_log": [],
        }

    try:
        # Navigate to start URL
        result = await browser_session.navigate(start_url, take_screenshot=True)
        if not result.success:
            return {
                "success":  False,
                "error":    result.error,
                "content":  "",
                "actions_log": [],
            }

        current_url  = result.url
        page_title   = result.title
        page_content = result.text or ""

        if result.screenshot and on_screenshot:
            await on_screenshot(result.screenshot, f"Navigated to {start_url}")
            all_screenshots.append(result.screenshot)

        actions_log.append({
            "action": "navigate", "url": start_url,
            "result": "success", "latency_ms": result.latency_ms,
        })

        # ── Agentic loop ────────────────────────────────────────────────────
        for step in range(max_actions):
            # Plan next action
            messages = [
                {
                    "role":    "system",
                    "content": "You are a precise browser automation agent. Return only JSON.",
                },
                {
                    "role": "user",
                    "content": BROWSER_PLANNER_PROMPT.format(
                        task=task,
                        current_url=current_url,
                        page_title=page_title,
                        page_content=page_content[:3000],
                        actions_taken=json.dumps(actions_log[-5:], indent=2),
                    ),
                },
            ]

            response, _ = await llm_router.complete(
                messages=messages,
                temperature=0,
                max_tokens=300,
            )

            try:
                plan    = json.loads(strip_code_fence(response if isinstance(response, str) else ""))
                action  = plan.get("action", "done")
                params  = plan.get("params", {})
                reasoning = plan.get("reasoning", "")
            except (json.JSONDecodeError, KeyError):
                logger.warning("Browser planner parse failed — stopping")
                break

            logger.info(f"Browser step {step+1}: {action} — {reasoning[:60]}")

            if action == "done":
                # Collect final page content
                if page_content:
                    collected_content.append(page_content)
                break

            # Execute action
            result: BrowserActionResult | None = None

            if action == "navigate":
                url = params.get("url", "")
                allowed, reason = is_allowed(url, whitelist)
                if not allowed:
                    actions_log.append({
                        "action": "navigate", "url": url,
                        "result": f"blocked: {reason}",
                    })
                    logger.warning(f"Browser blocked URL: {url} ({reason})")
                    continue
                result = await browser_session.navigate(url)

            elif action == "click":
                result = await browser_session.click(params.get("selector", "body"))

            elif action == "type":
                result = await browser_session.type_text(
                    params.get("selector", "input"),
                    params.get("text", ""),
                )

            elif action == "scroll":
                result = await browser_session.scroll(
                    direction=params.get("direction", "down"),
                    pixels=params.get("pixels", 500),
                )

            elif action == "extract":
                result = await browser_session.extract(
                    params.get("selector", "body"),
                    params.get("attribute"),
                )

            if result:
                if result.success:
                    current_url  = result.url  or current_url
                    page_title   = result.title or page_title
                    page_content = result.text  or ""

                    if page_content:
                        collected_content.append(page_content[:MAX_CONTENT_PER_PAGE])

                    if result.screenshot:
                        all_screenshots.append(result.screenshot)
                        if on_screenshot:
                            await on_screenshot(
                                result.screenshot,
                                f"Step {step+1}: {action} — {reasoning[:40]}"
                            )

                actions_log.append({
                    "action":     action,
                    "params":     params,
                    "reasoning":  reasoning,
                    "result":     "success" if result.success else f"error: {result.error}",
                    "latency_ms": result.latency_ms if result else 0,
                })

    finally:
        await browser_session.close()

    # Deduplicate and cap collected content
    unique_content = list(dict.fromkeys(collected_content))
    final_content  = "\n\n---\n\n".join(unique_content)[:MAX_CONTENT_PER_PAGE * 3]

    elapsed = (time.monotonic() - start) * 1000
    logger.info(
        f"Browser task complete: {len(actions_log)} actions, "
        f"{len(all_screenshots)} screenshots, {elapsed:.0f}ms"
    )

    return {
        "success":      True,
        "content":      final_content,
        "actions_log":  actions_log,
        "final_url":    current_url,
        "page_title":   page_title,
        "screenshots":  all_screenshots,
        "elapsed_ms":   elapsed,
    }