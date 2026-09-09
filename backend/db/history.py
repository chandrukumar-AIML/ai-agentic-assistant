"""
Content history — persisted AI outputs per user.
Storage backend selected at startup:
  - DATABASE_URL set  → asyncpg (Postgres / Neon) — production-ready
  - no DATABASE_URL   → SQLite fallback (local dev / Render free tier)
"""
from __future__ import annotations

import json
import logging
import os
import sqlite3
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# ── Backend selection ──────────────────────────────────────────────────────────
_USE_POSTGRES = bool(os.getenv("DATABASE_URL", "").startswith("postgresql"))
_DB_PATH      = Path("./data/history.db")

# ── SQLite helpers ─────────────────────────────────────────────────────────────

def _get_conn() -> sqlite3.Connection:
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(_DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


_HISTORY_DDL = """
    CREATE TABLE IF NOT EXISTS content_history (
        id           SERIAL PRIMARY KEY,
        user_id      TEXT    NOT NULL,
        vertical     TEXT    NOT NULL,
        action       TEXT    NOT NULL,
        input_label  TEXT,
        output       TEXT    NOT NULL,
        created_at   TEXT    NOT NULL
    )
"""
_SQLITE_DDL = _HISTORY_DDL.replace("SERIAL", "INTEGER")

_HISTORY_IDX = "CREATE INDEX IF NOT EXISTS idx_history_user ON content_history(user_id, created_at DESC)"


def init_db() -> None:
    """Create tables on first boot. Safe to call multiple times."""
    if _USE_POSTGRES:
        _pg_init()
        return
    try:
        with _get_conn() as conn:
            conn.execute(_SQLITE_DDL)
            conn.execute(_HISTORY_IDX)
    except Exception as exc:
        logger.warning("SQLite history init failed (non-fatal): %s", exc)


def save(user_id: str, vertical: str, action: str, input_label: str, output: dict) -> None:
    """Persist one generated output. Errors swallowed — never block the response."""
    if _USE_POSTGRES:
        _pg_save(user_id, vertical, action, input_label, output)
        return
    try:
        with _get_conn() as conn:
            conn.execute(
                "INSERT INTO content_history (user_id, vertical, action, input_label, output, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (user_id, vertical, action, input_label,
                 json.dumps(output, ensure_ascii=False), datetime.utcnow().isoformat()),
            )
    except Exception as exc:
        logger.warning("History save failed (non-fatal): %s", exc)


def get_history(
    user_id: str,
    vertical: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> list[dict]:
    if _USE_POSTGRES:
        return _pg_get_history(user_id, vertical, limit, offset)
    try:
        with _get_conn() as conn:
            if vertical:
                rows = conn.execute(
                    "SELECT * FROM content_history WHERE user_id=? AND vertical=? "
                    "ORDER BY created_at DESC LIMIT ? OFFSET ?",
                    (user_id, vertical, limit, offset),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM content_history WHERE user_id=? "
                    "ORDER BY created_at DESC LIMIT ? OFFSET ?",
                    (user_id, limit, offset),
                ).fetchall()
            result = []
            for r in rows:
                item = dict(r)
                try:
                    item["output"] = json.loads(item["output"])
                except Exception:
                    pass
                result.append(item)
            return result
    except Exception as exc:
        logger.warning("History fetch failed: %s", exc)
        return []


def count_history(user_id: str, vertical: str | None = None) -> int:
    if _USE_POSTGRES:
        return _pg_count_history(user_id, vertical)
    try:
        with _get_conn() as conn:
            if vertical:
                row = conn.execute(
                    "SELECT COUNT(*) FROM content_history WHERE user_id=? AND vertical=?",
                    (user_id, vertical),
                ).fetchone()
            else:
                row = conn.execute(
                    "SELECT COUNT(*) FROM content_history WHERE user_id=?",
                    (user_id,),
                ).fetchone()
            return row[0] if row else 0
    except Exception:
        return 0


def delete_item(user_id: str, item_id: int) -> bool:
    if _USE_POSTGRES:
        return _pg_delete_item(user_id, item_id)
    try:
        with _get_conn() as conn:
            cur = conn.execute(
                "DELETE FROM content_history WHERE id=? AND user_id=?",
                (item_id, user_id),
            )
            return cur.rowcount > 0
    except Exception as exc:
        logger.warning("History delete failed: %s", exc)
        return False


# ── Postgres backend (asyncpg via sync wrapper) ────────────────────────────────
# Uses psycopg2-binary (already in requirements.txt) for sync calls.
# asyncpg (also in requirements) is available for async routes in the future.

def _pg_conn():
    import psycopg2
    import psycopg2.extras
    dsn = os.getenv("DATABASE_URL", "")
    conn = psycopg2.connect(dsn)
    conn.autocommit = True
    return conn


def _pg_init() -> None:
    try:
        conn = _pg_conn()
        cur  = conn.cursor()
        cur.execute(_HISTORY_DDL)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_history_user ON content_history(user_id, created_at DESC)")
        conn.close()
        logger.info("Postgres history table ready")
    except Exception as exc:
        logger.warning("Postgres history init failed (non-fatal): %s", exc)


def _pg_save(user_id: str, vertical: str, action: str, input_label: str, output: dict) -> None:
    try:
        conn = _pg_conn()
        cur  = conn.cursor()
        cur.execute(
            "INSERT INTO content_history (user_id, vertical, action, input_label, output, created_at) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            (user_id, vertical, action, input_label,
             json.dumps(output, ensure_ascii=False), datetime.utcnow().isoformat()),
        )
        conn.close()
    except Exception as exc:
        logger.warning("Postgres history save failed (non-fatal): %s", exc)


def _pg_get_history(user_id: str, vertical: str | None, limit: int, offset: int) -> list[dict]:
    try:
        import psycopg2.extras
        conn = _pg_conn()
        cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        if vertical:
            cur.execute(
                "SELECT * FROM content_history WHERE user_id=%s AND vertical=%s "
                "ORDER BY created_at DESC LIMIT %s OFFSET %s",
                (user_id, vertical, limit, offset),
            )
        else:
            cur.execute(
                "SELECT * FROM content_history WHERE user_id=%s "
                "ORDER BY created_at DESC LIMIT %s OFFSET %s",
                (user_id, limit, offset),
            )
        rows = cur.fetchall()
        conn.close()
        result = []
        for r in rows:
            item = dict(r)
            if isinstance(item.get("output"), str):
                try:
                    item["output"] = json.loads(item["output"])
                except Exception:
                    pass
            result.append(item)
        return result
    except Exception as exc:
        logger.warning("Postgres history fetch failed: %s", exc)
        return []


def _pg_count_history(user_id: str, vertical: str | None) -> int:
    try:
        conn = _pg_conn()
        cur  = conn.cursor()
        if vertical:
            cur.execute("SELECT COUNT(*) FROM content_history WHERE user_id=%s AND vertical=%s",
                        (user_id, vertical))
        else:
            cur.execute("SELECT COUNT(*) FROM content_history WHERE user_id=%s", (user_id,))
        count = cur.fetchone()[0]
        conn.close()
        return count
    except Exception:
        return 0


def _pg_delete_item(user_id: str, item_id: int) -> bool:
    try:
        conn = _pg_conn()
        cur  = conn.cursor()
        cur.execute("DELETE FROM content_history WHERE id=%s AND user_id=%s", (item_id, user_id))
        deleted = cur.rowcount > 0
        conn.close()
        return deleted
    except Exception as exc:
        logger.warning("Postgres history delete failed: %s", exc)
        return False
