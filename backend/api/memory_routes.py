# backend/api/memory_routes.py
"""
Memory CRUD endpoints.
Users can view and delete their own memories.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

from backend.api.auth import verify_token

logger = logging.getLogger(__name__)
from backend.memory.memory_store import (
    get_all_memories,
    delete_memory,
    delete_all_memories,
    add_memory,
    MemoryType,
)

router = APIRouter(prefix="/memory", tags=["memory"])


class MemoryCreateRequest(BaseModel):
    content:     str
    memory_type: MemoryType = MemoryType.SEMANTIC
    session_id:  Optional[str] = None


class MemoryDeleteRequest(BaseModel):
    memory_id: str


@router.get("/{user_id}")
async def get_memories(
    user_id: str,
    limit:   int  = 50,
    token:   dict = Depends(verify_token),
):
    """Return all memories for a user — for the React memory panel."""
    # FIXED: Enforce that users can only read their own memories
    requesting_user = token.get("sub", "")
    requesting_role = token.get("role", "user")
    if requesting_user != user_id and requesting_role != "admin":
        from fastapi import HTTPException
        raise HTTPException(403, "Forbidden: cannot access another user's memories")
    try:
        memories = await get_all_memories(user_id=user_id, limit=limit)
    except Exception as e:
        logger.warning("Memory store unavailable: %s", e)
        return {"user_id": user_id, "total": 0, "memories": {"episodic": [], "semantic": [], "procedural": []}, "unavailable": True}

    # Group by type for the UI
    grouped = {"episodic": [], "semantic": [], "procedural": []}
    for m in memories:
        mem_type = m.get("metadata", {}).get("memory_type", "semantic")
        content  = m.get("memory") or m.get("content", "")
        entry    = {
            "id":         m.get("id", ""),
            "content":    content,
            "created_at": m.get("created_at", ""),
        }
        if mem_type in grouped:
            grouped[mem_type].append(entry)
        else:
            grouped["semantic"].append(entry)

    return {
        "user_id":  user_id,
        "total":    len(memories),
        "memories": grouped,
    }


@router.delete("/{user_id}/{memory_id}")
async def delete_single_memory(
    user_id:   str,
    memory_id: str,
    token:     dict = Depends(verify_token),
):
    """Delete a specific memory (user privacy control)."""
    # FIXED: Authorization check
    requesting_user = token.get("sub", "")
    requesting_role = token.get("role", "user")
    if requesting_user != user_id and requesting_role != "admin":
        from fastapi import HTTPException
        raise HTTPException(403, "Forbidden: cannot delete another user's memories")
    ok = await delete_memory(memory_id=memory_id, user_id=user_id)
    if not ok:
        raise HTTPException(404, "Memory not found or could not be deleted")
    return {"deleted": True, "memory_id": memory_id}


@router.delete("/{user_id}")
async def delete_all_user_memories(
    user_id: str,
    token:   dict = Depends(verify_token),
):
    """Delete ALL memories for a user — full privacy reset."""
    # FIXED: Authorization check
    requesting_user = token.get("sub", "")
    requesting_role = token.get("role", "user")
    if requesting_user != user_id and requesting_role != "admin":
        from fastapi import HTTPException
        raise HTTPException(403, "Forbidden: cannot delete another user's memories")
    ok = await delete_all_memories(user_id=user_id)
    if not ok:
        raise HTTPException(500, "Failed to delete memories")
    return {"deleted": True, "user_id": user_id, "message": "All memories cleared"}


@router.post("/{user_id}")
async def add_manual_memory(
    user_id: str,
    body:    MemoryCreateRequest,
    token:   dict = Depends(verify_token),
):
    """Manually add a memory (for testing or user-provided context)."""
    mem_id = await add_memory(
        content=body.content,
        user_id=user_id,
        memory_type=body.memory_type,
        session_id=body.session_id,
    )
    if not mem_id:
        raise HTTPException(500, "Failed to add memory")
    return {"added": True, "memory_id": mem_id}