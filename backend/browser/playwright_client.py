# backend/browser/playwright_client.py
"""
HTTP client for the Playwright Docker service.
The main FastAPI process never runs Playwright directly —
it always goes through the isolated service.
"""
import logging
import uuid
import httpx
from typing import Optional, Literal
from dataclasses import dataclass

from backend.config import get_settings

logger   = logging.getLogger(__name__)
settings = get_settings()

PLAYWRIGHT_SERVICE_URL = getattr(settings, "playwright_service_url", "http://aaa_playwright:8010")  # FIXED: from settings, hardcoded localhost URL replaced

# Module-level httpx client
_client = httpx.AsyncClient(timeout=60.0)


@dataclass
class BrowserActionResult:
    success:     bool
    screenshot:  Optional[str]   # base64 PNG — stream to React UI
    text:        Optional[str]   # extracted page text for agent
    links:       list[str]
    title:       str
    url:         str
    error:       Optional[str]
    latency_ms:  float


class PlaywrightSession:
    """
    Manages a browser session for the duration of one agent task.
    Creates session on first use, closes on cleanup.
    """

    def __init__(self, session_id: str | None = None):
        self.session_id = session_id or str(uuid.uuid4())
        self._actions_taken = 0
        self.MAX_ACTIONS = 20    # safety: max actions per session

    async def _call(self, endpoint: str, data: dict) -> BrowserActionResult:
        """Make a request to the Playwright service."""
        self._actions_taken += 1
        if self._actions_taken > self.MAX_ACTIONS:
            return BrowserActionResult(
                success=False,
                screenshot=None, text=None, links=[], title="", url="",
                error=f"Max actions ({self.MAX_ACTIONS}) reached for this session",
                latency_ms=0.0,
            )

        try:
            response = await _client.post(
                f"{PLAYWRIGHT_SERVICE_URL}/{endpoint}/{self.session_id}",
                json=data,
            )
            response.raise_for_status()
            res = response.json()
            return BrowserActionResult(
                success=res.get("success", False),
                screenshot=res.get("screenshot"),
                text=res.get("text"),
                links=res.get("links", []),
                title=res.get("title", ""),
                url=res.get("url", ""),
                error=res.get("error"),
                latency_ms=res.get("latency_ms", 0.0),
            )
        except httpx.ConnectError:
            return BrowserActionResult(
                success=False, screenshot=None, text=None, links=[],
                title="", url="",
                error="Playwright service unavailable — is the Docker container running?",
                latency_ms=0.0,
            )
        except Exception as e:
            return BrowserActionResult(
                success=False, screenshot=None, text=None, links=[],
                title="", url="",
                error=f"Browser service error: {str(e)[:200]}",
                latency_ms=0.0,
            )

    async def navigate(
        self,
        url:              str,
        wait_for:         Literal["load", "networkidle", "domcontentloaded"] = "domcontentloaded",
        take_screenshot:  bool = True,
        extract_links:    bool = False,
    ) -> BrowserActionResult:
        return await self._call("navigate", {
            "url": url, "wait_for": wait_for,
            "take_screenshot": take_screenshot,
            "extract_text": True,
            "extract_links": extract_links,
        })

    async def click(self, selector: str, take_screenshot: bool = True) -> BrowserActionResult:
        return await self._call("click", {"selector": selector, "take_screenshot": take_screenshot})

    async def type_text(
        self,
        selector:    str,
        text:        str,
        clear_first: bool = True,
    ) -> BrowserActionResult:
        return await self._call("type", {
            "selector": selector, "text": text, "clear_first": clear_first,
        })

    async def scroll(
        self,
        direction: Literal["up", "down", "top", "bottom"] = "down",
        pixels: int = 500,
    ) -> BrowserActionResult:
        return await self._call("scroll", {"direction": direction, "pixels": pixels})

    async def extract(self, selector: str, attribute: str | None = None) -> BrowserActionResult:
        return await self._call("extract", {"selector": selector, "attribute": attribute})

    async def screenshot(self) -> BrowserActionResult:
        return await self._call("screenshot", {})

    async def close(self):
        try:
            await _client.delete(
                f"{PLAYWRIGHT_SERVICE_URL}/session/{self.session_id}"
            )
        except Exception as e:  # FIXED: bare except Exception: pass without logging
            logger.warning(f"Failed to close browser session {self.session_id[:8]}: {e}")
        logger.info(f"Browser session closed: {self.session_id[:8]}")