import logging
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address

from backend.config import get_settings

router = APIRouter(tags=["auth"])

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


# ── Demo user store (dev only) ────────────────────────────────────────────────

_DEMO_USERS = {
    "admin@agentic.local": {
        "id": "00000000-0000-0000-0000-000000000001",
        "full_name": "Admin User",
        "email": "admin@agentic.local",
        "password_hash": hash_password("admin123"),
        "role": UserRole.admin,
        "plan_tier": PlanTier.enterprise,
        "workspace_id": "ws-001",
        "workspace_slug": "default",
    },
    "demo@agentic.local": {
        "id": "00000000-0000-0000-0000-000000000002",
        "full_name": "Demo Client",
        "email": "demo@agentic.local",
        "password_hash": hash_password("demo123"),
        "role": UserRole.member,
        "plan_tier": PlanTier.pro,
        "workspace_id": "ws-001",
        "workspace_slug": "default",
    },
}


class LoginRequest(BaseModel):
    email:    str
    password: str


class UserProfile(BaseModel):
    id:             str
    full_name:      str
    email:          str
    role:           str
    plan_tier:      str
    workspace_id:   str
    workspace_slug: str


@router.post("/auth/login")
async def login(body: LoginRequest):
    user = _DEMO_USERS.get(body.email)
    if not user or not verify_password(body.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_access_token(
        user_id=user["id"], email=user["email"],
        workspace_id=user["workspace_id"], workspace_slug=user["workspace_slug"],
        role=user["role"], plan_tier=user["plan_tier"],
    )
    return {
        **token.model_dump(),
        "user": {
            "id": user["id"], "full_name": user["full_name"],
            "email": user["email"], "role": user["role"].value,
            "plan_tier": user["plan_tier"].value,
            "workspace_id": user["workspace_id"],
            "workspace_slug": user["workspace_slug"],
        },
    }


@router.get("/auth/me")
async def me(claims: dict = Depends(verify_token)):
    email = claims.get("email", "dev@example.com")
    user  = _DEMO_USERS.get(email, list(_DEMO_USERS.values())[0])
    return {
        "id": user["id"], "full_name": user["full_name"],
        "email": user["email"], "role": claims.get("role", "admin"),
        "plan_tier": claims.get("plan_tier", "enterprise"),
        "workspace_id": claims.get("workspace_id", "ws-001"),
        "workspace_slug": claims.get("workspace_slug", "default"),
    }


@router.get("/auth/profile")
async def profile(claims: dict = Depends(verify_token)):
    return await me(claims)
