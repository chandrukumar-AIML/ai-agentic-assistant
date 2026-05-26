# backend/memory/memory_updater.py
"""
After each session, extract and store new memories.
Uses GPT-4o to identify facts worth remembering.
"""
import json
import logging

from backend.llm.ollama_openai import ollama_chat_completion, OLLAMA_MODEL
from backend.memory.memory_store import add_memory, MemoryType
from backend.config import get_settings
from backend.utils.text import strip_code_fence

logger   = logging.getLogger(__name__)
settings = get_settings()

EXTRACTION_PROMPT = """
You are a memory extraction system. Analyse this conversation and extract facts worth remembering.

Return a JSON object with three lists:
{{
  "episodic": [
    "Brief summary of what happened in this session (1-2 sentences)"
  ],
  "semantic": [
    "Fact about the user's role, preferences, domain, or working style"
  ],
  "procedural": [
    "Tool or strategy that worked well for this type of task"
  ]
}}

Rules:
- Each list can be empty [] if nothing new was learned
- Be specific and factual — no vague generalities
- Episodic: max 1 entry per session (the session summary)
- Semantic: only NEW facts not already known
- Procedural: only if a clear tool/strategy pattern emerged
- Total entries across all three: max 5

Conversation:
{conversation}

Known user facts (don't repeat these):
{known_facts}
"""


async def extract_and_store_memories(
    conversation:   list[dict],     # [{"role": "human"/"ai", "content": "..."}]
    user_id:        str,
    session_id:     str,
    known_facts:    list[str] | None = None,
) -> dict:
    """
    Extract memories from the conversation and store them.
    Returns summary of what was stored.
    """
    if not conversation:
        return {"stored": 0}

    # Format conversation for the prompt
    conv_text = "\n".join(
        f"{m['role'].upper()}: {m['content'][:300]}"
        for m in conversation[-20:]   # last 20 messages
    )
    known_str = "\n".join(known_facts or []) or "None yet"

    try:
        raw_response = await ollama_chat_completion(
            messages=[{"role": "user", "content": EXTRACTION_PROMPT.format(
                conversation=conv_text,
                known_facts=known_str,
            )}],
            model=OLLAMA_MODEL,
            temperature=0,
            max_tokens=600,
        )
        raw    = strip_code_fence(raw_response)
        parsed = json.loads(raw)
    except Exception as e:
        logger.error("Memory extraction LLM failed: %s", e)
        return {"stored": 0, "error": str(e)}

    stored = 0
    errors = []

    # Store episodic memories
    for content in parsed.get("episodic", []):
        if content.strip():
            mem_id = await add_memory(
                content=content,
                user_id=user_id,
                memory_type=MemoryType.EPISODIC,
                session_id=session_id,
            )
            if mem_id:
                stored += 1

    # Store semantic memories
    for content in parsed.get("semantic", []):
        if content.strip():
            mem_id = await add_memory(
                content=content,
                user_id=user_id,
                memory_type=MemoryType.SEMANTIC,
                session_id=session_id,
            )
            if mem_id:
                stored += 1

    # Store procedural memories
    for content in parsed.get("procedural", []):
        if content.strip():
            mem_id = await add_memory(
                content=content,
                user_id=user_id,
                memory_type=MemoryType.PROCEDURAL,
                session_id=session_id,
            )
            if mem_id:
                stored += 1

    logger.info(
        f"Memory update: {stored} memories stored for user {user_id} "
        f"session {session_id}"
    )
    return {"stored": stored, "breakdown": parsed, "errors": errors}