# backend/memory/memory_retriever.py
"""
Retrieves all three memory types and formats them
into a system prompt injection block.
"""
import logging
from backend.memory.memory_store import (
    search_memories, MemoryType
)
from backend.config import get_settings

logger   = logging.getLogger(__name__)
settings = get_settings()

MAX_MEMORY_TOKENS = 500   # approximate — each memory ~20 tokens avg


def _format_memories(memories: list[dict], label: str) -> str:
    if not memories:
        return ""
    lines = [f"[{label}]"]
    for m in memories:
        content = m.get("memory") or m.get("content") or str(m)
        lines.append(f"  • {content}")
    return "\n".join(lines)


async def build_memory_context(
    query:      str,
    user_id:    str,
    session_id: str,
) -> str:
    """
    Retrieve relevant memories across all three types.
    Returns a formatted string to inject into the system prompt.

    Example output:
    ─── AGENT MEMORY ───────────────────────────────
    [Episodic — recent sessions]
      • Last session: debugged FastAPI JWT 401 error
      • Two sessions ago: built a LangGraph RAG pipeline

    [Semantic — user facts]
      • User is a Python developer
      • Works in fintech / banking domain
      • Prefers async code patterns
      • Dislikes verbose explanations

    [Procedural — effective strategies]
      • For API questions: RAG tool finds docs faster than web search
      • For code debugging: always run code first, then explain
    ────────────────────────────────────────────────
    """
    # Retrieve all three types in parallel (conceptually — Mem0 is sync)
    episodic_mems = await search_memories(
        query=query,
        user_id=user_id,
        memory_type=MemoryType.EPISODIC,
        limit=5,
    )
    semantic_mems = await search_memories(
        query=query,
        user_id=user_id,
        memory_type=MemoryType.SEMANTIC,
        limit=5,
    )
    procedural_mems = await search_memories(
        query=query,
        user_id=user_id,
        memory_type=MemoryType.PROCEDURAL,
        limit=3,
    )

    sections = []
    ep  = _format_memories(episodic_mems,   "Episodic — recent sessions")
    sem = _format_memories(semantic_mems,   "Semantic — user facts")
    pro = _format_memories(procedural_mems, "Procedural — effective strategies")

    if ep:  sections.append(ep)
    if sem: sections.append(sem)
    if pro: sections.append(pro)

    if not sections:
        return ""

    body = "\n\n".join(sections)
    return (
        f"\n─── AGENT MEMORY ───────────────────────────────\n"
        f"{body}\n"
        f"────────────────────────────────────────────────\n"
    )