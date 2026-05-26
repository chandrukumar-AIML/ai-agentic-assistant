# backend/agent/nodes/memory_updater_node.py
"""
LangGraph node: updates memory after the agent responds.
Runs AFTER response_streamer — non-blocking fire-and-forget.
"""
import asyncio
import logging
from backend.agent.state import AgentState
from backend.memory.memory_updater import extract_and_store_memories
from backend.memory.memory_store import search_memories, MemoryType

logger = logging.getLogger(__name__)


async def memory_updater_node(state: AgentState) -> dict:
    """
    Post-session memory update.
    Extracts and stores new memories from this conversation.
    Non-blocking — failures never affect the response.
    """
    user_id = state.get("user_id", "anonymous")

    if user_id == "anonymous":
        return {}

    # Build conversation history from messages
    conversation = [
        {
            "role":    "human" if msg.__class__.__name__ == "HumanMessage" else "ai",
            "content": msg.content,
        }
        for msg in state.get("messages", [])
        if hasattr(msg, "content")
    ]

    # Get existing semantic facts to avoid duplication
    try:
        existing = await search_memories(
            query="user facts preferences",
            user_id=user_id,
            memory_type=MemoryType.SEMANTIC,
            limit=20,
        )
        known_facts = [
            m.get("memory") or m.get("content", "")
            for m in existing
        ]
    except Exception as e:  # FIXED: bare except silently swallowed errors
        logger.warning(f"Memory updater: failed to fetch existing memories (non-fatal): {e}")
        known_facts = []

    # Fire and forget — don't block the response stream
    asyncio.create_task(
        extract_and_store_memories(
            conversation=conversation,
            user_id=user_id,
            session_id=state.get("session_id", ""),
            known_facts=known_facts,
        )
    )

    return {}