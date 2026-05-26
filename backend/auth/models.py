# backend/auth/models.py
"""
Pydantic models for User, Workspace, JWT claims.
Used across auth, RBAC, and audit layers.
"""
from __future__ import annotations
from enum import Enum
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field  # FIXED: import Field for length validation
from typing import Optional


class PlanTier(str, Enum):
    FREE       = "free"
    PRO        = "pro"
    ENTERPRISE = "enterprise"


class UserRole(str, Enum):
    VIEWER = "viewer"    # read-only chat
    USER   = "user"      # all agent tools
    ADMIN  = "admin"     # + user management, prompt editor, eval results


# Rate limits per tier (daily queries)
RATE_LIMITS: dict[PlanTier, int] = {
    PlanTier.FREE:       50,
    PlanTier.PRO:        500,
    PlanTier.ENTERPRISE: 999_999,   # effectively unlimited
}


class WorkspaceRecord(BaseModel):
    id:               UUID
    name:             str
    slug:             str
    plan_tier:        PlanTier
    is_active:        bool
    chroma_collection: str
    mem0_namespace:   str
    neo4j_label:      str
    daily_query_count: int
    total_tokens_used: int
    monthly_cost_usd: float
    created_at:       datetime


class UserRecord(BaseModel):
    id:               UUID
    email:            str
    full_name:        Optional[str]
    workspace_id:     UUID
    role:             UserRole
    is_active:        bool
    created_at:       datetime
    last_seen_at:     Optional[datetime]
    daily_query_count: int


class JWTClaims(BaseModel):
    """Claims embedded in the JWT token."""
    sub:          str        # user_id (UUID string)
    email:        str
    workspace_id: str        # workspace_id (UUID string)
    role:         UserRole
    plan_tier:    PlanTier
    workspace_slug: str
    exp:          int        # Unix timestamp
    iat:          int


class TokenResponse(BaseModel):
    access_token:  str
    token_type:    str = "bearer"
    expires_in:    int = 86400   # 24 hours


class UserCreateRequest(BaseModel):
    email:        EmailStr
    password:     str     = Field(..., min_length=8, max_length=128)   # FIXED: added length limits — prevents empty/unbounded passwords
    full_name:    Optional[str] = Field(None, max_length=200)          # FIXED: added max_length to prevent oversized input
    workspace_id: Optional[str] = None   # admin provides this
    role:         UserRole = UserRole.USER


class WorkspaceCreateRequest(BaseModel):
    name:      str = Field(..., min_length=1, max_length=100)   # FIXED: added length limits on user-provided strings
    slug:      str = Field(..., min_length=1, max_length=50)    # FIXED: added length limits on user-provided strings
    plan_tier: PlanTier = PlanTier.FREE