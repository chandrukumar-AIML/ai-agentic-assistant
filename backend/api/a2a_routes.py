# backend/api/a2a_routes.py
"""
Google A2A Protocol REST API (Feature 2).

Endpoints:
  GET  /.well-known/agent.json             — agent card (public)
  POST /api/a2a/tasks                      — create A2A task
  GET  /api/a2a/tasks/{task_id}            — get task status/result
  GET  /api/a2a/tasks/{task_id}/stream     — SSE stream
  POST /api/a2a/tasks/{task_id}/cancel     — cancel task
  POST /api/a2a/adapters/{adapter}/{action}— invoke external adapter
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

from backend.api.auth    import verify_token
from backend.a2a.agent_card import get_agent_card
from backend.a2a.a2a_server  import (
    ADAPTER_MAP,
    A2ATask,
    create_task,
    get_task,
    stream_task,
)

logger = logging.getLogger(__name__)

# Two routers: public (agent card) and authenticated (tasks)
well_known_router = APIRouter(tags=["a2a"])
router            = APIRouter(prefix="/a2a", tags=["a2a"])


class TaskRequest(BaseModel):
    skill_id:   str  = Field(..., min_length=1, max_length=100)
    input_data: dict = Field(default_factory=dict)


class AdapterRequest(BaseModel):
    action:  str  = Field(..., min_length=1, max_length=100)
    payload: dict = Field(default_factory=dict)


@well_known_router.get(
    "/.well-known/agent.json",
    summary="A2A Agent Card (public)",
    response_class=JSONResponse,
)
async def agent_card():
    """
    Serve the A2A agent card.
    External agents discover capabilities by fetching this endpoint.
    """
    return get_agent_card()


@router.post(
    "/tasks",
    summary="Create A2A task",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=dict,
)
async def create_a2a_task(
    req:   TaskRequest,
    token: dict = Depends(verify_token),
):
    """Submit a task to this agent's skill system. Returns task_id immediately."""
    caller_id = token.get("sub", "anonymous")
    task = await create_task(
        skill_id=req.skill_id,
        input_data=req.input_data,
        caller_id=caller_id,
    )
    return {
        "task_id":    task.task_id,
        "skill_id":   task.skill_id,
        "status":     task.status,
        "stream_url": f"/api/a2a/tasks/{task.task_id}/stream",
    }


@router.get(
    "/tasks/{task_id}",
    summary="Get A2A task result",
    response_model=dict,
)
async def get_a2a_task(
    task_id: str,
    token:   dict = Depends(verify_token),
):
    task = get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")
    return task.to_dict()


@router.get(
    "/tasks/{task_id}/stream",
    summary="Stream A2A task output (SSE)",
)
async def stream_a2a_task(
    task_id: str,
    token:   dict = Depends(verify_token),
):
    """Server-Sent Events stream of task progress and output."""
    task = get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")
    return StreamingResponse(
        stream_task(task_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control":  "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.post(
    "/tasks/{task_id}/cancel",
    summary="Cancel A2A task",
    response_model=dict,
)
async def cancel_a2a_task(
    task_id: str,
    token:   dict = Depends(verify_token),
):
    task = get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")
    if task.status in (A2ATask.STATUS_COMPLETED, A2ATask.STATUS_FAILED):
        raise HTTPException(status_code=409, detail=f"Task already {task.status}.")
    task.status = A2ATask.STATUS_CANCELLED
    return {"task_id": task_id, "status": "cancelled"}


@router.post(
    "/adapters/{adapter_name}/{action}",
    summary="Invoke external system adapter",
    response_model=dict,
)
async def invoke_adapter(
    adapter_name: str,
    action:       str,
    req:          AdapterRequest,
    token:        dict = Depends(verify_token),
):
    """
    Invoke a mock adapter for Salesforce, SAP, or ServiceNow.
    In production, replace mock logic with real API calls.
    """
    adapter_fn = ADAPTER_MAP.get(adapter_name.lower())
    if not adapter_fn:
        raise HTTPException(
            status_code=404,
            detail=f"Adapter '{adapter_name}' not found. Available: {list(ADAPTER_MAP.keys())}",
        )
    result = await adapter_fn(action, req.payload)
    return result
