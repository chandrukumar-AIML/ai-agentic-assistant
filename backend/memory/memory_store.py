# backend/memory/memory_store.py
"""
Three memory types:
  Episodic   — what happened in past conversations
  Semantic   — facts about the user (preferences, role, domain)
  Procedural — which tool strategies worked for which task types
"""
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Optional
from datetime import datetime

from backend.memory.mem0_client import get_mem0

logger = logging.getLogger(__name__)


class MemoryType(str, Enum):
    EPISODIC   = "episodic"
    SEMANTIC   = "semantic"
    PROCEDURAL = "procedural"


@dataclass
class MemoryEntry:
    content:     str
    memory_type: MemoryType
    user_id:     str
    session_id:  Optional[str] = None
    metadata:    Optional[dict] = None
    created_at:  Optional[datetime] = None


async def add_memory(
    content:     str,
    user_id:     str,
    memory_type: MemoryType,
    session_id:  Optional[str] = None,
    metadata:    Optional[dict] = None,
) -> str | None:
    """
    Add a memory to Mem0.
    Returns memory_id or None on failure.
    """
    mem0 = get_mem0()
    meta = {
        "memory_type": memory_type.value,
        "session_id":  session_id or "",
        **(metadata or {}),
    }
    try:
        messages = [{"role": "user", "content": content}]
        result   = mem0.add(messages, user_id=user_id, metadata=meta)
        memory_id = (
            result[0]["id"]
            if isinstance(result, list) and result
            else result.get("id")
        )
        logger.debug(f"Memory added: {memory_type.value} for {user_id}: {content[:60]}")
        return memory_id
    except Exception as e:
        logger.error(f"Failed to add memory: {e}")
        return None


async def search_memories(
    query:       str,
    user_id:     str,
    memory_type: Optional[MemoryType] = None,
    limit:       int = 10,
) -> list[dict]:
    """
    Search relevant memories for a query.
    Optionally filter by memory type.
    """
    mem0 = get_mem0()
    try:
        filters = {}
        if memory_type:
            filters["metadata"] = {"memory_type": memory_type.value}

        results = mem0.search(
            query=query,
            user_id=user_id,
            limit=limit,
            filters=filters if filters else None,
        )
        return results if isinstance(results, list) else results.get("results", [])
    except Exception as e:
        logger.error(f"Memory search failed: {e}")
        return []


async def get_all_memories(user_id: str, limit: int = 50) -> list[dict]:
    """Retrieve all memories for a user (for the React memory panel)."""
    mem0 = get_mem0()
    try:
        results = mem0.get_all(user_id=user_id, limit=limit)
        return results if isinstance(results, list) else results.get("results", [])
    except Exception as e:
        logger.error(f"Get all memories failed: {e}")
        return []


async def delete_memory(memory_id: str, user_id: str) -> bool:
    """Delete a specific memory (privacy — user-initiated)."""
    mem0 = get_mem0()
    try:
        mem0.delete(memory_id=memory_id, user_id=user_id)
        logger.info(f"Memory deleted: {memory_id} for user {user_id}")
        return True
    except Exception as e:
        logger.error(f"Memory delete failed: {e}")
        return False


async def delete_all_memories(user_id: str) -> bool:
    """Delete ALL memories for a user (full privacy reset)."""
    mem0 = get_mem0()
    try:
        mem0.delete_all(user_id=user_id)
        logger.info(f"All memories deleted for user {user_id}")
        return True
    except Exception as e:
        logger.error(f"Delete all memories failed: {e}")
        return False