# backend/agents/memory_agent.py
"""
Memory Agent: manages Mem0 read/write, conversation summarisation,
user fact extraction, memory reports.
"""
import time
import logging
from typing import Any

from backend.agent.base_agent   import BaseWorkerAgent, WorkerResult
from backend.memory.memory_store import (
    search_memories, get_all_memories,
    add_memory, MemoryType,
)

logger = logging.getLogger(__name__)


class MemoryAgent(BaseWorkerAgent):
    name        = "memory_agent"
    description = (
        "Manages user memory — reads past context, extracts user facts, "
        "summarises conversations. Best for: what do you know about me, "
        "remember this, forget this, memory-heavy personalisation tasks."
    )

    @property
    def system_prompt(self) -> str:
        return """You are a Memory Management Agent. You manage what the AI system knows about users.

Your responsibilities:
1. Retrieve and present relevant memories clearly
2. Extract facts worth remembering from conversations
3. Summarise long conversation histories concisely
4. Generate personalised memory reports
5. Identify gaps in what is known about a user

Format memories clearly:
- Use bullet points for facts
- Group by category (professional, personal, preferences, domain)
- Note confidence level if uncertain
- Flag contradictions between memories"""

    async def run(
        self,
        query:          str,
        context:        dict[str, Any],
        memory_context: str = "",
    ) -> WorkerResult:
        start   = time.monotonic()
        user_id = context.get("user_id", "anonymous")
        q_lower = query.lower()

        # ── Determine memory task ──────────────────────────────────────────
        is_report    = any(w in q_lower for w in ["report", "summary", "what do you know", "tell me about me"])
        is_search    = any(w in q_lower for w in ["remember", "recall", "forgot", "previous"])
        is_store     = any(w in q_lower for w in ["store this", "remember that", "save this", "note that"])

        parts = []

        if is_store:
            # Extract what to remember
            store_prompt = (
                f"The user wants you to remember something from this message:\n'{query}'\n\n"
                f"Extract the exact fact to store as a memory. "
                f"Return just the fact, nothing else."
            )
            fact = await self._call_llm(
                user_content=store_prompt,
                temperature=0,
                max_tokens=100,
            )
            if fact.strip():
                mem_id = await add_memory(
                    content=fact.strip(),
                    user_id=user_id,
                    memory_type=MemoryType.SEMANTIC,
                )
                parts.append(
                    f"✅ Stored memory: '{fact.strip()}'" if mem_id
                    else "❌ Failed to store memory."
                )

        if is_report or is_search:
            # Retrieve all memories for report
            all_mems = await get_all_memories(user_id=user_id, limit=50)
            if not all_mems:
                parts.append("No memories found yet. Chat more so I can learn about you!")
            else:
                # Group by type
                grouped: dict[str, list[str]] = {
                    "episodic":   [],
                    "semantic":   [],
                    "procedural": [],
                }
                for m in all_mems:
                    mem_type = m.get("metadata", {}).get("memory_type", "semantic")
                    content  = m.get("memory") or m.get("content", "")
                    if mem_type in grouped:
                        grouped[mem_type].append(content)
                    else:
                        grouped["semantic"].append(content)

                mem_text = ""
                if grouped["episodic"]:
                    mem_text += "**Past Sessions:**\n" + "\n".join(f"• {m}" for m in grouped["episodic"]) + "\n\n"
                if grouped["semantic"]:
                    mem_text += "**What I Know About You:**\n" + "\n".join(f"• {m}" for m in grouped["semantic"]) + "\n\n"
                if grouped["procedural"]:
                    mem_text += "**Effective Strategies:**\n" + "\n".join(f"• {m}" for m in grouped["procedural"])

                # Generate report via LLM
                report = await self._call_llm(
                    user_content=(
                        f"Query: {query}\n\n"
                        f"Here are all memories for this user:\n{mem_text}\n\n"
                        f"Generate a clear, organised summary answering the query."
                    ),
                    system_content=self.system_prompt,
                    temperature=0.2,
                    max_tokens=800,
                )
                parts.append(report)

        if not parts:
            # General memory search
            results = await search_memories(query=query, user_id=user_id, limit=5)
            if results:
                content_list = [
                    m.get("memory") or m.get("content", "") for m in results
                ]
                parts.append(
                    "Relevant memories:\n" +
                    "\n".join(f"• {c}" for c in content_list if c)
                )
            else:
                parts.append(
                    "I don't have relevant memories for that query yet. "
                    "Tell me more so I can remember!"
                )

        return WorkerResult(
            worker_name="memory_agent",
            content="\n\n".join(parts),
            confidence=0.88,
            metadata={"user_id": user_id, "task": "report" if is_report else "search"},
            latency_ms=(time.monotonic() - start) * 1000,
        )