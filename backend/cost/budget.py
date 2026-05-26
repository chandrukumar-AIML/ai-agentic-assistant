# backend/cost/budget.py
"""
Workspace budget management.
Tracks monthly spend, sends alerts at 80%, switches models at 100%.
"""
import logging
from dataclasses import dataclass
from typing import Optional

from backend.auth.models import PlanTier

logger = logging.getLogger(__name__)

# Monthly budget limits per plan tier (USD)
PLAN_BUDGETS: dict[PlanTier, float] = {
    PlanTier.FREE:       5.00,    # $5/month
    PlanTier.PRO:       50.00,    # $50/month
    PlanTier.ENTERPRISE: 500.00,  # $500/month (soft limit — alerts only)
}

ALERT_THRESHOLD   = 0.80   # alert at 80% of budget
HARD_LIMIT_FACTOR = 1.0    # block or downgrade at 100%


@dataclass
class BudgetStatus:
    workspace_id:    str
    plan_tier:       PlanTier
    monthly_budget:  float
    monthly_spend:   float
    remaining:       float
    pct_used:        float
    alert_triggered: bool
    hard_limit_hit:  bool
    recommended_model: str   # model to use given budget state


async def check_budget(
    workspace_id: str,
    plan_tier:    PlanTier,
    estimated_cost: float = 0.0,
) -> BudgetStatus:
    """
    Check workspace budget status.
    Returns recommended model based on budget state.
    """
    budget = PLAN_BUDGETS.get(plan_tier, PLAN_BUDGETS[PlanTier.FREE])

    # Get current monthly spend from PostgreSQL
    try:
        from backend.prompts.registry import get_pool
        pool = await get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT COALESCE(SUM(cost_usd), 0) AS monthly_spend
                FROM audit_log
                WHERE workspace_id = $1::uuid
                  AND action = 'llm_call'
                  AND timestamp >= DATE_TRUNC('month', NOW())
                """,
                workspace_id,
            )
        monthly_spend = float(row["monthly_spend"])
    except Exception as e:
        logger.warning(f"Budget check DB failed: {e} — assuming $0 spent")
        monthly_spend = 0.0

    pct_used       = monthly_spend / budget if budget > 0 else 0.0
    remaining      = max(0.0, budget - monthly_spend)
    alert_triggered = pct_used >= ALERT_THRESHOLD
    hard_limit_hit  = pct_used >= HARD_LIMIT_FACTOR

    # Recommend model based on budget state
    if hard_limit_hit and plan_tier != PlanTier.ENTERPRISE:
        recommended_model = "ollama"   # free fallback when over budget
        logger.warning(
            f"Budget hard limit hit for workspace {workspace_id[:8]}: "
            f"${monthly_spend:.2f}/${budget:.2f}"
        )
    elif alert_triggered:
        recommended_model = "gpt-4o-mini"   # downgrade to cheap model
        logger.warning(
            f"Budget alert ({pct_used:.0%}) for workspace {workspace_id[:8]}: "
            f"${monthly_spend:.2f}/${budget:.2f}"
        )
    else:
        recommended_model = "auto"   # normal routing

    return BudgetStatus(
        workspace_id=workspace_id,
        plan_tier=plan_tier,
        monthly_budget=budget,
        monthly_spend=round(monthly_spend, 4),
        remaining=round(remaining, 4),
        pct_used=round(pct_used, 4),
        alert_triggered=alert_triggered,
        hard_limit_hit=hard_limit_hit,
        recommended_model=recommended_model,
    )


async def send_budget_alert(
    workspace_id:   str,
    pct_used:       float,
    monthly_spend:  float,
    budget:         float,
):
    """
    Send budget alert.
    In production: email admin, Slack webhook, etc.
    For now: log prominently + store in Redis for UI polling.
    """
    from backend.session.redis_client import get_redis
    redis  = await get_redis()
    key    = f"budget_alert:{workspace_id}"

    alert = {
        "workspace_id":  workspace_id,
        "pct_used":      round(pct_used, 4),
        "monthly_spend": round(monthly_spend, 4),
        "budget":        round(budget, 4),
        "message":       (
            f"⚠️ Budget alert: {pct_used:.0%} of monthly budget used "
            f"(${monthly_spend:.2f} / ${budget:.2f})"
        ),
    }

    await redis.setex(key, 86400, str(alert))   # 24hr TTL

    logger.warning(
        f"BUDGET ALERT — workspace {workspace_id[:8]}: "
        f"{pct_used:.0%} used (${monthly_spend:.2f}/${budget:.2f})"
    )


async def get_budget_alerts(workspace_id: str) -> Optional[dict]:
    """Check if there's an active budget alert for this workspace."""
    from backend.session.redis_client import get_redis
    redis = await get_redis()
    raw   = await redis.get(f"budget_alert:{workspace_id}")
    if raw:
        import ast
        try:
            return ast.literal_eval(raw)
        except Exception:
            return None
    return None