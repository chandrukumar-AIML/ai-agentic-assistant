# backend/browser/domain_whitelist.py
"""
Per-workspace domain whitelist for browser agent.
Prevents the agent from visiting malicious, off-limits, or internal URLs.

Workspace-specific domains are loaded from PostgreSQL (workspace_domains table)
with a 5-minute TTL in-memory cache to avoid repeated DB round-trips.
"""
import re
import logging
import asyncio
import ipaddress
import time
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Global always-allowed research domains
ALWAYS_ALLOWED = {
    # Research
    "arxiv.org", "scholar.google.com", "semanticscholar.org",
    "pubmed.ncbi.nlm.nih.gov", "ncbi.nlm.nih.gov",
    "ieee.org", "acm.org", "nature.com", "sciencedirect.com",

    # Documentation
    "docs.python.org", "docs.langchain.com", "python.org",
    "fastapi.tiangolo.com", "pydantic.dev", "github.com",
    "stackoverflow.com", "developer.mozilla.org",

    # News and general
    "wikipedia.org", "en.wikipedia.org",
    "techcrunch.com", "wired.com", "theverge.com",
    "reuters.com", "bloomberg.com", "ft.com",

    # AI/ML
    "huggingface.co", "openai.com", "anthropic.com",
    "langchain.com", "llamaindex.ai", "pytorch.org",
}

# Always blocked — never allow regardless of whitelist
ALWAYS_BLOCKED = {
    # Local network (exact hostnames)
    "localhost", "127.0.0.1", "0.0.0.0",
    # Cloud metadata
    "169.254.169.254",   # AWS metadata service
    "metadata.google.internal",
}

# FIXED: private IP ranges checked via ipaddress for full RFC-1918 coverage
_PRIVATE_IP_NETWORKS = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),   # covers 172.16–172.31
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),  # link-local
    ipaddress.ip_network("::1/128"),          # IPv6 loopback
    ipaddress.ip_network("fc00::/7"),         # IPv6 ULA
]

# Regex patterns to block
BLOCKED_PATTERNS = [
    re.compile(r'\.onion$'),          # Tor hidden services
    re.compile(r'file://'),           # Local files
    re.compile(r'javascript:'),       # JS injection
    re.compile(r'data:'),             # Data URIs
    re.compile(r'localhost:\d+'),     # Localhost with port
]

# ── TTL cache for workspace domain lists ──────────────────────────────────────
_CACHE_TTL_SECONDS = 300   # 5 minutes
_cache: dict[str, tuple[list[str], float]] = {}   # slug → (domains, expiry_ts)
_cache_lock = asyncio.Lock()


def is_allowed(url: str, workspace_whitelist: list[str] | None = None) -> tuple[bool, str]:
    """
    Check if a URL is allowed for the browser agent.

    Returns:
        (allowed: bool, reason: str)
    """
    if not url.startswith(("http://", "https://")):
        return False, "Only HTTP/HTTPS URLs allowed"

    # Check blocked patterns
    for pattern in BLOCKED_PATTERNS:
        if pattern.search(url):
            return False, f"URL matches blocked pattern: {pattern.pattern}"

    try:
        parsed = urlparse(url)
        hostname = parsed.hostname or ""
    except Exception:
        return False, "Invalid URL"

    # Check always-blocked exact hostnames
    if hostname in ALWAYS_BLOCKED:
        return False, f"Blocked hostname: {hostname}"

    # Check private/reserved IP ranges via ipaddress module
    try:
        addr = ipaddress.ip_address(hostname)
        for network in _PRIVATE_IP_NETWORKS:
            if addr in network:
                return False, f"Private/reserved IP address blocked: {hostname}"
    except ValueError:
        pass  # not an IP address — continue to hostname checks

    # Check always-allowed
    for allowed in ALWAYS_ALLOWED:
        if hostname == allowed or hostname.endswith(f".{allowed}"):
            return True, "always_allowed"

    # Check workspace-specific whitelist
    if workspace_whitelist:
        for domain in workspace_whitelist:
            if hostname == domain or hostname.endswith(f".{domain}"):
                return True, f"workspace_whitelist:{domain}"

    return False, f"Domain not in whitelist: {hostname}"


async def get_workspace_whitelist(workspace_slug: str) -> list[str]:
    """
    Fetch the per-workspace extra allowed domains from PostgreSQL.

    Results are cached for 5 minutes to avoid DB round-trips on every URL.
    Falls back to an empty list gracefully if the DB is unavailable or the
    workspace_domains table does not yet exist.
    """
    if not workspace_slug:
        return []

    now = time.monotonic()

    # ── Cache hit? ──────────────────────────────────────────────────────────
    async with _cache_lock:
        cached = _cache.get(workspace_slug)
        if cached is not None:
            domains, expiry = cached
            if now < expiry:
                return domains

    # ── Cache miss — fetch from DB ──────────────────────────────────────────
    domains: list[str] = []
    try:
        from backend.prompts.registry import get_pool

        pool = await get_pool()
        rows = await pool.fetch(
            """
            SELECT domain
            FROM   workspace_domains
            WHERE  workspace_slug = $1
              AND  is_active = true
            ORDER  BY domain
            """,
            workspace_slug,
        )
        domains = [row["domain"] for row in rows]
        logger.debug(
            "Loaded %d whitelist domain(s) for workspace '%s'",
            len(domains), workspace_slug,
        )
    except Exception as exc:
        # Table may not exist yet (pre-migration), DB may be down, etc.
        logger.debug(
            "workspace_domains lookup failed for '%s' (non-fatal): %s",
            workspace_slug, exc,
        )
        domains = []

    # ── Populate cache ──────────────────────────────────────────────────────
    async with _cache_lock:
        _cache[workspace_slug] = (domains, now + _CACHE_TTL_SECONDS)

    return domains


def invalidate_cache(workspace_slug: str | None = None) -> None:
    """
    Invalidate the in-memory cache.
    Call after an admin adds/removes workspace domains.
    Pass workspace_slug to invalidate one workspace; pass None to clear all.
    """
    if workspace_slug is None:
        _cache.clear()
        logger.debug("Workspace domain cache fully invalidated")
    else:
        _cache.pop(workspace_slug, None)
        logger.debug("Workspace domain cache invalidated for '%s'", workspace_slug)
