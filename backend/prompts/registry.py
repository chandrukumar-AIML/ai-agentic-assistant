# backend/prompts/registry.py
"""
PostgreSQL-backed prompt registry.
Stores, versions, and retrieves prompts.
All prompt versions are immutable once created.
"""
import logging
import asyncpg
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import Optional
from functools import lru_cache

from backend.config import get_settings

logger   = logging.getLogger(__name__)
settings = get_settings()

_pool: asyncpg.Pool | None = None


async def get_pool() -> asyncpg.Pool:
    """Shared asyncpg connection pool."""
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            host=settings.postgres_host,
            port=settings.postgres_port,
            database=settings.postgres_db,
            user=settings.postgres_user,
            password=settings.postgres_password,
            min_size=2,
            max_size=10,
        )
        logger.info("Prompt registry DB pool created")
    return _pool


async def close_pool():
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


@dataclass
class PromptVersion:
    id:                int
    prompt_name:       str
    version:           str
    content:           str
    description:       str
    is_active:         bool
    performance_score: float
    query_count:       int
    thumbs_up:         int
    thumbs_down:       int
    created_at:        datetime
    created_by:        str


async def create_prompt(
    prompt_name:  str,
    version:      str,
    content:      str,
    description:  str = "",
    created_by:   str = "system",
    set_active:   bool = False,
) -> PromptVersion:
    """
    Create a new prompt version.
    If set_active=True, deactivate the current active version first.
    Versions are immutable once created.
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            if set_active:
                await conn.execute(
                    "UPDATE prompt_versions SET is_active = false WHERE prompt_name = $1",
                    prompt_name,
                )

            row = await conn.fetchrow(
                """
                INSERT INTO prompt_versions
                    (prompt_name, version, content, description, created_by, is_active)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING *
                """,
                prompt_name, version, content, description, created_by, set_active,
            )

    logger.info(f"Prompt created: {prompt_name} v{version} (active={set_active})")
    return _row_to_prompt(row)


async def get_active_prompt(prompt_name: str) -> Optional[PromptVersion]:
    """Get the currently active version of a prompt."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT * FROM prompt_versions
            WHERE prompt_name = $1 AND is_active = true
            ORDER BY created_at DESC
            LIMIT 1
            """,
            prompt_name,
        )
    return _row_to_prompt(row) if row else None


async def get_prompt_by_id(prompt_id: int) -> Optional[PromptVersion]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM prompt_versions WHERE id = $1", prompt_id
        )
    return _row_to_prompt(row) if row else None


async def get_prompt_history(prompt_name: str) -> list[PromptVersion]:
    """Return all versions of a prompt, newest first."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT * FROM prompt_versions
            WHERE prompt_name = $1
            ORDER BY created_at DESC
            """,
            prompt_name,
        )
    return [_row_to_prompt(r) for r in rows]


async def set_active_version(prompt_id: int, prompt_name: str) -> bool:
    """Activate a specific version — deactivates all others for this name."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute(
                "UPDATE prompt_versions SET is_active = false WHERE prompt_name = $1",
                prompt_name,
            )
            result = await conn.execute(
                "UPDATE prompt_versions SET is_active = true WHERE id = $1",
                prompt_id,
            )
    updated = result.split()[-1] != "0"
    if updated:
        logger.info(f"Prompt {prompt_name} activated version id={prompt_id}")
    return updated


async def record_prompt_feedback(
    prompt_id:  int,
    score:      float,    # 1.0 = thumbs up, 0.0 = thumbs down
):
    """Update prompt performance metrics from user feedback."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        if score >= 0.5:
            await conn.execute(
                """
                UPDATE prompt_versions
                SET thumbs_up    = thumbs_up + 1,
                    query_count  = query_count + 1,
                    performance_score = (
                        (performance_score * query_count + $1) / (query_count + 1)
                    )
                WHERE id = $2
                """,
                score, prompt_id,
            )
        else:
            await conn.execute(
                """
                UPDATE prompt_versions
                SET thumbs_down  = thumbs_down + 1,
                    query_count  = query_count + 1,
                    performance_score = (
                        (performance_score * query_count + $1) / (query_count + 1)
                    )
                WHERE id = $2
                """,
                score, prompt_id,
            )


async def list_all_prompts() -> dict[str, list[PromptVersion]]:
    """Return all prompts grouped by name — for admin UI."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM prompt_versions ORDER BY prompt_name, created_at DESC"
        )
    result: dict[str, list[PromptVersion]] = {}
    for row in rows:
        pv = _row_to_prompt(row)
        result.setdefault(pv.prompt_name, []).append(pv)
    return result


async def delete_prompt_version(prompt_id: int) -> bool:
    """Delete a non-active prompt version."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        # Safety: cannot delete active version
        row = await conn.fetchrow(
            "SELECT is_active FROM prompt_versions WHERE id = $1", prompt_id
        )
        if not row:
            return False
        if row["is_active"]:
            raise ValueError("Cannot delete the active version — activate another first")
        await conn.execute("DELETE FROM prompt_versions WHERE id = $1", prompt_id)
    return True


def _row_to_prompt(row) -> PromptVersion:
    return PromptVersion(
        id=row["id"],
        prompt_name=row["prompt_name"],
        version=row["version"],
        content=row["content"],
        description=row["description"] or "",
        is_active=row["is_active"],
        performance_score=row["performance_score"] or 0.0,
        query_count=row["query_count"] or 0,
        thumbs_up=row["thumbs_up"] or 0,
        thumbs_down=row["thumbs_down"] or 0,
        created_at=row["created_at"],
        created_by=row["created_by"] or "system",
    )