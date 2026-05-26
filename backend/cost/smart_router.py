# backend/cost/smart_router.py
"""
Cost-aware LLM router.
Wraps the existing llm_router with:
  - Complexity-based model selection
  - Redis response caching
  - Budget enforcement
  - Token tracking
"""
import logging
import time
from typing import AsyncGenerator, Optional

from backend.cost.classifier   import classify_query, Complexity, COMPLEXITY_TO_MODEL
from backend.cost.cache        import get_cached_response, cache_response
from backend.cost.tracker      import record_token_usage, TokenUsage
from backend.cost.budget       import check_budget, send_budget_alert
from backend.llm.router        import llm_router
from backend.auth.models       import PlanTier

logger = logging.getLogger(__name__)


class SmartRouter:
    """
    Drop-in replacement for llm_router that adds cost optimisation.
    Falls back to standard llm_router for any unhandled case.
    """

    async def complete(
        self,
        messages:      list[dict],
        temperature:   float  = 0.3,
        max_tokens:    int    = 1000,
        stream:        bool   = False,
        # Cost context
        query:         str    = "",
        has_image:     bool   = False,
        intent:        str    = "",
        tool_count:    int    = 1,
        workspace_id:  str    = "",
        session_id:    str    = "",
        trace_id:      str    = "",
        plan_tier:     PlanTier = PlanTier.FREE,
        force_model:   str | None = None,
    ) -> tuple[str | AsyncGenerator, str, TokenUsage]:
        """
        Cost-aware LLM completion.

        Returns: (response, model_used, token_usage)

        Added return value vs standard llm_router:
          token_usage: TokenUsage with cost data for the caller
        """
        start = time.monotonic()

        # ── 1. Classify complexity ─────────────────────────────────────────
        if force_model:
            selected_model = force_model
            classification = None
        else:
            classification = classify_query(
                query=query or (messages[-1].get("content", "") if messages else ""),
                has_image=has_image,
                intent=intent,
                tool_count=tool_count,
            )
            selected_model = classification.model
            logger.debug(
                f"Smart router: complexity={classification.complexity} "
                f"model={selected_model} "
                f"reasons={classification.reasons[:1]}"
            )

        # ── 2. Budget check ────────────────────────────────────────────────
        if workspace_id:
            budget_status = await check_budget(workspace_id, plan_tier)

            if budget_status.hard_limit_hit and plan_tier != PlanTier.ENTERPRISE:
                # Override: force free model
                selected_model = "ollama"
                logger.warning(
                    f"Budget limit hit — forcing ollama for workspace {workspace_id[:8]}"
                )
            elif budget_status.alert_triggered and selected_model == "gpt-4o":
                # Downgrade to mini when approaching budget limit
                selected_model = "gpt-4o-mini"
                logger.info(
                    f"Budget alert active — downgrading gpt-4o → gpt-4o-mini "
                    f"for workspace {workspace_id[:8]}"
                )

            if budget_status.alert_triggered:
                await send_budget_alert(
                    workspace_id=workspace_id,
                    pct_used=budget_status.pct_used,
                    monthly_spend=budget_status.monthly_spend,
                    budget=budget_status.monthly_budget,
                )

        # ── 3. Cache check (exact match, temperature=0 only) ──────────────
        user_query = query or (messages[-1].get("content", "") if messages else "")
        system_prompt = next(
            (m.get("content", "") for m in messages if m.get("role") == "system"),
            "",
        )

        if not stream and temperature <= 0.1:
            cached = await get_cached_response(
                query=user_query,
                model=selected_model,
                temperature=temperature,
                system_prompt=system_prompt[:100],
            )
            if cached:
                usage = TokenUsage(
                    model=selected_model,
                    input_tokens=cached.get("input_tokens", 0),
                    output_tokens=cached.get("output_tokens", 0),
                    cost_usd=0.0,
                    cached=True,
                    latency_ms=(time.monotonic() - start) * 1000,
                )
                logger.info(
                    f"Cache HIT: saved ${cached.get('cost_usd', 0):.5f} "
                    f"model={selected_model}"
                )
                return cached["response"], selected_model, usage

        # ── 4. Execute LLM call with selected model ────────────────────────
        response, model_used = await llm_router.complete(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=stream,
            force_model=(
                "openai" if selected_model in ("gpt-4o", "gpt-4o-mini")
                else "ollama" if "ollama" in selected_model
                else None
            ),
        )

        # For non-streaming: count tokens and cache
        if not stream and isinstance(response, str):
            # Estimate token counts (actual counts need tiktoken or API response)
            input_tokens  = self._estimate_tokens(messages)
            output_tokens = self._estimate_tokens_str(response)

            from backend.cost.classifier import estimate_cost
            cost_usd = estimate_cost(input_tokens, output_tokens, selected_model)

            # Track usage
            usage = await record_token_usage(
                workspace_id=workspace_id or "unknown",
                session_id=session_id,
                trace_id=trace_id,
                model=selected_model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
            )
            usage.latency_ms = (time.monotonic() - start) * 1000

            # Write to cache
            await cache_response(
                query=user_query,
                response=response,
                model=selected_model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=cost_usd,
                temperature=temperature,
                system_prompt=system_prompt[:100],
            )

            return response, selected_model, usage

        # Streaming — return without cache/tracking (tracked by caller)
        usage = TokenUsage(model=selected_model)
        return response, selected_model, usage

    def _estimate_tokens(self, messages: list[dict]) -> int:
        """Rough token estimation: ~4 chars per token."""
        total_chars = sum(len(m.get("content", "")) for m in messages)
        return max(1, total_chars // 4)

    def _estimate_tokens_str(self, text: str) -> int:
        return max(1, len(text) // 4)


# Module-level singleton
smart_router = SmartRouter()