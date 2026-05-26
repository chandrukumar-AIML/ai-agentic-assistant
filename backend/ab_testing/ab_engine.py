# backend/ab_testing/ab_engine.py
"""
Agent A/B Testing Framework (Feature 12).

Extends the prompt-level ab_router with full model-level experimentation:
  1. Run queries through two LLM models simultaneously
  2. Track latency, cost, token usage, quality scores per turn
  3. Welch's t-test for statistical significance (scipy.stats.ttest_ind)
  4. Cohen's d effect size computation
  5. Auto-promote winner to LLM router preference when p < 0.05
  6. MLflow experiment tracking for every evaluation run
  7. Admin API for creating/monitoring/promoting experiments

Supported model pairs (examples):
  gpt-4o      vs  gpt-4o-mini
  gpt-4o      vs  llama3 (via Ollama)
  gpt-4o-mini vs  claude-3-haiku (via Anthropic)

Cost constants (USD per 1k tokens — update as pricing changes):
  gpt-4o:       input=0.005  output=0.015
  gpt-4o-mini:  input=0.00015 output=0.0006
  llama3:       input=0.0    output=0.0    (self-hosted, no cost)
"""
from __future__ import annotations

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from backend.config import get_settings

logger   = logging.getLogger(__name__)
settings = get_settings()

# ── Model cost table (USD per 1k tokens) ─────────────────────────────────────

_COST_TABLE: dict[str, dict[str, float]] = {
    "gpt-4o":               {"input": 0.005,   "output": 0.015},
    "gpt-4o-mini":          {"input": 0.00015, "output": 0.0006},
    "gpt-4-turbo":          {"input": 0.01,    "output": 0.03},
    "gpt-3.5-turbo":        {"input": 0.0005,  "output": 0.0015},
    "claude-3-haiku":       {"input": 0.00025, "output": 0.00125},
    "claude-3-sonnet":      {"input": 0.003,   "output": 0.015},
    "llama3":               {"input": 0.0,     "output": 0.0},
    "llama3:8b":            {"input": 0.0,     "output": 0.0},
    "llama3:70b":           {"input": 0.0,     "output": 0.0},
    "mistral":              {"input": 0.0,     "output": 0.0},
}

def compute_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    """Compute USD cost for a single inference call."""
    costs = _COST_TABLE.get(model, {"input": 0.005, "output": 0.015})
    return (
        prompt_tokens     / 1000 * costs["input"] +
        completion_tokens / 1000 * costs["output"]
    )


# ── Data models ───────────────────────────────────────────────────────────────

@dataclass
class ExperimentTurn:
    """Single inference record for one model in an A/B turn."""
    variant:            str     # "A" or "B"
    model:              str
    query:              str
    response:           str
    latency_ms:         int
    prompt_tokens:      int
    completion_tokens:  int
    cost_usd:           float
    quality_score:      Optional[float] = None
    thumbs_up:          Optional[bool]  = None


@dataclass
class ABRunResult:
    """Paired result from running one query through both variants."""
    experiment_id: str
    turn_a_id:     int
    turn_b_id:     int
    turn_a:        ExperimentTurn
    turn_b:        ExperimentTurn
    served_variant: str   # which variant the user actually received


@dataclass
class SignificanceResult:
    """Statistical significance analysis for an experiment."""
    experiment_id:  str
    n_a:            int
    n_b:            int
    mean_a:         float
    mean_b:         float
    std_a:          float
    std_b:          float
    t_statistic:    float
    p_value:        float
    cohen_d:        float
    is_significant: bool     # p < 0.05
    winner:         Optional[str]  # "A", "B", or None (too close)
    winner_model:   Optional[str]
    interpretation: str


# ── Core inference runner ─────────────────────────────────────────────────────

async def _call_openai(
    model:         str,
    system_prompt: str,
    user_query:    str,
) -> tuple[str, int, int, int]:
    """
    Call OpenAI-compatible API. Returns (response_text, latency_ms, prompt_tokens, completion_tokens).
    For Ollama/local models, falls through to _call_ollama().
    """
    if model.startswith("llama") or model.startswith("mistral"):
        return await _call_ollama(model, system_prompt, user_query)

    from openai import AsyncOpenAI
    client = AsyncOpenAI(api_key=settings.openai_api_key)

    t0 = time.monotonic()
    try:
        resp = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt or "You are a helpful assistant."},
                {"role": "user",   "content": user_query},
            ],
            max_tokens=800,
            temperature=0.7,
        )
        latency_ms        = int((time.monotonic() - t0) * 1000)
        text              = resp.choices[0].message.content or ""
        prompt_tokens     = resp.usage.prompt_tokens if resp.usage else 0
        completion_tokens = resp.usage.completion_tokens if resp.usage else 0
        return text, latency_ms, prompt_tokens, completion_tokens
    except Exception as e:
        latency_ms = int((time.monotonic() - t0) * 1000)
        logger.error("OpenAI call failed (%s): %s", model, e)
        return f"[Error: {type(e).__name__}]", latency_ms, 0, 0


async def _call_ollama(
    model:         str,
    system_prompt: str,
    user_query:    str,
) -> tuple[str, int, int, int]:
    """Call local Ollama instance for open-source models."""
    import httpx
    ollama_url = getattr(settings, "ollama_base_url", "http://localhost:11434")
    t0 = time.monotonic()
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{ollama_url}/api/chat",
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system_prompt or "You are a helpful assistant."},
                        {"role": "user",   "content": user_query},
                    ],
                    "stream": False,
                },
            )
            resp.raise_for_status()
            data = resp.json()
        latency_ms        = int((time.monotonic() - t0) * 1000)
        text              = data.get("message", {}).get("content", "")
        prompt_eval_count = data.get("prompt_eval_count", 0)
        eval_count        = data.get("eval_count", 0)
        return text, latency_ms, prompt_eval_count, eval_count
    except Exception as e:
        latency_ms = int((time.monotonic() - t0) * 1000)
        logger.warning("Ollama call failed (%s): %s — using mock", model, e)
        # Return a mock so the experiment can still log the turn
        mock = f"[Ollama mock for {model}: {user_query[:60]}...]"
        return mock, latency_ms, len(user_query.split()), 50


# ── LLM-as-Judge quality scorer ───────────────────────────────────────────────

async def _score_response(query: str, response: str) -> float:
    """
    Use Ollama as an automated judge.
    Scores 0.0–1.0 based on correctness, helpfulness, and conciseness.
    Falls back to 0.5 if unavailable.
    """
    try:
        from backend.llm.ollama_openai import ollama_chat_completion, OLLAMA_MODEL
        judge_prompt = (
            "You are an impartial AI judge. Rate the following AI response on a scale of 0.0 to 1.0 "
            "(0=terrible, 0.5=acceptable, 1.0=excellent). "
            "Consider: accuracy, helpfulness, clarity, and conciseness. "
            "Reply with ONLY a decimal number between 0.0 and 1.0. No other text."
        )
        raw = await ollama_chat_completion(
            messages=[
                {"role": "system", "content": judge_prompt},
                {"role": "user",   "content": f"Query: {query}\n\nResponse: {response[:1000]}"},
            ],
            model=OLLAMA_MODEL,
            temperature=0.0,
            max_tokens=5,
        )
        score = float(raw.strip())
        return max(0.0, min(1.0, score))
    except Exception as e:
        logger.debug("Auto-judge failed (non-fatal): %s", e)
        return 0.5  # neutral fallback


# ── Statistical significance ──────────────────────────────────────────────────

def _welch_ttest_and_cohen(
    scores_a: list[float],
    scores_b: list[float],
) -> tuple[float, float, float]:
    """
    Welch's t-test (unequal variance) + Cohen's d effect size.
    Returns (t_stat, p_value, cohen_d).
    """
    import math

    n_a, n_b = len(scores_a), len(scores_b)
    if n_a < 2 or n_b < 2:
        return 0.0, 1.0, 0.0

    mean_a = sum(scores_a) / n_a
    mean_b = sum(scores_b) / n_b
    var_a  = sum((x - mean_a) ** 2 for x in scores_a) / (n_a - 1)
    var_b  = sum((x - mean_b) ** 2 for x in scores_b) / (n_b - 1)

    se = math.sqrt(var_a / n_a + var_b / n_b)
    if se == 0:
        return 0.0, 1.0, 0.0

    t_stat = (mean_a - mean_b) / se

    # Welch-Satterthwaite degrees of freedom
    df_num   = (var_a / n_a + var_b / n_b) ** 2
    df_denom = (var_a / n_a) ** 2 / (n_a - 1) + (var_b / n_b) ** 2 / (n_b - 1)
    df       = df_num / df_denom if df_denom > 0 else 1.0

    # Two-tailed p-value via scipy if available, else approximate
    try:
        from scipy.stats import t as t_dist
        p_value = 2.0 * t_dist.sf(abs(t_stat), df)
    except ImportError:
        # Simple approximation for large df (normal distribution)
        import math
        p_value = 2.0 * (1.0 - _normal_cdf(abs(t_stat)))

    # Pooled Cohen's d
    pooled_std = math.sqrt((var_a + var_b) / 2) if (var_a + var_b) > 0 else 1.0
    cohen_d    = (mean_a - mean_b) / pooled_std

    return t_stat, float(p_value), float(cohen_d)


def _normal_cdf(z: float) -> float:
    """Approximation of normal CDF for large-sample fallback."""
    import math
    return 0.5 * (1 + math.erf(z / math.sqrt(2)))


# ── Database helpers ──────────────────────────────────────────────────────────

async def _get_pool():
    from backend.prompts.registry import get_pool
    return await get_pool()


async def create_experiment(
    name:          str,
    model_a:       str,
    model_b:       str,
    description:   str   = "",
    system_prompt: str   = "",
    min_turns:     int   = 50,
    traffic_split: float = 0.5,
    auto_promote:  bool  = True,
    created_by:    str   = "",
) -> dict:
    """
    Create a new model A/B experiment.
    Returns the experiment record as a dict.
    """
    exp_id = str(uuid.uuid4())
    pool   = await _get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO model_experiments
                (id, name, description, model_a, model_b,
                 system_prompt, min_turns, traffic_split,
                 auto_promote, created_by)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            RETURNING *
            """,
            exp_id, name, description, model_a, model_b,
            system_prompt, min_turns, traffic_split,
            auto_promote, created_by,
        )
    logger.info("A/B experiment created: %s (%s vs %s)", name, model_a, model_b)
    return dict(row)


async def get_experiment(experiment_id: str) -> Optional[dict]:
    """Fetch experiment row by ID."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM model_experiments WHERE id = $1", experiment_id
        )
    return dict(row) if row else None


async def list_experiments(status: Optional[str] = None) -> list[dict]:
    """List all experiments, optionally filtered by status."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        if status:
            rows = await conn.fetch(
                "SELECT * FROM model_experiments WHERE status = $1 ORDER BY created_at DESC",
                status,
            )
        else:
            rows = await conn.fetch(
                "SELECT * FROM model_experiments ORDER BY created_at DESC"
            )
    return [dict(r) for r in rows]


async def _save_turn(
    experiment_id: str,
    turn:          ExperimentTurn,
    session_id:    str = "",
    user_id:       str = "",
    trace_id:      str = "",
) -> int:
    """Persist one experiment turn; returns the row id."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO model_experiment_turns
                (experiment_id, variant, model, query, response,
                 latency_ms, prompt_tokens, completion_tokens,
                 cost_usd, quality_score, thumbs_up,
                 session_id, user_id, trace_id)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14)
            RETURNING id
            """,
            experiment_id, turn.variant, turn.model,
            turn.query[:2000], turn.response[:4000],
            turn.latency_ms, turn.prompt_tokens, turn.completion_tokens,
            turn.cost_usd, turn.quality_score, turn.thumbs_up,
            session_id, user_id, trace_id,
        )
    return row["id"]


# ── Main run function ─────────────────────────────────────────────────────────

async def run_ab_turn(
    experiment_id: str,
    query:         str,
    session_id:    str = "",
    user_id:       str = "",
    auto_score:    bool = True,
) -> ABRunResult:
    """
    Run a single query through both model variants simultaneously.
    Returns paired results. The "served" variant is chosen by traffic_split.
    Also checks auto-promotion threshold.
    """
    import random

    exp = await get_experiment(experiment_id)
    if not exp:
        raise ValueError(f"Experiment {experiment_id} not found")
    if exp["status"] != "running":
        raise ValueError(f"Experiment {experiment_id} is {exp['status']}, not running")

    model_a       = exp["model_a"]
    model_b       = exp["model_b"]
    system_prompt = exp["system_prompt"] or ""
    traffic_split = float(exp["traffic_split"])

    # Determine which variant is served to the user
    serve_a      = random.random() < traffic_split
    served_variant = "A" if serve_a else "B"

    # Run both models in parallel (shadow traffic pattern)
    (text_a, lat_a, pt_a, ct_a), (text_b, lat_b, pt_b, ct_b) = await asyncio.gather(
        _call_openai(model_a, system_prompt, query),
        _call_openai(model_b, system_prompt, query),
    )

    cost_a = compute_cost(model_a, pt_a, ct_a)
    cost_b = compute_cost(model_b, pt_b, ct_b)

    turn_a = ExperimentTurn(
        variant="A", model=model_a, query=query, response=text_a,
        latency_ms=lat_a, prompt_tokens=pt_a, completion_tokens=ct_a,
        cost_usd=cost_a,
    )
    turn_b = ExperimentTurn(
        variant="B", model=model_b, query=query, response=text_b,
        latency_ms=lat_b, prompt_tokens=pt_b, completion_tokens=ct_b,
        cost_usd=cost_b,
    )

    # Auto-score via LLM judge (fire-and-forget on scores)
    if auto_score:
        score_a, score_b = await asyncio.gather(
            _score_response(query, text_a),
            _score_response(query, text_b),
        )
        turn_a.quality_score = score_a
        turn_b.quality_score = score_b

    # Persist both turns
    turn_a_id, turn_b_id = await asyncio.gather(
        _save_turn(experiment_id, turn_a, session_id, user_id),
        _save_turn(experiment_id, turn_b, session_id, user_id),
    )

    # MLflow logging
    _log_to_mlflow(experiment_id, exp["name"], turn_a, turn_b)

    result = ABRunResult(
        experiment_id=experiment_id,
        turn_a_id=turn_a_id,
        turn_b_id=turn_b_id,
        turn_a=turn_a,
        turn_b=turn_b,
        served_variant=served_variant,
    )

    # Check auto-promote in background
    asyncio.create_task(_check_and_promote(experiment_id))

    return result


def _log_to_mlflow(
    experiment_id: str,
    experiment_name: str,
    turn_a: ExperimentTurn,
    turn_b: ExperimentTurn,
) -> None:
    """Non-blocking MLflow metric logging."""
    try:
        import mlflow
        with mlflow.start_run(
            run_name=f"ab_{experiment_name}",
            tags={"experiment_id": experiment_id},
            nested=True,
        ):
            mlflow.log_metrics({
                f"latency_ms_A_{turn_a.model}":   turn_a.latency_ms,
                f"latency_ms_B_{turn_b.model}":   turn_b.latency_ms,
                f"cost_usd_A_{turn_a.model}":     turn_a.cost_usd,
                f"cost_usd_B_{turn_b.model}":     turn_b.cost_usd,
                f"tokens_A_{turn_a.model}":       turn_a.prompt_tokens + turn_a.completion_tokens,
                f"tokens_B_{turn_b.model}":       turn_b.prompt_tokens + turn_b.completion_tokens,
            })
            if turn_a.quality_score is not None:
                mlflow.log_metrics({
                    f"quality_A_{turn_a.model}": turn_a.quality_score,
                    f"quality_B_{turn_b.model}": turn_b.quality_score or 0,
                })
    except Exception as e:
        logger.debug("MLflow logging (non-fatal): %s", e)


# ── Statistical analysis ──────────────────────────────────────────────────────

async def compute_significance(experiment_id: str) -> SignificanceResult:
    """
    Compute Welch's t-test + Cohen's d across all rated turns in an experiment.
    Only turns with non-NULL quality_score are included.
    """
    import math

    pool = await _get_pool()
    async with pool.acquire() as conn:
        exp = await conn.fetchrow(
            "SELECT * FROM model_experiments WHERE id = $1", experiment_id
        )
        rows = await conn.fetch(
            """
            SELECT variant, quality_score
            FROM   model_experiment_turns
            WHERE  experiment_id = $1 AND quality_score IS NOT NULL
            """,
            experiment_id,
        )

    scores_a = [float(r["quality_score"]) for r in rows if r["variant"] == "A"]
    scores_b = [float(r["quality_score"]) for r in rows if r["variant"] == "B"]

    n_a    = len(scores_a)
    n_b    = len(scores_b)
    mean_a = sum(scores_a) / n_a if n_a else 0.0
    mean_b = sum(scores_b) / n_b if n_b else 0.0
    std_a  = math.sqrt(sum((x - mean_a) ** 2 for x in scores_a) / max(n_a - 1, 1)) if n_a > 1 else 0.0
    std_b  = math.sqrt(sum((x - mean_b) ** 2 for x in scores_b) / max(n_b - 1, 1)) if n_b > 1 else 0.0

    t_stat, p_value, cohen_d = _welch_ttest_and_cohen(scores_a, scores_b)

    is_significant = p_value < 0.05 and (n_a >= 10 and n_b >= 10)

    # Determine winner
    winner         = None
    winner_model   = None
    if is_significant:
        if mean_a > mean_b:
            winner       = "A"
            winner_model = exp["model_a"] if exp else None
        elif mean_b > mean_a:
            winner       = "B"
            winner_model = exp["model_b"] if exp else None

    # Human-readable interpretation
    if not is_significant:
        effect_desc = (
            f"No statistically significant difference (p={p_value:.3f}, need p<0.05). "
            f"Collect more data (have {n_a + n_b} rated turns)."
        )
    else:
        magnitude = (
            "large" if abs(cohen_d) >= 0.8
            else "medium" if abs(cohen_d) >= 0.5
            else "small"
        )
        effect_desc = (
            f"Significant difference (p={p_value:.4f}). "
            f"{winner} wins with {magnitude} effect size (d={cohen_d:.3f}). "
            f"Mean quality: A={mean_a:.3f}, B={mean_b:.3f}."
        )

    return SignificanceResult(
        experiment_id=experiment_id,
        n_a=n_a,
        n_b=n_b,
        mean_a=mean_a,
        mean_b=mean_b,
        std_a=std_a,
        std_b=std_b,
        t_statistic=t_stat,
        p_value=p_value,
        cohen_d=cohen_d,
        is_significant=is_significant,
        winner=winner,
        winner_model=winner_model,
        interpretation=effect_desc,
    )


async def _check_and_promote(experiment_id: str) -> None:
    """Background task: promote winner if min_turns reached and significant."""
    try:
        pool = await _get_pool()
        async with pool.acquire() as conn:
            exp = await conn.fetchrow(
                "SELECT * FROM model_experiments WHERE id = $1 AND status = 'running'",
                experiment_id,
            )
        if not exp or not exp["auto_promote"]:
            return

        # Count total rated turns
        async with pool.acquire() as conn:
            count_row = await conn.fetchrow(
                """
                SELECT COUNT(*) AS cnt
                FROM   model_experiment_turns
                WHERE  experiment_id = $1 AND quality_score IS NOT NULL
                """,
                experiment_id,
            )
        total_rated = count_row["cnt"] if count_row else 0

        if total_rated < exp["min_turns"]:
            return  # not enough data yet

        sig = await compute_significance(experiment_id)
        if not sig.is_significant or not sig.winner_model:
            return  # no clear winner yet

        await promote_winner(experiment_id, sig.winner_model, sig.p_value, sig.cohen_d)

    except Exception as e:
        logger.warning("Auto-promote check failed (non-fatal): %s", e)


async def promote_winner(
    experiment_id: str,
    winner_model:  str,
    p_value:       float = 0.0,
    cohen_d:       float = 0.0,
) -> dict:
    """
    Mark experiment as completed with a winner.
    Updates the LLM router preference in Redis.
    """
    pool = await _get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            UPDATE model_experiments
            SET    status = 'completed',
                   winner_model = $1,
                   significance_p = $2,
                   effect_size = $3,
                   promoted_at = NOW(),
                   completed_at = NOW()
            WHERE  id = $4
            RETURNING *
            """,
            winner_model, p_value, cohen_d, experiment_id,
        )

    logger.info(
        "A/B experiment %s completed — winner: %s (p=%.4f, d=%.3f)",
        experiment_id, winner_model, p_value, cohen_d,
    )

    # Update LLM router preference in Redis
    try:
        from backend.session.redis_client import get_redis
        redis = await get_redis()
        await redis.set(
            f"ab_winner:{row['name']}",
            winner_model,
            ex=86400 * 30,  # 30-day preference
        )
        logger.info("LLM router preference set: %s → %s", row["name"], winner_model)
    except Exception as e:
        logger.warning("Redis router preference update (non-fatal): %s", e)

    return dict(row)


# ── Feedback recording ────────────────────────────────────────────────────────

async def record_turn_feedback(
    turn_id:       int,
    quality_score: Optional[float] = None,
    thumbs_up:     Optional[bool]  = None,
) -> dict:
    """
    Record human feedback on a specific turn.
    Returns updated turn record.
    """
    pool = await _get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            UPDATE model_experiment_turns
            SET    quality_score = COALESCE($1, quality_score),
                   thumbs_up     = COALESCE($2, thumbs_up)
            WHERE  id = $3
            RETURNING *
            """,
            quality_score, thumbs_up, turn_id,
        )
    if row:
        asyncio.create_task(_check_and_promote(row["experiment_id"]))
    return dict(row) if row else {}


# ── Aggregated statistics ─────────────────────────────────────────────────────

async def get_experiment_stats(experiment_id: str) -> dict:
    """
    Return comprehensive stats for an experiment (for admin dashboard).
    """
    pool = await _get_pool()
    async with pool.acquire() as conn:
        exp = await conn.fetchrow(
            "SELECT * FROM model_experiments WHERE id = $1", experiment_id
        )
        if not exp:
            return {}

        stats = await conn.fetch(
            """
            SELECT
                variant,
                model,
                COUNT(*)                                AS total_turns,
                COUNT(quality_score)                    AS rated_turns,
                ROUND(AVG(quality_score)::numeric, 4)   AS avg_quality,
                ROUND(AVG(latency_ms)::numeric, 1)      AS avg_latency_ms,
                ROUND(AVG(cost_usd)::numeric, 6)        AS avg_cost_usd,
                SUM(cost_usd)                           AS total_cost_usd,
                SUM(prompt_tokens + completion_tokens)  AS total_tokens,
                SUM(CASE WHEN thumbs_up THEN 1 ELSE 0 END) AS thumbs_up_count,
                SUM(CASE WHEN thumbs_up = FALSE THEN 1 ELSE 0 END) AS thumbs_down_count
            FROM model_experiment_turns
            WHERE experiment_id = $1
            GROUP BY variant, model
            ORDER BY variant
            """,
            experiment_id,
        )

    stats_by_variant = {}
    for row in stats:
        stats_by_variant[row["variant"]] = {
            "variant":        row["variant"],
            "model":          row["model"],
            "total_turns":    int(row["total_turns"]),
            "rated_turns":    int(row["rated_turns"]),
            "avg_quality":    float(row["avg_quality"] or 0),
            "avg_latency_ms": float(row["avg_latency_ms"] or 0),
            "avg_cost_usd":   float(row["avg_cost_usd"] or 0),
            "total_cost_usd": float(row["total_cost_usd"] or 0),
            "total_tokens":   int(row["total_tokens"] or 0),
            "thumbs_up":      int(row["thumbs_up_count"] or 0),
            "thumbs_down":    int(row["thumbs_down_count"] or 0),
        }

    # Compute significance
    try:
        sig = await compute_significance(experiment_id)
        significance = {
            "n_a":            sig.n_a,
            "n_b":            sig.n_b,
            "t_statistic":    round(sig.t_statistic, 4),
            "p_value":        round(sig.p_value, 6),
            "cohen_d":        round(sig.cohen_d, 4),
            "is_significant": sig.is_significant,
            "winner":         sig.winner,
            "winner_model":   sig.winner_model,
            "interpretation": sig.interpretation,
        }
    except Exception as e:
        logger.warning("Significance computation failed (non-fatal): %s", e)
        significance = {"error": "Significance not yet computable — collect more rated turns."}

    return {
        "experiment_id":   experiment_id,
        "name":            exp["name"],
        "description":     exp["description"],
        "model_a":         exp["model_a"],
        "model_b":         exp["model_b"],
        "status":          exp["status"],
        "winner_model":    exp["winner_model"],
        "traffic_split":   float(exp["traffic_split"]),
        "min_turns":       exp["min_turns"],
        "auto_promote":    exp["auto_promote"],
        "created_at":      exp["created_at"].isoformat() if exp["created_at"] else None,
        "completed_at":    exp["completed_at"].isoformat() if exp.get("completed_at") else None,
        "variant_a":       stats_by_variant.get("A", {}),
        "variant_b":       stats_by_variant.get("B", {}),
        "significance":    significance,
        "completion_pct":  min(100, round(
            (
                stats_by_variant.get("A", {}).get("rated_turns", 0) +
                stats_by_variant.get("B", {}).get("rated_turns", 0)
            ) / max(exp["min_turns"], 1) * 100, 1
        )),
    }
