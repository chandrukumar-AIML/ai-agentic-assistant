import logging
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address

from backend.config import get_settings

limiter  = Limiter(key_func=get_remote_address)
logger   = logging.getLogger(__name__)
settings = get_settings()

ALGORITHM    = "HS256"
TOKEN_EXPIRE = timedelta(days=30) if settings.app_env == "development" else timedelta(hours=24)


# ── Inline models (backend/auth/ was removed) ─────────────────────────────────

class UserRole(str, Enum):
    admin  = "admin"
    member = "member"
    viewer = "viewer"


class PlanTier(str, Enum):
    free       = "free"
    pro        = "pro"
    enterprise = "enterprise"


class TokenResponse(BaseModel):
    access_token: str
    token_type:   str = "bearer"
    expires_in:   int = 86400


class JWTClaims(BaseModel):
    sub:            str
    email:          str
    workspace_id:   str
    workspace_slug: str
    role:           UserRole
    plan_tier:      PlanTier


# ── Helpers ───────────────────────────────────────────────────────────────────

_pwd_ctx      = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return _pwd_ctx.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd_ctx.verify(plain, hashed)


def create_access_token(
    user_id: str, email: str,
    workspace_id: str, workspace_slug: str,
    role: UserRole, plan_tier: PlanTier,
) -> TokenResponse:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id, "email": email,
        "workspace_id": workspace_id, "workspace_slug": workspace_slug,
        "role": role.value, "plan_tier": plan_tier.value,
        "iat": int(now.timestamp()),
        "exp": int((now + TOKEN_EXPIRE).timestamp()),
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)
    return TokenResponse(access_token=token, token_type="bearer", expires_in=86400)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def verify_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> dict:
    # In development, skip JWT — return a dev admin user
    if settings.app_env == "development":
        return {
            "sub":            "dev-user-001",
            "email":          "dev@example.com",
            "workspace_id":   "00000000-0000-0000-0000-000000000001",
            "workspace_slug": "default",
            "role":           "admin",
            "plan_tier":      "enterprise",
        }
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return decode_token(credentials.credentials)
