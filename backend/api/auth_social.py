"""
Social Media OAuth 2.0 flows — LinkedIn & Buffer.
Each platform: /start (redirect to platform) → /callback (exchange code → token).
After success, redirect to frontend /settings with token in URL fragment so it
never appears in server logs.
"""
import httpx
from fastapi import APIRouter
from fastapi.responses import RedirectResponse

from backend.config import get_settings

router = APIRouter(prefix="/auth", tags=["social-oauth"])
settings = get_settings()

# ── LinkedIn ──────────────────────────────────────────────────────────────────
_LI_AUTH   = "https://www.linkedin.com/oauth/v2/authorization"
_LI_TOKEN  = "https://www.linkedin.com/oauth/v2/accessToken"
_LI_ME     = "https://api.linkedin.com/v2/me"
_LI_SCOPE  = "openid profile w_member_social"
def _LI_REDIR() -> str:
    return f"{settings.backend_url}/auth/linkedin/callback"


@router.get("/linkedin/start")
async def linkedin_start():
    if not settings.linkedin_client_id:
        return RedirectResponse(
            f"{settings.frontend_url}/settings?social_error=linkedin_not_configured"
        )
    url = (
        f"{_LI_AUTH}"
        f"?response_type=code"
        f"&client_id={settings.linkedin_client_id}"
        f"&redirect_uri={_LI_REDIR()}"
        f"&scope={_LI_SCOPE.replace(' ', '%20')}"
        f"&state=linkedin"
    )
    return RedirectResponse(url)


@router.get("/linkedin/callback")
async def linkedin_callback(code: str = "", error: str = "", state: str = ""):
    fe = settings.frontend_url
    if error or not code:
        return RedirectResponse(f"{fe}/settings?social_error=linkedin_{error or 'cancelled'}")

    async with httpx.AsyncClient() as client:
        # Exchange code for token
        tok_resp = await client.post(_LI_TOKEN, data={
            "grant_type":    "authorization_code",
            "code":          code,
            "redirect_uri":  _LI_REDIR(),
            "client_id":     settings.linkedin_client_id,
            "client_secret": settings.linkedin_client_secret,
        })
        if tok_resp.status_code != 200:
            return RedirectResponse(f"{fe}/settings?social_error=linkedin_token_failed")
        access_token = tok_resp.json().get("access_token", "")

        # Fetch person URN
        me_resp = await client.get(
            _LI_ME,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        person_id  = me_resp.json().get("id", "") if me_resp.status_code == 200 else ""
        person_urn = f"urn:li:person:{person_id}" if person_id else ""

    return RedirectResponse(
        f"{fe}/settings"
        f"?social_ok=linkedin"
        f"&li_token={access_token}"
        f"&li_urn={person_urn}"
    )


# ── Buffer ────────────────────────────────────────────────────────────────────
_BUF_AUTH  = "https://bufferapp.com/oauth2/authorize"
_BUF_TOKEN = "https://api.bufferapp.com/1/oauth2/token.json"
def _BUF_REDIR() -> str:
    return f"{settings.backend_url}/auth/buffer/callback"


@router.get("/buffer/start")
async def buffer_start():
    if not settings.buffer_client_id:
        return RedirectResponse(
            f"{settings.frontend_url}/settings?social_error=buffer_not_configured"
        )
    url = (
        f"{_BUF_AUTH}"
        f"?client_id={settings.buffer_client_id}"
        f"&redirect_uri={_BUF_REDIR()}"
        f"&response_type=code"
    )
    return RedirectResponse(url)


@router.get("/buffer/callback")
async def buffer_callback(code: str = "", error: str = ""):
    fe = settings.frontend_url
    if error or not code:
        return RedirectResponse(f"{fe}/settings?social_error=buffer_{error or 'cancelled'}")

    async with httpx.AsyncClient() as client:
        tok_resp = await client.post(_BUF_TOKEN, data={
            "client_id":     settings.buffer_client_id,
            "client_secret": settings.buffer_client_secret,
            "redirect_uri":  _BUF_REDIR(),
            "code":          code,
            "grant_type":    "authorization_code",
        })
        if tok_resp.status_code != 200:
            return RedirectResponse(f"{fe}/settings?social_error=buffer_token_failed")
        access_token = tok_resp.json().get("access_token", "")

    return RedirectResponse(
        f"{fe}/settings?social_ok=buffer&buf_token={access_token}"
    )
