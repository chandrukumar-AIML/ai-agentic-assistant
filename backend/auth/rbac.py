# backend/auth/rbac.py
"""
Role-Based Access Control.
Defines permissions per role and provides FastAPI dependency for checking.
"""
import logging
from enum import Enum
from functools import wraps
from fastapi import HTTPException, Depends, status

from backend.auth.models import UserRole, JWTClaims
from backend.api.auth    import verify_token   # existing JWT verifier

logger = logging.getLogger(__name__)


class Permission(str, Enum):
    # Chat permissions
    CHAT            = "chat"           # send messages
    UPLOAD_FILE     = "upload_file"    # ingest documents
    VIEW_HISTORY    = "view_history"   # see past sessions

    # Tool permissions
    RUN_CODE        = "run_code"       # code_agent execution
    WEB_SEARCH      = "web_search"     # tavily web search
    VISION          = "vision"         # GPT-4o vision

    # Memory permissions
    READ_MEMORY     = "read_memory"
    WRITE_MEMORY    = "write_memory"
    DELETE_MEMORY   = "delete_memory"

    # Admin permissions
    MANAGE_USERS    = "manage_users"
    VIEW_AUDIT_LOG  = "view_audit_log"
    EDIT_PROMPTS    = "edit_prompts"
    VIEW_EVAL       = "view_eval"
    RUN_EVAL        = "run_eval"
    VIEW_COSTS      = "view_costs"


# Permission matrix: role → set of permissions
ROLE_PERMISSIONS: dict[UserRole, set[Permission]] = {
    UserRole.VIEWER: {
        Permission.CHAT,
        Permission.VIEW_HISTORY,
        Permission.READ_MEMORY,
    },
    UserRole.USER: {
        Permission.CHAT,
        Permission.UPLOAD_FILE,
        Permission.VIEW_HISTORY,
        Permission.RUN_CODE,
        Permission.WEB_SEARCH,
        Permission.VISION,
        Permission.READ_MEMORY,
        Permission.WRITE_MEMORY,
        Permission.DELETE_MEMORY,
        Permission.VIEW_EVAL,
        Permission.VIEW_COSTS,
    },
    UserRole.ADMIN: {
        # Admin has everything
        *list(Permission),
    },
}


def has_permission(role: UserRole, permission: Permission) -> bool:
    return permission in ROLE_PERMISSIONS.get(role, set())


def require_permission(permission: Permission):
    """
    FastAPI dependency factory.
    Usage:
        @router.get("/admin")
        async def admin_route(claims=Depends(require_permission(Permission.MANAGE_USERS))):
    """
    async def _check(token: dict = Depends(verify_token)) -> JWTClaims:
        role_str  = token.get("role", "user")
        try:
            role = UserRole(role_str)
        except ValueError:
            logger.warning(
                f"Invalid role in token: {role_str} for user={token.get('sub')}"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid role in token",
            )

        if not has_permission(role, permission):
            logger.warning(
                f"Permission denied: user={token.get('sub')} "
                f"role={role} required={permission}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission required: {permission.value}",
            )

        return JWTClaims(
            sub=token.get("sub", ""),
            email=token.get("email", ""),
            workspace_id=token.get("workspace_id", ""),
            role=role,
            plan_tier=token.get("plan_tier", "free"),
            workspace_slug=token.get("workspace_slug", "default"),
            exp=token.get("exp", 0),
            iat=token.get("iat", 0),
        )
    return _check


def require_admin():
    """Shortcut for admin-only routes."""
    return require_permission(Permission.MANAGE_USERS)


def extract_claims(token: dict = Depends(verify_token)) -> JWTClaims:
    """
    Extract JWTClaims from token dict.
    Used as FastAPI dependency in any route that needs user context.
    Falls back to dev defaults in development mode.
    """
    from backend.config import get_settings
    settings = get_settings()

    if settings.app_env == "development":
        return JWTClaims(
            sub="dev-user-001",
            email="dev@example.com",
            workspace_id="00000000-0000-0000-0000-000000000001",
            role=UserRole.ADMIN,    # dev gets admin
            plan_tier="enterprise",
            workspace_slug="default",
            exp=9999999999,
            iat=0,
        )

    return JWTClaims(
        sub=token.get("sub", ""),
        email=token.get("email", ""),
        workspace_id=token.get("workspace_id", ""),
        role=UserRole(token.get("role", "user")),
        plan_tier=token.get("plan_tier", "free"),
        workspace_slug=token.get("workspace_slug", "default"),
        exp=token.get("exp", 0),
        iat=token.get("iat", 0),
    )