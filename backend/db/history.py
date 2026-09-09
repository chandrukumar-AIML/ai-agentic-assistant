"""
Content history — SQLite-backed persistence for generated AI outputs.
Each vertical action result is saved so users can review past generations.
"""
from __future__ import annotations

import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

_DB_PATH = Path("./data/history.db")


def _get_conn() -> sqlite3.Connection:
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(_DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create tables on first boot. Safe to call multiple times."""
    try:
        with _get_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS content_history (
                    id           INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id      TEXT    NOT NULL,
                    vertical     TEXT    NOT NULL,
                    action       TEXT    NOT NULL,
                    input_label  TEXT,
                    output       TEXT    NOT NULL,
                    created_at   TEXT    NOT NULL
                )
            """)
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_history_user ON content_history(user_id, created_at DESC)"
            )
    except Exception as exc:
        logger.warning("History DB init failed (non-fatal): %s", exc)


def save(
    user_id: str,
    vertical: str,
    action: str,
    input_label: str,
    output: dict,
) -> None:
    """Persist one generated output. Errors are swallowed — never block the response."""
    try:
        with _get_conn() as conn:
            conn.execute(
                "INSERT INTO content_history (user_id, vertical, action, input_label, output, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (user_id, vertical, action, input_label, json.dumps(output, ensure_ascii=False),
                 datetime.utcnow().isoformat()),
            )
    except Exception as exc:
        logger.warning("History save failed (non-fatal): %s", exc)


def get_history(user_id: str, vertical: str | None = None, limit: int = 20) -> list[dict]:
    """Return recent history for a user, optionally filtered by vertical."""
    try:
        with _get_conn() as conn:
            if vertical:
                rows = conn.execute(
                    "SELECT * FROM content_history WHERE user_id=? AND vertical=? "
                    "ORDER BY created_at DESC LIMIT ?",
                    (user_id, vertical, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM content_history WHERE user_id=? "
                    "ORDER BY created_at DESC LIMIT ?",
                    (user_id, limit),
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


def delete_item(user_id: str, item_id: int) -> bool:
    """Delete one history item. Only deletes if it belongs to the user."""
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
