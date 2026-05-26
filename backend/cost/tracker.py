# backend/cost/tracker.py
"""
Token usage tracker and cost logger.
Counts tokens per call, accumulates workspace totals,
writes to PostgreSQL audit_log.
"""
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone

from backend.cost.classifier import estimate_cost, MODEL_PRICING

logger = logging.getLogger(__name__)


@dataclass
class TokenUsage:
    model:         str
    input_tokens:  int   = 0
    output_tokens: int   = 0
    cost_usd:      float = 0.0
    cached:        bool  = False
    latency_ms:    float = 0.0


@dataclass
class SessionCostAccumulator:
    """Tracks total cost across all LLM calls in one agent session."""
    session_id:     str
    workspace_id:   str
    calls:          list[TokenUsage] = field(default_factory=list)

    @property
    def total_input_tokens(self) -> int:
        return sum(c.input_tokens for c in self.calls)

    @property
    def total_output_tokens(self) -> int:
        return sum(c.output_tokens for c in self.calls)

    @property
    def total_cost_usd(self) -> float:
        return round(sum(c.cost_usd for c in self.calls), 6)

    @property
    def total_tokens(self) -> int:
        return self.total_input_tokens + self.total_output_tokens

    @property
    def cache_savings_usd(self) -> float:
        """Estimate savings from cache hits."""
        return round(sum(
            estimate_cost(c.input_tokens, c.output_tokens, c.model)
            for c in self.calls if c.cached
        ), 6)

    def add_call(self, usage: TokenUsage):
        self.calls.append(usage)

    def to_summary(self) -> dict:
        return {
            "session_id":          self.session_id,
            "total_calls":         len(self.calls),
            "total_input_tokens":  self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_tokens":        self.total_tokens,
            "total_cost_usd":      self.total_cost_usd,
            "cache_savings_usd":   self.cache_savings_usd,
            "models_used":         list({c.model for c in self.calls}),
        }


async def record_token_usage(
    workspace_id:  str,
    session_id:    str,
    trace_id:      str,
    model:         str,
    input_tokens:  int,
    output_tokens: int,
    cached:        bool = False,
) -> TokenUsage:
    """
    Record token usage for one LLM call.
    Writes to PostgreSQL and returns usage summary.
    """
    cost_usd = 0.0 if cached else estimate_cost(input_tokens, output_tokens, model)

    usage = TokenUsage(
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cost_usd=cost_usd,
        cached=cached,
    )

    # Write to audit_log (non-blocking)
    try:
        from backend.audit.audit_logger import log_agent_action
        log_agent_action(
            user_id=f"system:{session_id}",
            workspace_id=workspace_id,
            session_id=session_id,
            trace_id=trace_id,
            action="llm_call",
            model_used=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost_usd,
            metadata={
                "cached":       cached,
                "total_tokens": input_tokens + output_tokens,
            },
        )
    except Exception as e:
        logger.warning(f"Token tracking audit write failed: {e}")

    # Update workspace monthly cost in PostgreSQL
    if not cached and cost_usd > 0:
        try:
            from backend.prompts.registry import get_pool
            pool = await get_pool()
            async with pool.acquire() as conn:
                await conn.execute(
                    """
                    UPDATE workspaces
                    SET total_tokens_used = total_tokens_used + $1,
                        monthly_cost_usd  = monthly_cost_usd  + $2
                    WHERE id = $3::uuid
                    """,
                    input_tokens + output_tokens,
                    cost_usd,
                    workspace_id,
                )
        except Exception as e:
            logger.warning(f"Workspace cost update failed: {e}")

    logger.debug(
        f"Token usage: model={model} "
        f"in={input_tokens} out={output_tokens} "
        f"cost=${cost_usd:.5f} cached={cached}"
    )
    return usage


async def get_workspace_cost_report(
    workspace_id: str,
    days:         int = 30,
) -> dict:
    """Return cost breakdown for admin dashboard."""
    try:
        from backend.prompts.registry import get_pool
        pool = await get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT
                    DATE_TRUNC('day', timestamp) AS day,
                    model_used,
                    SUM(cost_usd)                AS daily_cost,
                    SUM(input_tokens)            AS daily_input,
                    SUM(output_tokens)           AS daily_output,
                    COUNT(*)                     AS call_count
                FROM audit_log
                WHERE workspace_id = $1::uuid
                  AND action = 'llm_call'
                  AND timestamp >= NOW() - $2 * INTERVAL '1 day'  -- FIXED: asyncpg doesn't substitute inside string literals
                GROUP BY day, model_used
                ORDER BY day DESC, daily_cost DESC
                """,
                workspace_id, days,
            )

            # Totals
            total_row = await conn.fetchrow(
                """
                SELECT
                    SUM(cost_usd)      AS total_cost,
                    SUM(input_tokens)  AS total_input,
                    SUM(output_tokens) AS total_output,
                    COUNT(*)           AS total_calls
                FROM audit_log
                WHERE workspace_id = $1::uuid
                  AND action = 'llm_call'
                  AND timestamp >= NOW() - $2 * INTERVAL '1 day'  -- FIXED: asyncpg doesn't substitute inside string literals
                """,
                workspace_id, days,
            )

    except Exception as e:
        logger.error(f"Cost report failed: {e}")
        return {"error": str(e)}

    daily_breakdown = {}
    model_breakdown = {}

    for row in rows:
        day   = row["day"].strftime("%Y-%m-%d") if row["day"] else "unknown"
        model = row["model_used"] or "unknown"
        cost  = float(row["daily_cost"] or 0)

        # Per-day
        if day not in daily_breakdown:
            daily_breakdown[day] = {"cost": 0.0, "calls": 0, "tokens": 0}
        daily_breakdown[day]["cost"]   += cost
        daily_breakdown[day]["calls"]  += int(row["call_count"] or 0)
        daily_breakdown[day]["tokens"] += int((row["daily_input"] or 0) + (row["daily_output"] or 0))

        # Per-model
        if model not in model_breakdown:
            model_breakdown[model] = {"cost": 0.0, "calls": 0}
        model_breakdown[model]["cost"]  += cost
        model_breakdown[model]["calls"] += int(row["call_count"] or 0)

    return {
        "period_days":      days,
        "total_cost_usd":   round(float(total_row["total_cost"]   or 0), 4),
        "total_tokens":     int((total_row["total_input"] or 0) + (total_row["total_output"] or 0)),
        "total_calls":      int(total_row["total_calls"]  or 0),
        "daily_breakdown":  daily_breakdown,
        "model_breakdown":  model_breakdown,
    }