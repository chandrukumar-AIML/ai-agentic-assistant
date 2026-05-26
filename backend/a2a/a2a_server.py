# backend/a2a/a2a_server.py
"""
Google A2A Protocol Server (Feature 2).

Implements the A2A request/response and streaming task protocol.

A2A Message Flow:
  1. External agent → POST /api/a2a/tasks         (create task)
  2. Server streams  → GET  /api/a2a/tasks/{id}/stream  (SSE)
  3. External agent  → GET  /api/a2a/tasks/{id}   (poll result)
  4. External agent  → POST /api/a2a/tasks/{id}/cancel

Skill dispatch: routes to the matching internal capability.
All tasks go through Guardian compliance check first.
"""
from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any, AsyncGenerator, Optional

from backend.config import get_settings

logger   = logging.getLogger(__name__)
settings = get_settings()

# In-memory task store (Redis-backed in production)
_tasks: dict[str, dict] = {}


class A2ATask:
    """Represents an A2A task lifecycle."""
    STATUS_PENDING    = "pending"
    STATUS_RUNNING    = "running"
    STATUS_COMPLETED  = "completed"
    STATUS_FAILED     = "failed"
    STATUS_CANCELLED  = "cancelled"

    def __init__(
        self,
        skill_id:   str,
        input_data: dict,
        caller_id:  str,
        session_id: str = "",
    ):
        self.task_id    = str(uuid.uuid4())
        self.skill_id   = skill_id
        self.input_data = input_data
        self.caller_id  = caller_id
        self.session_id = session_id or self.task_id
        self.status     = self.STATUS_PENDING
        self.output:    Optional[dict] = None
        self.error:     Optional[str]  = None
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.updated_at = self.created_at
        self.stream_chunks: list[dict] = []

    def to_dict(self) -> dict:
        return {
            "task_id":    self.task_id,
            "skill_id":   self.skill_id,
            "status":     self.status,
            "output":     self.output,
            "error":      self.error,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


# ── Skill dispatch ────────────────────────────────────────────────────────────

async def _dispatch_skill(task: A2ATask) -> AsyncGenerator[dict, None]:
    """
    Dispatch to the correct internal capability based on skill_id.
    Yields streaming chunks.
    """
    skill_id   = task.skill_id
    input_data = task.input_data

    # Guardian compliance check first
    try:
        from backend.agent.compliance_agent import guardian_check_input
        verdict, _ = await guardian_check_input(
            text=json.dumps(input_data),
            user_id=task.caller_id,
            session_id=task.session_id,
        )
        if verdict in ("REJECT", "ESCALATE_TO_HUMAN"):
            yield {"type": "error", "message": f"Compliance check failed: {verdict}"}
            return
    except Exception as e:
        logger.warning("A2A compliance check failed (non-fatal): %s", e)

    yield {"type": "status", "status": "running", "message": f"Executing skill: {skill_id}"}

    if skill_id == "rag_query":
        query = input_data.get("query", "")
        try:
            from backend.agent.graph import compile_graph
            from langgraph.checkpoint.memory import MemorySaver
            graph  = compile_graph(checkpointer=MemorySaver())
            state  = {
                "user_query": query, "user_id": task.caller_id,
                "session_id": task.session_id, "messages": [],
                "trace_id": task.task_id, "latency_ms": {},
            }
            result = await graph.ainvoke(
                state,
                config={"configurable": {"thread_id": task.task_id}},
            )
            yield {"type": "result", "answer": result.get("final_answer", ""), "sources": result.get("sources", [])}
        except Exception as e:
            yield {"type": "error", "message": f"RAG query failed: {e}"}

    elif skill_id == "web_search":
        query = input_data.get("query", "")
        try:
            from backend.agent.tools.web_search_tool import web_search
            results = await web_search(query)
            yield {"type": "result", "results": results}
        except Exception as e:
            yield {"type": "error", "message": f"Web search failed: {e}"}

    elif skill_id == "compliance_check":
        text = input_data.get("text", "")
        try:
            from backend.guardrails.compliance_checker import run_compliance_check
            verdict = await run_compliance_check(text, context={"user_id": task.caller_id})
            yield {"type": "result", **verdict.to_api_dict()}
        except Exception as e:
            yield {"type": "error", "message": f"Compliance check failed: {e}"}

    elif skill_id == "document_generation":
        fmt     = input_data.get("format", "pdf")
        payload = input_data.get("payload", {})
        try:
            from backend.outputs.output_generator import generate_output
            file_bytes, content_type, filename = await generate_output(fmt, payload)
            # Store file in temp and return URL (simplified)
            yield {"type": "result", "filename": filename, "content_type": content_type,
                   "size_bytes": len(file_bytes)}
        except Exception as e:
            yield {"type": "error", "message": f"Document generation failed: {e}"}

    elif skill_id == "hitl_approval":
        action_type = input_data.get("action_type", "a2a_action")
        context     = input_data.get("context", "")
        try:
            from backend.hitl.hitl_manager import request_approval
            approval_id = await request_approval(
                action_type=action_type, action_payload=input_data,
                context_summary=context, user_id=task.caller_id,
                session_id=task.session_id,
            )
            yield {"type": "result", "approval_id": approval_id, "status": "pending",
                   "message": "Awaiting human approval (30-min timeout)."}
        except Exception as e:
            yield {"type": "error", "message": f"HITL request failed: {e}"}

    elif skill_id == "gst_calculation":
        amount   = input_data.get("amount", 0)
        hsn_code = input_data.get("hsn_code", "")
        # GST calculation inline (no external call needed for basic rates)
        gst_rates = {"0%": 0.0, "5%": 0.05, "12%": 0.12, "18%": 0.18, "28%": 0.28}
        rate  = 0.18   # default 18% GST
        cgst  = round(amount * rate / 2, 2)
        sgst  = round(amount * rate / 2, 2)
        total = round(amount + cgst + sgst, 2)
        yield {"type": "result", "gst_amount": cgst + sgst, "cgst": cgst, "sgst": sgst,
               "total": total, "rate": f"{int(rate*100)}%", "hsn_code": hsn_code}

    else:
        yield {"type": "error", "message": f"Unknown skill_id: {skill_id!r}"}

    yield {"type": "done", "task_id": task.task_id}


# ── Adapter stubs ────────────────────────────────────────────────────────────

async def salesforce_adapter(action: str, payload: dict) -> dict:
    """Mock Salesforce adapter — replace with real Salesforce REST API calls."""
    await asyncio.sleep(0.1)   # simulate network
    if action == "create_lead":
        return {"success": True, "lead_id": f"SFDC-{uuid.uuid4().hex[:8].upper()}", "mock": True}
    if action == "get_opportunity":
        return {"id": payload.get("id"), "name": "Mock Opportunity", "stage": "Prospecting", "mock": True}
    return {"error": f"Unknown Salesforce action: {action}", "mock": True}


async def sap_adapter(action: str, payload: dict) -> dict:
    """Mock SAP ERP adapter."""
    await asyncio.sleep(0.1)
    if action == "get_inventory":
        return {"material": payload.get("material_id"), "quantity": 500, "unit": "EA", "mock": True}
    if action == "create_purchase_order":
        return {"po_number": f"PO-{uuid.uuid4().hex[:8].upper()}", "status": "created", "mock": True}
    return {"error": f"Unknown SAP action: {action}", "mock": True}


async def servicenow_adapter(action: str, payload: dict) -> dict:
    """Mock ServiceNow ITSM adapter."""
    await asyncio.sleep(0.1)
    if action == "create_incident":
        return {"incident_id": f"INC{uuid.uuid4().hex[:6].upper()}", "state": "New", "mock": True}
    if action == "get_ticket":
        return {"ticket_id": payload.get("id"), "state": "In Progress", "priority": "2-High", "mock": True}
    return {"error": f"Unknown ServiceNow action: {action}", "mock": True}


ADAPTER_MAP = {
    "salesforce":  salesforce_adapter,
    "sap":         sap_adapter,
    "servicenow":  servicenow_adapter,
}


# ── Task manager ─────────────────────────────────────────────────────────────

async def create_task(skill_id: str, input_data: dict, caller_id: str) -> A2ATask:
    task = A2ATask(skill_id=skill_id, input_data=input_data, caller_id=caller_id)
    _tasks[task.task_id] = task

    # Run async in background
    asyncio.create_task(_run_task(task))
    return task


async def _run_task(task: A2ATask) -> None:
    task.status     = A2ATask.STATUS_RUNNING
    task.updated_at = datetime.now(timezone.utc).isoformat()

    try:
        async for chunk in _dispatch_skill(task):
            task.stream_chunks.append(chunk)
            if chunk.get("type") == "result":
                task.output = chunk
            elif chunk.get("type") == "error":
                task.error  = chunk.get("message")
        task.status = A2ATask.STATUS_COMPLETED
    except Exception as e:
        task.status = A2ATask.STATUS_FAILED
        task.error  = str(e)
        logger.error("A2A task %s failed: %s", task.task_id, e)

    task.updated_at = datetime.now(timezone.utc).isoformat()


def get_task(task_id: str) -> Optional[A2ATask]:
    return _tasks.get(task_id)


async def stream_task(task_id: str) -> AsyncGenerator[str, None]:
    """SSE stream of task chunks."""
    task = _tasks.get(task_id)
    if not task:
        yield f"data: {json.dumps({'type': 'error', 'message': 'Task not found'})}\n\n"
        return

    sent = 0
    while task.status in (A2ATask.STATUS_PENDING, A2ATask.STATUS_RUNNING):
        while sent < len(task.stream_chunks):
            chunk = task.stream_chunks[sent]
            yield f"data: {json.dumps(chunk)}\n\n"
            sent += 1
        await asyncio.sleep(0.1)

    # Flush remaining
    while sent < len(task.stream_chunks):
        chunk = task.stream_chunks[sent]
        yield f"data: {json.dumps(chunk)}\n\n"
        sent += 1

    yield f"data: {json.dumps({'type': 'done', 'status': task.status, 'task_id': task_id})}\n\n"
