# backend/prompts/prompt_loader.py
"""
Node-facing prompt API.
Agents use this instead of hardcoded strings.
Falls back to hardcoded defaults if DB is unavailable.
"""
import logging
from typing import Optional
from functools import lru_cache

from backend.prompts.ab_router import get_prompt_for_request, ABRoutingResult
from backend.prompts.registry  import get_active_prompt, PromptVersion

logger = logging.getLogger(__name__)

# ── Hardcoded fallbacks ─────────────────────────────────────────────────────
# These are the V1 prompts — used if DB is down or prompt not in registry
_FALLBACKS: dict[str, str] = {
    "synthesizer": """You are a precise AI assistant.

{memory_context}

Tool results:
{tool_results}

Sources:
{sources}

Query: {query}

Synthesise a comprehensive, accurate answer grounded in the tool results above.
Cite sources with [1], [2] notation where relevant.""",

    "planner": """You are a task planning agent. Based on the user's query and intent,
create a focused execution plan.

Query: {query}
Intent: {intent}
Retry #{retry_count} (error: {error})

Respond ONLY with valid JSON:
{{
  "plan": ["step 1", "step 2"],
  "selected_tools": ["tool_name"]
}}""",

    "reflection": """You are a quality critic evaluating an AI response.

Query: {query}
Tool results used: {tool_results}
Agent's answer: {answer}

Score 1-10 and identify problems.
Respond ONLY with JSON:
{{
  "score": 7,
  "verdict": "pass",
  "critique": "specific issues or None",
  "missing": [],
  "hallucinations": []
}}""",

    "supervisor": """You are a supervisor routing requests to specialist agents.

Team: research_agent, code_agent, vision_agent, memory_agent, planning_agent

Query: {query}
Has image: {has_image}
Memory: {memory_context}

Respond ONLY with JSON:
{{
  "routing_decision": "explanation",
  "workers": [{{"worker": "name", "sub_query": "task", "priority": 1}}],
  "parallel": true,
  "aggregation_strategy": "merge"
}}""",
}


class PromptLoader:
    """
    Retrieves prompts from registry with A/B routing.
    Falls back to hardcoded defaults on failure.
    Used by all agent nodes.
    """

    def __init__(self):
        self._session_variant_cache: dict[str, dict[str, ABRoutingResult]] = {}

    async def get(
        self,
        prompt_name: str,
        session_id:  str = "",
        user_id:     str = "",
        trace_id:    str = "",
    ) -> tuple[str, Optional[int]]:
        """
        Get prompt content + optional log_entry_id for A/B tracking.
        Returns: (prompt_content, log_entry_id_or_None)

        log_entry_id is used later when user gives feedback to attribute
        the score to the correct variant.
        """
        # Per-session caching: same session gets same variant throughout
        cache_key = f"{session_id}:{prompt_name}"
        if cache_key in self._session_variant_cache.get(session_id, {}):
            cached = self._session_variant_cache[session_id][cache_key]
            return cached.prompt.content, cached.log_entry_id

        try:
            result = await get_prompt_for_request(
                prompt_name=prompt_name,
                session_id=session_id,
                user_id=user_id,
                trace_id=trace_id,
            )
            # Cache for this session
            if session_id not in self._session_variant_cache:
                self._session_variant_cache[session_id] = {}
            self._session_variant_cache[session_id][cache_key] = result

            logger.debug(
                f"Prompt loaded: {prompt_name} "
                f"(variant={result.variant}, session={session_id[:8]})"
            )
            return result.prompt.content, result.log_entry_id

        except Exception as e:
            logger.warning(
                f"Prompt registry unavailable ({e}) — using fallback for {prompt_name}"
            )
            fallback = _FALLBACKS.get(prompt_name, f"You are a helpful AI. Query: {{query}}")
            return fallback, None

    async def get_content_only(self, prompt_name: str) -> str:
        """Simplified getter — no A/B tracking (for non-session contexts)."""
        content, _ = await self.get(prompt_name)
        return content

    def clear_session_cache(self, session_id: str):
        """Clear cached variants when session ends."""
        self._session_variant_cache.pop(session_id, None)


# Module-level singleton
prompt_loader = PromptLoader()


async def seed_default_prompts():
    """
    Seed the database with the current hardcoded prompts as v1.0.0.
    Run once after Phase G is deployed.
    """
    from backend.prompts.registry import create_prompt, get_active_prompt

    for name, content in _FALLBACKS.items():
        existing = await get_active_prompt(name)
        if existing:
            logger.info(f"Prompt {name} already in registry (v{existing.version})")
            continue

        await create_prompt(
            prompt_name=name,
            version="1.0.0",
            content=content,
            description=f"Initial version of {name} prompt — seeded from hardcoded defaults",
            created_by="seed_script",
            set_active=True,
        )
        logger.info(f"Seeded prompt: {name} v1.0.0")