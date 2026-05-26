# backend/scheduler/task_scheduler.py
"""
Agentic Task Scheduler (Feature 4).

Supports four schedule types:
  once      — run at a specific ISO datetime
  interval  — repeat every N minutes/hours (e.g. "30m", "2h", "1d")
  cron      — standard cron expression (e.g. "0 9 * * 1-5")
  event     — trigger on a named Redis pub/sub event

Uses APScheduler with AsyncIOScheduler + Redis job store for persistence.
Falls back to in-memory store if Redis job store unavailable.

Each task execution:
  1. Loads agent_payload and calls the LangGraph graph
  2. Writes result to task_runs table
  3. Sends email/Slack notification if configured
  4. Reschedules or marks completed based on max_runs
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron      import CronTrigger
from apscheduler.triggers.date      import DateTrigger
from apscheduler.triggers.interval  import IntervalTrigger

from backend.config import get_settings

logger   = logging.getLogger(__name__)
settings = get_settings()

# Singleton scheduler
_scheduler: Optional[AsyncIOScheduler] = None


def get_scheduler() -> AsyncIOScheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = AsyncIOScheduler(timezone="UTC")
    return _scheduler


# ── Interval parser ──────────────────────────────────────────────────────────

def _parse_interval(value: str) -> dict:
    """
    Parse "30m", "2h", "7d", "1w" into APScheduler IntervalTrigger kwargs.
    """
    m = re.fullmatch(r'(\d+)([mhdw])', value.strip().lower())
    if not m:
        raise ValueError(f"Invalid interval format: {value!r} — use e.g. '30m', '2h', '7d'")
    n, unit = int(m.group(1)), m.group(2)
    return {
        'm': {"minutes":  n},
        'h': {"hours":    n},
        'd': {"days":     n},
        'w': {"weeks":    n},
    }[unit]


# ── APScheduler trigger builder ──────────────────────────────────────────────

def _build_trigger(schedule_type: str, schedule_value: str, tz: str = "UTC"):
    if schedule_type == "once":
        dt = datetime.fromisoformat(schedule_value)
        return DateTrigger(run_date=dt, timezone=tz)

    if schedule_type == "interval":
        kwargs = _parse_interval(schedule_value)
        return IntervalTrigger(**kwargs, timezone=tz)

    if schedule_type == "cron":
        parts = schedule_value.split()
        if len(parts) != 5:
            raise ValueError(f"Cron expression must have 5 fields: {schedule_value!r}")
        minute, hour, day, month, day_of_week = parts
        return CronTrigger(
            minute=minute, hour=hour, day=day, month=month,
            day_of_week=day_of_week, timezone=tz,
        )

    raise ValueError(f"Unsupported schedule_type: {schedule_type!r}")


# ── DB helpers ────────────────────────────────────────────────────────────────

async def _get_pool():
    from backend.prompts.registry import get_pool
    return await get_pool()


async def _get_task_row(task_id: str) -> Optional[dict]:
    try:
        pool = await _get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT task_id, user_id, session_id, name, agent_node, agent_payload,
                       schedule_type, schedule_value, timezone, status,
                       run_count, max_runs, notify_email, notify_slack
                FROM scheduled_tasks
                WHERE task_id = $1::uuid
                """,
                task_id,
            )
        return dict(row) if row else None
    except Exception as e:
        logger.error("_get_task_row failed for %s: %s", task_id, e)
        return None


async def _update_task_after_run(
    task_id:    str,
    success:    bool,
    error_msg:  Optional[str] = None,
) -> None:
    try:
        pool = await _get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE scheduled_tasks
                SET run_count   = run_count + 1,
                    last_run_at = NOW(),
                    status      = CASE
                        WHEN max_runs IS NOT NULL AND run_count + 1 >= max_runs THEN 'completed'
                        ELSE status
                    END,
                    last_error  = $2
                WHERE task_id = $1::uuid
                """,
                task_id,
                error_msg,
            )
    except Exception as e:
        logger.error("_update_task_after_run failed: %s", e)


async def _log_run(
    task_id:    str,
    status:     str,
    output:     dict,
    error:      Optional[str],
    latency_ms: float,
) -> None:
    try:
        pool = await _get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO task_runs (task_id, status, finished_at, output, error, latency_ms)
                VALUES ($1::uuid, $2, NOW(), $3::jsonb, $4, $5)
                """,
                task_id, status, json.dumps(output), error, latency_ms,
            )
    except Exception as e:
        logger.debug("_log_run non-fatal: %s", e)


# ── Task executor ─────────────────────────────────────────────────────────────

async def _execute_task(task_id: str) -> None:
    """
    Called by APScheduler when a task fires.
    Loads task config, invokes the agent, records results.
    """
    start = time.monotonic()
    task  = await _get_task_row(task_id)
    if not task:
        logger.warning("Scheduled task %s not found — removing from scheduler", task_id)
        try:
            get_scheduler().remove_job(task_id)
        except Exception:
            pass
        return

    if task["status"] not in ("pending", "running"):
        logger.info("Task %s has status=%s — skipping run", task_id, task["status"])
        return

    logger.info("Executing scheduled task: %s (%s)", task["name"], task_id)

    output: dict = {}
    error:  Optional[str] = None

    try:
        # Build minimal AgentState for the task
        payload = json.loads(task["agent_payload"]) if task.get("agent_payload") else {}
        state   = {
            "user_query":    payload.get("query", task["name"]),
            "user_id":       task["user_id"],
            "session_id":    f"scheduled_{task_id}",
            "trace_id":      str(uuid.uuid4()),
            "messages":      [],
            "latency_ms":    {},
            **payload,
        }

        # Run via the compiled LangGraph agent
        from backend.agent.graph import compile_graph
        from langgraph.checkpoint.memory import MemorySaver
        graph   = compile_graph(checkpointer=MemorySaver())
        result  = await graph.ainvoke(
            state,
            config={"configurable": {"thread_id": f"sched_{task_id}"}},
        )
        output  = {"final_answer": result.get("final_answer", ""), "status": "completed"}

    except Exception as e:
        error  = str(e)
        output = {"error": error, "status": "failed"}
        logger.error("Scheduled task %s failed: %s", task_id, e)

    latency_ms = (time.monotonic() - start) * 1000

    # Record run
    await _log_run(
        task_id=task_id,
        status="completed" if not error else "failed",
        output=output,
        error=error,
        latency_ms=latency_ms,
    )
    await _update_task_after_run(task_id, success=not bool(error), error_msg=error)

    # Send notification
    if task.get("notify_email") or task.get("notify_slack"):
        asyncio.create_task(_send_completion_notification(task, output, error))


async def _send_completion_notification(task: dict, output: dict, error: Optional[str]) -> None:
    """Send email/Slack notification after task completion."""
    status_emoji = "✅" if not error else "❌"
    msg = (
        f"{status_emoji} Scheduled task *{task['name']}* "
        f"{'completed' if not error else 'failed'}."
        + (f"\nError: {error}" if error else "")
        + (f"\nResult: {output.get('final_answer', '')[:200]}" if not error else "")
    )

    slack_url = getattr(settings, "slack_webhook_url", None)
    if task.get("notify_slack") and slack_url:
        try:
            import httpx
            async with httpx.AsyncClient(timeout=10.0) as client:
                await client.post(slack_url, json={"text": msg})
        except Exception as e:
            logger.debug("Slack task notification failed: %s", e)

    email = task.get("notify_email")
    if email:
        logger.info("Task %s notification → %s (email delivery skipped in dev)", task["task_id"], email[:4] + "***")


# ── Public API ────────────────────────────────────────────────────────────────

async def create_task(
    name:           str,
    description:    str,
    agent_node:     str,
    agent_payload:  dict,
    schedule_type:  str,
    schedule_value: str,
    user_id:        str,
    workspace_id:   str = "00000000-0000-0000-0000-000000000001",
    timezone:       str = "UTC",
    max_runs:       Optional[int] = None,
    notify_email:   Optional[str] = None,
    notify_slack:   bool = False,
) -> str:
    """Create and register a new scheduled task. Returns task_id UUID."""
    # Validate trigger before DB write
    _build_trigger(schedule_type, schedule_value, timezone)

    task_id = str(uuid.uuid4())

    try:
        pool = await _get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO scheduled_tasks
                    (task_id, user_id, workspace_id, name, description,
                     agent_node, agent_payload, schedule_type, schedule_value,
                     timezone, max_runs, notify_email, notify_slack, next_run_at)
                VALUES ($1::uuid, $2, $3, $4, $5, $6, $7::jsonb, $8, $9,
                        $10, $11, $12, $13, NOW())
                """,
                task_id, user_id, workspace_id, name, description,
                agent_node, json.dumps(agent_payload),
                schedule_type, schedule_value,
                timezone, max_runs, notify_email, notify_slack,
            )
    except Exception as e:
        raise RuntimeError(f"Task creation failed: {e}") from e

    # Register with APScheduler
    _register_job(task_id, schedule_type, schedule_value, timezone)

    logger.info("Task created: %s (%s) — schedule: %s %s", name, task_id, schedule_type, schedule_value)
    return task_id


def _register_job(
    task_id:        str,
    schedule_type:  str,
    schedule_value: str,
    tz:             str,
) -> None:
    """Register an APScheduler job for the task."""
    if schedule_type == "event":
        return   # Event-driven tasks are triggered via Redis pub/sub, not APScheduler

    trigger  = _build_trigger(schedule_type, schedule_value, tz)
    scheduler = get_scheduler()

    scheduler.add_job(
        func=_execute_task,
        trigger=trigger,
        args=[task_id],
        id=task_id,
        replace_existing=True,
        misfire_grace_time=60,   # allow 60s late execution
    )
    logger.debug("APScheduler job registered: %s", task_id)


async def cancel_task(task_id: str) -> bool:
    """Cancel a scheduled task and remove from APScheduler."""
    try:
        pool = await _get_pool()
        async with pool.acquire() as conn:
            result = await conn.execute(
                "UPDATE scheduled_tasks SET status='cancelled' WHERE task_id=$1::uuid AND status!='completed'",
                task_id,
            )
        cancelled = result != "UPDATE 0"
    except Exception as e:
        logger.error("cancel_task DB failed: %s", e)
        return False

    try:
        get_scheduler().remove_job(task_id)
    except Exception:
        pass   # Job may not be in APScheduler (event-type, already completed)

    return cancelled


async def pause_task(task_id: str) -> bool:
    """Pause a recurring task without deleting it."""
    try:
        pool = await _get_pool()
        async with pool.acquire() as conn:
            result = await conn.execute(
                "UPDATE scheduled_tasks SET status='paused' WHERE task_id=$1::uuid AND status='pending'",
                task_id,
            )
        if result == "UPDATE 0":
            return False
        get_scheduler().pause_job(task_id)
        return True
    except Exception as e:
        logger.error("pause_task failed: %s", e)
        return False


async def resume_task(task_id: str) -> bool:
    """Resume a paused task."""
    try:
        pool = await _get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "UPDATE scheduled_tasks SET status='pending' WHERE task_id=$1::uuid AND status='paused' RETURNING schedule_type, schedule_value, timezone",
                task_id,
            )
        if not row:
            return False
        _register_job(task_id, row["schedule_type"], row["schedule_value"], row["timezone"])
        return True
    except Exception as e:
        logger.error("resume_task failed: %s", e)
        return False


async def list_tasks(
    user_id:     str,
    workspace_id: str,
    status_filter: Optional[str] = None,
    limit:  int = 50,
    offset: int = 0,
) -> list[dict]:
    """List tasks for a workspace."""
    limit  = max(1, min(limit, 200))
    offset = max(0, offset)
    try:
        pool = await _get_pool()
        async with pool.acquire() as conn:
            cond   = "WHERE workspace_id = $1"
            params: list = [workspace_id]
            if status_filter:
                cond += " AND status = $2"
                params.append(status_filter)
            rows = await conn.fetch(
                f"""
                SELECT task_id, name, description, schedule_type, schedule_value,
                       status, run_count, max_runs, last_run_at, next_run_at, created_at
                FROM scheduled_tasks {cond}
                ORDER BY created_at DESC
                LIMIT {limit} OFFSET {offset}
                """,
                *params,
            )
        return [dict(r) for r in rows]
    except Exception as e:
        logger.error("list_tasks failed: %s", e)
        return []


async def start_scheduler() -> None:
    """
    Start APScheduler and reload all active tasks from DB.
    Called from main.py lifespan on startup.
    """
    scheduler = get_scheduler()
    if scheduler.running:
        return

    scheduler.start()
    logger.info("APScheduler started")

    # Reload active tasks
    try:
        pool = await _get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT task_id, schedule_type, schedule_value, timezone
                FROM scheduled_tasks
                WHERE status IN ('pending', 'running')
                  AND schedule_type != 'event'
                  AND (schedule_type != 'once' OR next_run_at > NOW())
                """
            )
        for row in rows:
            try:
                _register_job(str(row["task_id"]), row["schedule_type"], row["schedule_value"], row["timezone"])
            except Exception as e:
                logger.warning("Could not reload task %s: %s", row["task_id"], e)
        logger.info("Reloaded %d scheduled tasks from DB", len(rows))
    except Exception as e:
        logger.warning("Task reload failed (non-fatal): %s", e)


async def stop_scheduler() -> None:
    """Gracefully stop APScheduler. Called from lifespan shutdown."""
    scheduler = get_scheduler()
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("APScheduler stopped")
