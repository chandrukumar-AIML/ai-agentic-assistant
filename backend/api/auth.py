import logging
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
from slowapi import Limiter
from slowapi.util import get_remote_address

from backend.config import get_settings

router = APIRouter(tags=["auth"])

limiter  = Limiter(key_func=get_remote_address)
logger   = logging.getLogger(__name__)
settings = get_settings()

ALGORITHM       = "HS256"
ACCESS_EXPIRE   = timedelta(days=30) if settings.app_env == "development" else timedelta(hours=24)
REFRESH_EXPIRE  = timedelta(days=7)


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
    access_token:  str
    refresh_token: str
    token_type:    str = "bearer"
    expires_in:    int = 86400


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


def _make_token(payload: dict, expire: timedelta) -> str:
    now = datetime.now(timezone.utc)
    payload = {**payload, "iat": int(now.timestamp()), "exp": int((now + expire).timestamp())}
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)


def create_access_token(
    user_id: str, email: str,
    workspace_id: str, workspace_slug: str,
    role: UserRole, plan_tier: PlanTier,
) -> TokenResponse:
    base = {
        "sub": user_id, "email": email,
        "workspace_id": workspace_id, "workspace_slug": workspace_slug,
        "role": role.value, "plan_tier": plan_tier.value,
    }
    access  = _make_token({**base, "type": "access"},  ACCESS_EXPIRE)
    refresh = _make_token({"sub": user_id, "type": "refresh"}, REFRESH_EXPIRE)
    return TokenResponse(access_token=access, refresh_token=refresh, expires_in=86400)


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


# ── Register ──────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email:     EmailStr
    password:  str
    full_name: str


@router.post("/auth/register", status_code=201, summary="Self-serve user registration")
async def register(body: RegisterRequest):
    if len(body.password) < 8:
        raise HTTPException(status_code=422, detail="Password must be at least 8 characters")

    from backend.db.users import create_user, get_user_by_email
    if body.email in _DEMO_USERS or get_user_by_email(body.email):
        raise HTTPException(status_code=409, detail="Email already registered")

    user = create_user(
        email=body.email,
        full_name=body.full_name,
        password_hash=hash_password(body.password),
        role="member",
        plan_tier="free",
    )
    if not user:
        raise HTTPException(status_code=500, detail="Registration failed — please try again")

    token = create_access_token(
        user_id=user["id"], email=user["email"],
        workspace_id=user["workspace_id"], workspace_slug=user["workspace_slug"],
        role=UserRole.member, plan_tier=PlanTier.free,
    )
    return {**token.model_dump(), "user": user}


# ── Refresh token ─────────────────────────────────────────────────────────────

class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/auth/refresh", summary="Exchange refresh token for new access token")
async def refresh_token(body: RefreshRequest):
    try:
        claims = jwt.decode(body.refresh_token, settings.jwt_secret, algorithms=[ALGORITHM])
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid refresh token: {e}")

    if claims.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Token is not a refresh token")

    user_id = claims.get("sub", "")

    # Look up the user (demo users + registered users)
    user = next((u for u in _DEMO_USERS.values() if u["id"] == user_id), None)
    if not user:
        # For registered users we need email; fall back to a minimal token
        new_access = _make_token(
            {"sub": user_id, "email": "", "workspace_id": "ws-001",
             "workspace_slug": "default", "role": "member", "plan_tier": "free", "type": "access"},
            ACCESS_EXPIRE,
        )
        new_refresh = _make_token({"sub": user_id, "type": "refresh"}, REFRESH_EXPIRE)
        return TokenResponse(access_token=new_access, refresh_token=new_refresh, expires_in=86400)

    token = create_access_token(
        user_id=user["id"], email=user["email"],
        workspace_id=user["workspace_id"], workspace_slug=user["workspace_slug"],
        role=user["role"], plan_tier=user["plan_tier"],
    )
    return token
