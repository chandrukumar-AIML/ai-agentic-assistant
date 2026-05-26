# backend/verticals/analyst/tools/sql_tool.py
"""
Safe PostgreSQL query tool for Data Analyst agent.
Read-only queries only — SELECT statements enforced.
"""
import logging
import asyncpg
from backend.config import get_settings

logger   = logging.getLogger(__name__)
settings = get_settings()

FORBIDDEN_KEYWORDS = {"INSERT", "UPDATE", "DELETE", "DROP", "CREATE", "ALTER", "TRUNCATE", "GRANT", "REVOKE"}


async def run_sql_query(
    query:   str,
    params:  list | None = None,
    limit:   int = 1000,
) -> dict:
    """
    Execute a read-only SQL query against the analytics database.
    Automatically appends LIMIT to prevent runaway queries.
    """
    query_upper = query.upper().strip()

    # Enforce read-only
    if not query_upper.startswith("SELECT"):
        return {"error": "Only SELECT queries are allowed"}

    for kw in FORBIDDEN_KEYWORDS:
        if f" {kw} " in f" {query_upper} " or query_upper.startswith(kw):
            return {"error": f"Forbidden keyword: {kw}"}

    # Append limit if not present
    if "LIMIT" not in query_upper:
        query = query.rstrip(";") + f" LIMIT {limit}"

    try:
        conn    = await asyncpg.connect(
            host=settings.postgres_host,
            port=settings.postgres_port,
            database=settings.postgres_db,
            user=settings.postgres_user,
            password=settings.postgres_password,
        )
        records = await conn.fetch(query, *(params or []))
        await conn.close()

        rows    = [dict(r) for r in records]
        columns = list(rows[0].keys()) if rows else []

        return {
            "rows":    rows,
            "columns": columns,
            "count":   len(rows),
        }
    except Exception as e:
        logger.error(f"SQL query failed: {e}")
        return {"error": str(e)}


async def get_table_schema(table_name: str) -> dict:
    """Get column definitions for a table."""
    # FIXED: SQL injection — table_name was interpolated directly; use parameterized $1 query
    result = await run_sql_query(
        """
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = $1
        ORDER BY ordinal_position
        """,
        params=[table_name],
    )
    return result


async def list_tables() -> list[str]:
    """List all user tables in the database."""
    result = await run_sql_query(
        """
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
        ORDER BY table_name
        """
    )
    return [r["table_name"] for r in result.get("rows", [])]