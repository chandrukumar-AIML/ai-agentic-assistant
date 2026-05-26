# backend/api/ab_routes.py
"""
Agent A/B Testing Framework REST API (Feature 12).

Endpoints:
  POST /ab/experiments                    — Create new model experiment
  GET  /ab/experiments                    — List all experiments
  GET  /ab/experiments/{id}               — Get experiment stats + significance
  POST /ab/experiments/{id}/run           — Run a test query through both models
  POST /ab/experiments/{id}/feedback      — Record feedback on a turn
  POST /ab/experiments/{id}/promote       — Manually promote a winner
  GET  /ab/experiments/{id}/significance  — Significance analysis only
  POST /ab/experiments/{id}/pause         — Pause experiment
  POST /ab/experiments/{id}/resume        — Resume paused experiment

Auth: all endpoints require a valid JWT token.
Admin-only: create, promote, pause/resume.
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, field_validator

from backend.api.auth import verify_token

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ab", tags=["ab-testing"])

# Supported model identifiers
_SUPPORTED_MODELS = {
    "gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo",
    "claude-3-haiku", "claude-3-sonnet",
    "llama3", "llama3:8b", "llama3:70b", "mistral",
}


# ── Request/Response models ───────────────────────────────────────────────────

class CreateExperimentRequest(BaseModel):
    name:          str   = Field(..., min_length=3, max_length=100)
    model_a:       str   = Field(..., description="Model identifier for variant A")
    model_b:       str   = Field(..., description="Model identifier for variant B")
    description:   str   = Field(default="", max_length=500)
    system_prompt: str   = Field(default="", max_length=4000)
    min_turns:     int   = Field(default=50, ge=10, le=5000)
    traffic_split: float = Field(default=0.5, ge=0.1, le=0.9)
    auto_promote:  bool  = Field(default=True)

    @field_validator("model_a", "model_b")
    @classmethod
    def validate_model(cls, v: str) -> str:
        if v not in _SUPPORTED_MODELS:
            raise ValueError(
                f"Model '{v}' not supported. Choose from: {sorted(_SUPPORTED_MODELS)}"
            )
        return v

    @field_validator("model_b")
    @classmethod
    def models_must_differ(cls, v: str, info) -> str:
        if "model_a" in (info.data or {}) and v == info.data["model_a"]:
            raise ValueError("model_a and model_b must be different")
        return v


class RunQueryRequest(BaseModel):
    query:      str  = Field(..., min_length=1, max_length=4000)
    session_id: str  = Field(default="")
    auto_score: bool = Field(default=True, description="Auto-score with LLM judge")


class FeedbackRequest(BaseModel):
    turn_id:       int            = Field(..., ge=1)
    quality_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    thumbs_up:     Optional[bool]  = Field(default=None)


class PromoteRequest(BaseModel):
    winner_model: str = Field(..., description="Model identifier to promote as winner")


# ── Helpers ───────────────────────────────────────────────────────────────────

def _require_admin(token: dict) -> None:
    role = token.get("role", "user")
    if role not in ("admin", "superadmin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required for this operation.",
        )


async def _get_exp_or_404(experiment_id: str) -> dict:
    from backend.ab_testing.ab_engine import get_experiment
    exp = await get_experiment(experiment_id)
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found.")
    return exp


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post(
    "/experiments",
    summary="Create model A/B experiment (Feature 12)",
    status_code=status.HTTP_201_CREATED,
)
async def create_experiment(
    req:   CreateExperimentRequest,
    token: dict = Depends(verify_token),
):
    """
    Create a new model-level A/B experiment.
    Requires admin role.
    """
    _require_admin(token)
    from backend.ab_testing.ab_engine import create_experiment as _create
    exp = await _create(
        name=req.name,
        model_a=req.model_a,
        model_b=req.model_b,
        description=req.description,
        system_prompt=req.system_prompt,
        min_turns=req.min_turns,
        traffic_split=req.traffic_split,
        auto_promote=req.auto_promote,
        created_by=token.get("sub", ""),
    )
    return {
        "experiment_id": exp["id"],
        "name":          exp["name"],
        "model_a":       exp["model_a"],
        "model_b":       exp["model_b"],
        "status":        exp["status"],
        "created_at":    exp["created_at"].isoformat() if exp.get("created_at") else None,
    }


@router.get("/experiments", summary="List all A/B experiments")
async def list_experiments(
    status_filter: Optional[str] = Query(default=None, alias="status"),
    token:         dict = Depends(verify_token),
):
    try:
        from backend.ab_testing.ab_engine import list_experiments as _list
        experiments = await _list(status=status_filter)
        return {"experiments": experiments, "count": len(experiments)}
    except Exception as e:
        logger.warning("AB experiments DB unavailable: %s", e)
        return {"experiments": [], "count": 0, "warning": "Database unavailable — no experiments stored yet."}


@router.get("/experiments/{experiment_id}", summary="Get experiment stats + significance")
async def get_experiment_stats(
    experiment_id: str,
    token:         dict = Depends(verify_token),
):
    await _get_exp_or_404(experiment_id)
    from backend.ab_testing.ab_engine import get_experiment_stats
    stats = await get_experiment_stats(experiment_id)
    return stats


@router.post("/experiments/{experiment_id}/run", summary="Run test query through both models")
async def run_ab_query(
    experiment_id: str,
    req:           RunQueryRequest,
    token:         dict = Depends(verify_token),
):
    """
    Run a query through both model variants simultaneously.
    Both responses are saved; the served_variant indicates which was returned to the user.
    Auto-scores with LLM judge unless auto_score=False.
    """
    await _get_exp_or_404(experiment_id)
    from backend.ab_testing.ab_engine import run_ab_turn

    result = await run_ab_turn(
        experiment_id=experiment_id,
        query=req.query,
        session_id=req.session_id,
        user_id=token.get("sub", ""),
        auto_score=req.auto_score,
    )

    # Return only the served variant's response to the caller
    served = result.turn_a if result.served_variant == "A" else result.turn_b

    return {
        "experiment_id":    experiment_id,
        "served_variant":   result.served_variant,
        "response":         served.response,
        "model":            served.model,
        "latency_ms":       served.latency_ms,
        "cost_usd":         round(served.cost_usd, 6),
        "quality_score":    served.quality_score,
        "turn_a_id":        result.turn_a_id,
        "turn_b_id":        result.turn_b_id,
        # Shadow turn metrics for monitoring
        "shadow": {
            "variant":     "B" if result.served_variant == "A" else "A",
            "model":       result.turn_b.model if result.served_variant == "A" else result.turn_a.model,
            "latency_ms":  result.turn_b.latency_ms if result.served_variant == "A" else result.turn_a.latency_ms,
            "cost_usd":    round(
                result.turn_b.cost_usd if result.served_variant == "A" else result.turn_a.cost_usd, 6
            ),
            "quality_score": (
                result.turn_b.quality_score if result.served_variant == "A" else result.turn_a.quality_score
            ),
        },
    }


@router.post("/experiments/{experiment_id}/feedback", summary="Record feedback on a turn")
async def record_feedback(
    experiment_id: str,
    req:           FeedbackRequest,
    token:         dict = Depends(verify_token),
):
    """
    Record human quality score or thumbs up/down on a specific turn.
    Triggers auto-promotion check in background if thresholds met.
    """
    await _get_exp_or_404(experiment_id)
    from backend.ab_testing.ab_engine import record_turn_feedback

    if req.quality_score is None and req.thumbs_up is None:
        raise HTTPException(
            status_code=400,
            detail="Provide at least one of: quality_score, thumbs_up",
        )

    # Convert thumbs_up to numeric score for t-test
    quality_score = req.quality_score
    if quality_score is None and req.thumbs_up is not None:
        quality_score = 1.0 if req.thumbs_up else 0.0

    updated = await record_turn_feedback(
        turn_id=req.turn_id,
        quality_score=quality_score,
        thumbs_up=req.thumbs_up,
    )
    return {"turn_id": req.turn_id, "updated": bool(updated), "quality_score": quality_score}


@router.get(
    "/experiments/{experiment_id}/significance",
    summary="Statistical significance analysis",
)
async def get_significance(
    experiment_id: str,
    token:         dict = Depends(verify_token),
):
    """
    Run Welch's t-test + Cohen's d on all rated turns.
    Returns interpretation and winner recommendation.
    """
    await _get_exp_or_404(experiment_id)
    from backend.ab_testing.ab_engine import compute_significance

    sig = await compute_significance(experiment_id)
    return {
        "experiment_id":  experiment_id,
        "n_a":            sig.n_a,
        "n_b":            sig.n_b,
        "mean_quality_a": round(sig.mean_a, 4),
        "mean_quality_b": round(sig.mean_b, 4),
        "std_a":          round(sig.std_a, 4),
        "std_b":          round(sig.std_b, 4),
        "t_statistic":    round(sig.t_statistic, 4),
        "p_value":        round(sig.p_value, 6),
        "cohen_d":        round(sig.cohen_d, 4),
        "is_significant": sig.is_significant,
        "winner":         sig.winner,
        "winner_model":   sig.winner_model,
        "interpretation": sig.interpretation,
        "alpha":          0.05,
    }


@router.post("/experiments/{experiment_id}/promote", summary="Manually promote a winner")
async def promote_winner(
    experiment_id: str,
    req:           PromoteRequest,
    token:         dict = Depends(verify_token),
):
    """
    Manually promote a model as winner, bypassing significance threshold.
    Admin-only. Updates LLM router preference in Redis.
    """
    _require_admin(token)
    exp = await _get_exp_or_404(experiment_id)

    if req.winner_model not in (exp["model_a"], exp["model_b"]):
        raise HTTPException(
            status_code=400,
            detail=f"winner_model must be one of: {exp['model_a']}, {exp['model_b']}",
        )

    from backend.ab_testing.ab_engine import promote_winner as _promote
    result = await _promote(experiment_id, req.winner_model)
    return {
        "experiment_id": experiment_id,
        "winner_model":  result["winner_model"],
        "status":        result["status"],
        "promoted_at":   result["promoted_at"].isoformat() if result.get("promoted_at") else None,
    }


@router.post("/experiments/{experiment_id}/pause", summary="Pause a running experiment")
async def pause_experiment(
    experiment_id: str,
    token:         dict = Depends(verify_token),
):
    _require_admin(token)
    exp = await _get_exp_or_404(experiment_id)

    if exp["status"] != "running":
        raise HTTPException(status_code=400, detail=f"Experiment is {exp['status']}, cannot pause.")

    from backend.prompts.registry import get_pool
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE model_experiments SET status = 'paused' WHERE id = $1", experiment_id
        )
    return {"experiment_id": experiment_id, "status": "paused"}


@router.post("/experiments/{experiment_id}/resume", summary="Resume a paused experiment")
async def resume_experiment(
    experiment_id: str,
    token:         dict = Depends(verify_token),
):
    _require_admin(token)
    exp = await _get_exp_or_404(experiment_id)

    if exp["status"] != "paused":
        raise HTTPException(status_code=400, detail=f"Experiment is {exp['status']}, cannot resume.")

    from backend.prompts.registry import get_pool
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE model_experiments SET status = 'running' WHERE id = $1", experiment_id
        )
    return {"experiment_id": experiment_id, "status": "running"}
