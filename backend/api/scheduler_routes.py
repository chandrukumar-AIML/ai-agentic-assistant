# backend/api/scheduler_routes.py
"""
Agentic Task Scheduler REST API (Feature 4).

Endpoints:
  POST /scheduler/tasks                    — create scheduled task
  GET  /scheduler/tasks                    — list tasks for workspace
  GET  /scheduler/tasks/{task_id}          — get single task detail
  PATCH /scheduler/tasks/{task_id}/cancel  — cancel task
  PATCH /scheduler/tasks/{task_id}/pause   — pause recurring task
  PATCH /scheduler/tasks/{task_id}/resume  — resume paused task
  GET  /scheduler/tasks/{task_id}/runs     — task run history
"""
from __future__ import annotations

import json
import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, field_validator

from backend.api.auth import verify_token
from backend.scheduler.task_scheduler import (
    cancel_task,
    create_task,
    list_tasks,
    pause_task,
    resume_task,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/scheduler", tags=["scheduler"])


# ── Models ────────────────────────────────────────────────────────────────────

VALID_SCHEDULE_TYPES = {"once", "interval", "cron", "event"}


class CreateTaskRequest(BaseModel):
    name:           str  = Field(..., min_length=1, max_length=200)
    description:    str  = Field(default="", max_length=1000)
    agent_node:     str  = Field(..., min_length=1, max_length=100,
                                  description="LangGraph node name to invoke")
    agent_payload:  dict = Field(default_factory=dict,
                                  description="Payload passed to the agent node")
    schedule_type:  str  = Field(..., description="once | interval | cron | event")
    schedule_value: str  = Field(..., min_length=1, max_length=200,
                                  description="ISO datetime | '30m' | cron expr | event name")
    timezone:       str  = Field(default="UTC", max_length=50)
    max_runs:       Optional[int] = Field(default=None, ge=1, le=10_000)
    notify_email:   Optional[str] = Field(default=None, max_length=200)
    notify_slack:   bool = Field(default=False)

    @field_validator("schedule_type")
    @classmethod
    def validate_schedule_type(cls, v: str) -> str:
        if v not in VALID_SCHEDULE_TYPES:
            raise ValueError(f"schedule_type must be one of {VALID_SCHEDULE_TYPES}")
        return v


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post(
    "/tasks",
    summary="Create a scheduled agent task",
    status_code=status.HTTP_201_CREATED,
    response_model=dict,
)
async def create_scheduled_task(
    req:   CreateTaskRequest,
    token: dict = Depends(verify_token),
):
    """
    Schedule an agent task to run once, on a recurring interval, or via cron expression.

    - `once`:     schedule_value = ISO 8601 datetime (e.g. "2025-06-01T09:00:00")
    - `interval`: schedule_value = duration string (e.g. "30m", "2h", "7d")
    - `cron`:     schedule_value = cron expression (e.g. "0 9 * * 1-5")
    - `event`:    schedule_value = Redis pub/sub event name
    """
    user_id      = token.get("sub", "anonymous")
    workspace_id = token.get("workspace_id", "00000000-0000-0000-0000-000000000001")

    try:
        task_id = await create_task(
            name=req.name,
            description=req.description,
            agent_node=req.agent_node,
            agent_payload=req.agent_payload,
            schedule_type=req.schedule_type,
            schedule_value=req.schedule_value,
            user_id=user_id,
            workspace_id=workspace_id,
            timezone=req.timezone,
            max_runs=req.max_runs,
            notify_email=req.notify_email,
            notify_slack=req.notify_slack,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail="Task scheduler temporarily unavailable.")

    return {
        "task_id": task_id,
        "name":    req.name,
        "status":  "pending",
        "message": f"Task scheduled: {req.schedule_type} / {req.schedule_value}",
    }


@router.get(
    "/tasks",
    summary="List scheduled tasks",
    response_model=dict,
)
async def list_scheduled_tasks(
    status_filter: Optional[str] = Query(default=None, alias="status"),
    limit:   int = Query(default=50, ge=1, le=200),
    offset:  int = Query(default=0, ge=0),
    token:   dict = Depends(verify_token),
):
    user_id      = token.get("sub", "anonymous")
    workspace_id = token.get("workspace_id", "00000000-0000-0000-0000-000000000001")

    tasks = await list_tasks(
        user_id=user_id,
        workspace_id=workspace_id,
        status_filter=status_filter,
        limit=limit,
        offset=offset,
    )

    def _serialize(t: dict) -> dict:
        return {
            "task_id":        str(t.get("task_id", "")),
            "name":           t.get("name", ""),
            "description":    t.get("description", ""),
            "schedule_type":  t.get("schedule_type", ""),
            "schedule_value": t.get("schedule_value", ""),
            "status":         t.get("status", ""),
            "run_count":      t.get("run_count", 0),
            "max_runs":       t.get("max_runs"),
            "last_run_at":    t["last_run_at"].isoformat() if t.get("last_run_at") else None,
            "next_run_at":    t["next_run_at"].isoformat() if t.get("next_run_at") else None,
            "created_at":     t["created_at"].isoformat() if t.get("created_at") else None,
        }

    return {
        "total":  len(tasks),
        "limit":  limit,
        "offset": offset,
        "tasks":  [_serialize(t) for t in tasks],
    }


@router.patch(
    "/tasks/{task_id}/cancel",
    summary="Cancel a scheduled task",
    response_model=dict,
)
async def cancel_scheduled_task(
    task_id: str,
    token:   dict = Depends(verify_token),
):
    try:
        UUID(task_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid task ID.")

    success = await cancel_task(task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found or already completed.")
    return {"task_id": task_id, "status": "cancelled"}


@router.patch(
    "/tasks/{task_id}/pause",
    summary="Pause a recurring task",
    response_model=dict,
)
async def pause_scheduled_task(
    task_id: str,
    token:   dict = Depends(verify_token),
):
    try:
        UUID(task_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid task ID.")

    success = await pause_task(task_id)
    if not success:
        raise HTTPException(status_code=409, detail="Task cannot be paused (not in pending state).")
    return {"task_id": task_id, "status": "paused"}


@router.patch(
    "/tasks/{task_id}/resume",
    summary="Resume a paused task",
    response_model=dict,
)
async def resume_scheduled_task(
    task_id: str,
    token:   dict = Depends(verify_token),
):
    try:
        UUID(task_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid task ID.")

    success = await resume_task(task_id)
    if not success:
        raise HTTPException(status_code=409, detail="Task is not paused.")
    return {"task_id": task_id, "status": "pending", "message": "Task resumed."}


@router.get(
    "/tasks/{task_id}/runs",
    summary="Task run history",
    response_model=dict,
)
async def get_task_runs(
    task_id: str,
    limit:   int = Query(default=20, ge=1, le=100),
    token:   dict = Depends(verify_token),
):
    """Get execution history for a specific task."""
    try:
        UUID(task_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid task ID.")

    try:
        from backend.prompts.registry import get_pool
        pool = await get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT run_id, status, started_at, finished_at, output, error, latency_ms
                FROM task_runs
                WHERE task_id = $1::uuid
                ORDER BY started_at DESC
                LIMIT $2
                """,
                task_id, limit,
            )
        runs = [
            {
                "run_id":      str(r["run_id"]),
                "status":      r["status"],
                "started_at":  r["started_at"].isoformat() if r["started_at"] else None,
                "finished_at": r["finished_at"].isoformat() if r["finished_at"] else None,
                "output":      json.loads(r["output"]) if r["output"] else {},
                "error":       r["error"],
                "latency_ms":  r["latency_ms"],
            }
            for r in rows
        ]
        return {"task_id": task_id, "runs": runs, "total": len(runs)}
    except Exception as e:
        logger.error("get_task_runs failed: %s", e)
        raise HTTPException(status_code=500, detail="Unable to retrieve task runs.")
