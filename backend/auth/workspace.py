# backend/auth/workspace.py
"""
Workspace context: builds namespace strings for service isolation.
Each workspace gets its own ChromaDB collection, Mem0 prefix, Neo4j label.
"""
import logging
from dataclasses import dataclass

import asyncpg

from backend.auth.models    import WorkspaceRecord, UserRecord, PlanTier, UserRole
from backend.prompts.registry import get_pool   # reuse asyncpg pool

logger = logging.getLogger(__name__)


@dataclass
class WorkspaceContext:
    """
    Fully resolved workspace context.
    Passed through agent state so all tools use correct namespaces.
    """
    workspace_id:      str
    workspace_slug:    str
    user_id:           str
    user_email:        str
    role:              UserRole
    plan_tier:         PlanTier

    # Namespace strings — use these in all service calls
    chroma_collection: str    # e.g. "ws_acme_corp"
    mem0_user_id:      str    # e.g. "ws_acme_corp:user-uuid"
    neo4j_workspace:   str    # e.g. "WS_ACME_CORP"

    @classmethod
    def from_slug(
        cls,
        workspace_slug: str,
        workspace_id:   str,
        user_id:        str,
        user_email:     str,
        role:           UserRole,
        plan_tier:      PlanTier,
    ) -> "WorkspaceContext":
        slug = workspace_slug.lower().replace("-", "_")
        return cls(
            workspace_id=workspace_id,
            workspace_slug=workspace_slug,
            user_id=user_id,
            user_email=user_email,
            role=role,
            plan_tier=plan_tier,
            chroma_collection=f"ws_{slug}",
            mem0_user_id=f"ws_{slug}:{user_id}",
            neo4j_workspace=f"WS_{slug.upper()}",
        )

    @classmethod
    def dev_default(cls) -> "WorkspaceContext":
        """Dev-mode context — used when APP_ENV=development."""
        return cls.from_slug(
            workspace_slug="default",
            workspace_id="00000000-0000-0000-0000-000000000001",
            user_id="dev-user-001",
            user_email="dev@example.com",
            role=UserRole.ADMIN,
            plan_tier=PlanTier.ENTERPRISE,
        )


async def get_workspace_by_slug(slug: str) -> WorkspaceRecord | None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM workspaces WHERE slug = $1 AND is_active = true",
            slug,
        )
    if not row:
        return None
    return WorkspaceRecord(
        id=row["id"], name=row["name"], slug=row["slug"],
        plan_tier=PlanTier(row["plan_tier"]),
        is_active=row["is_active"],
        chroma_collection=row["chroma_collection"],
        mem0_namespace=row["mem0_namespace"],
        neo4j_label=row["neo4j_label"],
        daily_query_count=row["daily_query_count"],
        total_tokens_used=row["total_tokens_used"],
        monthly_cost_usd=row["monthly_cost_usd"],
        created_at=row["created_at"],
    )


async def create_workspace(
    name:      str,
    slug:      str,
    plan_tier: PlanTier = PlanTier.FREE,
) -> WorkspaceRecord:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO workspaces (name, slug, plan_tier)
            VALUES ($1, $2, $3)
            RETURNING *
            """,
            name, slug, plan_tier.value,
        )
    logger.info(f"Workspace created: {slug} ({plan_tier})")
    return WorkspaceRecord(
        id=row["id"], name=row["name"], slug=row["slug"],
        plan_tier=PlanTier(row["plan_tier"]),
        is_active=row["is_active"],
        chroma_collection=row["chroma_collection"],
        mem0_namespace=row["mem0_namespace"],
        neo4j_label=row["neo4j_label"],
        daily_query_count=0,
        total_tokens_used=0,
        monthly_cost_usd=0.0,
        created_at=row["created_at"],
    )


async def get_user_by_id(user_id: str) -> UserRecord | None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM users WHERE id = $1 AND is_active = true",
            user_id,
        )
    if not row:
        return None
    return UserRecord(
        id=row["id"], email=row["email"], full_name=row["full_name"],
        workspace_id=row["workspace_id"],
        role=UserRole(row["role"]),
        is_active=row["is_active"],
        created_at=row["created_at"],
        last_seen_at=row["last_seen_at"],
        daily_query_count=row["daily_query_count"],
    )


async def create_user(
    email:        str,
    workspace_id: str,
    role:         UserRole      = UserRole.USER,
    full_name:    str | None    = None,
    password:     str | None    = None,
) -> UserRecord:
    pool = await get_pool()

    hashed = None
    if password:
        from passlib.context import CryptContext
        hashed = CryptContext(schemes=["bcrypt"]).hash(password)

    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO users (email, hashed_password, full_name, workspace_id, role)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING *
            """,
            email, hashed, full_name, workspace_id, role.value,
        )
    _masked_email = email[:2] + "***@***" if "@" in email else "***"
    logger.info(f"User created: {_masked_email} role={role} workspace={workspace_id}")  # FIXED: was logging full PII email in plain text; now masked
    return UserRecord(
        id=row["id"], email=row["email"], full_name=row["full_name"],
        workspace_id=row["workspace_id"],
        role=UserRole(row["role"]),
        is_active=row["is_active"],
        created_at=row["created_at"],
        last_seen_at=None,
        daily_query_count=0,
    )


async def list_workspace_users(workspace_id: str) -> list[UserRecord]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM users WHERE workspace_id = $1 ORDER BY created_at",
            workspace_id,
        )
    return [
        UserRecord(
            id=r["id"], email=r["email"], full_name=r["full_name"],
            workspace_id=r["workspace_id"], role=UserRole(r["role"]),
            is_active=r["is_active"], created_at=r["created_at"],
            last_seen_at=r["last_seen_at"],
            daily_query_count=r["daily_query_count"],
        )
        for r in rows
    ]