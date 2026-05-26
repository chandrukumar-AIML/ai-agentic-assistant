# playwright-service/server.py
"""
Isolated Playwright execution service.
Runs in a Docker container separate from the main FastAPI backend.
Accepts browser commands, executes them, returns results.

Security:
- Runs as non-root user
- No access to host filesystem
- Domain whitelist enforced at API level (before reaching here)
- Page JS can't escape the container
"""
import asyncio
import base64
import logging
import time
from contextlib import asynccontextmanager
from typing import Optional, Literal

from fastapi          import FastAPI, HTTPException
from pydantic         import BaseModel
from playwright.async_api import (
    async_playwright,
    Browser, BrowserContext, Page,
    PlaywrightContextManager,
)
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Global browser instance — reused across requests
_playwright_mgr: PlaywrightContextManager | None = None
_browser:        Browser | None                   = None

# Limits
MAX_PAGE_TEXT_CHARS  = 15_000   # cap content returned to agent
NAVIGATION_TIMEOUT_MS = 30_000  # 30 seconds
ACTION_TIMEOUT_MS     =  5_000  # 5 seconds per click/type


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _playwright_mgr, _browser
    _playwright_mgr = async_playwright()
    pw       = await _playwright_mgr.__aenter__()
    _browser = await pw.chromium.launch(
        headless=True,
        args=[
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--disable-extensions",
            "--disable-background-networking",
            "--no-first-run",
            "--no-zygote",
        ],
    )
    logger.info("Playwright Chromium browser ready")
    yield
    await _browser.close()
    await _playwright_mgr.__aexit__(None, None, None)
    logger.info("Playwright browser closed")


app = FastAPI(title="Playwright Browser Service", lifespan=lifespan)


# ── Request / Response models ────────────────────────────────────────────────

class NavigateRequest(BaseModel):
    url:              str
    wait_for:         Literal["load", "networkidle", "domcontentloaded"] = "domcontentloaded"
    timeout_ms:       int  = NAVIGATION_TIMEOUT_MS
    take_screenshot:  bool = True
    extract_text:     bool = True
    extract_links:    bool = False


class ClickRequest(BaseModel):
    selector:         str
    take_screenshot:  bool = True
    timeout_ms:       int  = ACTION_TIMEOUT_MS


class TypeRequest(BaseModel):
    selector:         str
    text:             str
    clear_first:      bool = True
    take_screenshot:  bool = False


class ScrollRequest(BaseModel):
    direction:   Literal["up", "down", "top", "bottom"] = "down"
    pixels:      int  = 500


class ExtractRequest(BaseModel):
    selector:    str
    attribute:   Optional[str] = None   # None = innerText


class BrowserResult(BaseModel):
    success:     bool
    screenshot:  Optional[str] = None   # base64 PNG
    text:        Optional[str] = None   # page text (capped)
    links:       list[str]     = []
    title:       str           = ""
    url:         str           = ""
    error:       Optional[str] = None
    latency_ms:  float         = 0.0


# ── Session management (one context per session) ─────────────────────────────

_sessions: dict[str, tuple[BrowserContext, Page]] = {}


async def _get_or_create_session(session_id: str) -> tuple[BrowserContext, Page]:
    if session_id not in _sessions:
        context = await _browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            java_script_enabled=True,
            bypass_csp=False,
        )
        page = await context.new_page()
        # Block heavy resources to speed up page loads
        await page.route(
            "**/*.{png,jpg,jpeg,gif,svg,ico,woff,woff2,ttf,mp4,webm}",
            lambda route: route.abort()
        )
        _sessions[session_id] = (context, page)
        logger.info(f"Browser session created: {session_id}")
    return _sessions[session_id]


async def _close_session(session_id: str):
    if session_id in _sessions:
        context, _ = _sessions.pop(session_id)
        await context.close()
        logger.info(f"Browser session closed: {session_id}")


async def _take_screenshot(page: Page) -> str:
    """Take screenshot and return as base64 PNG."""
    screenshot_bytes = await page.screenshot(
        type="png",
        full_page=False,    # viewport only — full page too slow
        clip={"x": 0, "y": 0, "width": 1280, "height": 800},
    )
    return base64.b64encode(screenshot_bytes).decode("utf-8")


async def _extract_clean_text(page: Page) -> str:
    """Extract readable text from page, stripping scripts/styles."""
    html = await page.content()
    soup = BeautifulSoup(html, "lxml")

    # Remove noise elements
    for tag in soup(["script", "style", "nav", "footer", "head",
                     "iframe", "noscript", "aside"]):
        tag.decompose()

    # Get main content (try common selectors first)
    main = (
        soup.find("main") or
        soup.find("article") or
        soup.find(id="content") or
        soup.find(class_="content") or
        soup.find("body")
    )
    text = (main or soup).get_text(separator="\n", strip=True)

    # Collapse multiple newlines
    import re
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text[:MAX_PAGE_TEXT_CHARS]


# ── API Endpoints ────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {
        "status":           "ok",
        "browser_running":  _browser is not None and _browser.is_connected(),
        "active_sessions":  len(_sessions),
    }


@app.post("/navigate/{session_id}", response_model=BrowserResult)
async def navigate(session_id: str, req: NavigateRequest):
    start = time.monotonic()
    _, page = await _get_or_create_session(session_id)

    try:
        response = await page.goto(
            req.url,
            wait_until=req.wait_for,
            timeout=req.timeout_ms,
        )
        if response and not response.ok:
            logger.warning(f"HTTP {response.status} for {req.url}")
    except Exception as e:
        return BrowserResult(
            success=False,
            error=f"Navigation failed: {str(e)[:200]}",
            url=req.url,
            latency_ms=(time.monotonic() - start) * 1000,
        )

    screenshot = await _take_screenshot(page)     if req.take_screenshot else None
    text       = await _extract_clean_text(page)  if req.extract_text    else None
    title      = await page.title()
    current_url = page.url

    links = []
    if req.extract_links:
        anchors = await page.eval_on_selector_all(
            "a[href]",
            "els => els.map(e => e.href).filter(h => h.startsWith('http')).slice(0, 20)"
        )
        links = anchors

    logger.info(f"Navigated to {req.url} in {(time.monotonic()-start)*1000:.0f}ms")
    return BrowserResult(
        success=True,
        screenshot=screenshot,
        text=text,
        links=links,
        title=title,
        url=current_url,
        latency_ms=(time.monotonic() - start) * 1000,
    )


@app.post("/click/{session_id}", response_model=BrowserResult)
async def click(session_id: str, req: ClickRequest):
    start = time.monotonic()
    _, page = await _get_or_create_session(session_id)

    try:
        await page.click(req.selector, timeout=req.timeout_ms)
        await page.wait_for_load_state("domcontentloaded", timeout=5000)
    except Exception as e:
        return BrowserResult(
            success=False,
            error=f"Click failed on '{req.selector}': {str(e)[:200]}",
            url=page.url,
            latency_ms=(time.monotonic() - start) * 1000,
        )

    screenshot = await _take_screenshot(page) if req.take_screenshot else None
    text       = await _extract_clean_text(page)
    return BrowserResult(
        success=True, screenshot=screenshot,
        text=text, title=await page.title(),
        url=page.url,
        latency_ms=(time.monotonic() - start) * 1000,
    )


@app.post("/type/{session_id}", response_model=BrowserResult)
async def type_text(session_id: str, req: TypeRequest):
    start = time.monotonic()
    _, page = await _get_or_create_session(session_id)

    try:
        if req.clear_first:
            await page.fill(req.selector, "", timeout=req.timeout_ms)
        await page.type(req.selector, req.text, delay=30)  # human-like typing
    except Exception as e:
        return BrowserResult(
            success=False,
            error=f"Type failed on '{req.selector}': {str(e)[:200]}",
            url=page.url,
            latency_ms=(time.monotonic() - start) * 1000,
        )

    screenshot = await _take_screenshot(page) if req.take_screenshot else None
    return BrowserResult(
        success=True, screenshot=screenshot,
        url=page.url, title=await page.title(),
        latency_ms=(time.monotonic() - start) * 1000,
    )


@app.post("/scroll/{session_id}", response_model=BrowserResult)
async def scroll(session_id: str, req: ScrollRequest):
    start = time.monotonic()
    _, page = await _get_or_create_session(session_id)

    scripts = {
        "down":   f"window.scrollBy(0, {req.pixels})",
        "up":     f"window.scrollBy(0, -{req.pixels})",
        "top":    "window.scrollTo(0, 0)",
        "bottom": "window.scrollTo(0, document.body.scrollHeight)",
    }
    await page.evaluate(scripts[req.direction])
    await asyncio.sleep(0.3)   # let lazy-load content appear

    screenshot = await _take_screenshot(page)
    text       = await _extract_clean_text(page)
    return BrowserResult(
        success=True, screenshot=screenshot, text=text,
        url=page.url, title=await page.title(),
        latency_ms=(time.monotonic() - start) * 1000,
    )


@app.post("/extract/{session_id}", response_model=BrowserResult)
async def extract(session_id: str, req: ExtractRequest):
    start = time.monotonic()
    _, page = await _get_or_create_session(session_id)

    try:
        if req.attribute:
            value = await page.get_attribute(req.selector, req.attribute)
            text  = value or ""
        else:
            text = await page.inner_text(req.selector)
    except Exception as e:
        return BrowserResult(
            success=False,
            error=f"Extract failed: {str(e)[:200]}",
            url=page.url,
            latency_ms=(time.monotonic() - start) * 1000,
        )

    return BrowserResult(
        success=True, text=text[:MAX_PAGE_TEXT_CHARS],
        url=page.url, title=await page.title(),
        latency_ms=(time.monotonic() - start) * 1000,
    )


@app.post("/screenshot/{session_id}", response_model=BrowserResult)
async def screenshot_only(session_id: str):
    start = time.monotonic()
    _, page = await _get_or_create_session(session_id)
    ss = await _take_screenshot(page)
    return BrowserResult(
        success=True, screenshot=ss,
        url=page.url, title=await page.title(),
        latency_ms=(time.monotonic() - start) * 1000,
    )


@app.delete("/session/{session_id}")
async def close_session_endpoint(session_id: str):
    await _close_session(session_id)
    return {"closed": True, "session_id": session_id}