"""User persistence — SQLite-backed user store for registered accounts."""
from __future__ import annotations

import logging
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

_DB_PATH = Path("./data/history.db")


def _get_conn() -> sqlite3.Connection:
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(_DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_users_table() -> None:
    try:
        with _get_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id            TEXT PRIMARY KEY,
                    email         TEXT UNIQUE NOT NULL,
                    full_name     TEXT NOT NULL,
                    password_hash TEXT NOT NULL,
                    role          TEXT NOT NULL DEFAULT 'member',
                    plan_tier     TEXT NOT NULL DEFAULT 'free',
                    workspace_id  TEXT NOT NULL,
                    created_at    TEXT NOT NULL
                )
            """)
            conn.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email ON users(email)"
            )
    except Exception as exc:
        logger.warning("Users table init failed (non-fatal): %s", exc)


def get_user_by_email(email: str) -> dict | None:
    try:
        with _get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE email = ?", (email,)
            ).fetchone()
            return dict(row) if row else None
    except Exception as exc:
        logger.warning("User lookup failed: %s", exc)
        return None


def create_user(
    email: str,
    full_name: str,
    password_hash: str,
    role: str = "member",
    plan_tier: str = "free",
) -> dict | None:
    user_id = str(uuid.uuid4())
    workspace_id = f"ws-{user_id[:8]}"
    now = datetime.utcnow().isoformat()
    try:
        with _get_conn() as conn:
            conn.execute(
                """INSERT INTO users
                   (id, email, full_name, password_hash, role, plan_tier, workspace_id, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (user_id, email, full_name, password_hash, role, plan_tier, workspace_id, now),
            )
        return {
            "id": user_id, "email": email, "full_name": full_name,
            "role": role, "plan_tier": plan_tier,
            "workspace_id": workspace_id, "workspace_slug": "default",
        }
    except sqlite3.IntegrityError:
        return None
    except Exception as exc:
        logger.warning("User create failed: %s", exc)
        return None
