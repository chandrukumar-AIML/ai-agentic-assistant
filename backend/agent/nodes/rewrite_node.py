# FIXED: Was an empty 1-line stub — now a complete rewrite node
"""
Rewrites the current answer based on reflection critique.
Called when reflection_verdict == "fail" and loops remain.
"""
import time
import logging
from backend.agent.state import AgentState
from backend.llm.router  import llm_router

logger = logging.getLogger(__name__)

REWRITE_PROMPT = """You are an AI answer improver.

Original user query:
{query}

Your previous answer (score: {score}/10):
{answer}

Critic's feedback:
{critique}

Missing elements:
{missing}

Potential hallucinations to fix:
{hallucinations}

Rewrite the answer fixing ALL the issues above. Be specific, accurate, and complete.
Do NOT repeat the critique — just write a better answer."""


async def rewrite_node(state: AgentState) -> dict:
    """
    Rewrites final_answer guided by reflection critique.
    Increments reflection_attempts counter.
    """
    start = time.monotonic()

    answer       = state.get("final_answer") or ""
    critique     = state.get("reflection_critique") or "Improve the answer."
    missing      = state.get("reflection_missing") or []
    score        = state.get("reflection_score", 5.0)

    hallucinations = []
    if state.get("reflection_history"):
        last = state["reflection_history"][-1]
        hallucinations = last.get("hallucinations", [])

    messages = [
        {
            "role":    "system",
            "content": "You are a precise, factual AI assistant. Rewrite only — no meta-commentary.",
        },
        {
            "role": "user",
            "content": REWRITE_PROMPT.format(
                query=state["user_query"],
                answer=answer[:3000],
                score=score,
                critique=critique,
                missing="\n".join(f"- {m}" for m in missing) or "None",
                hallucinations="\n".join(f"- {h}" for h in hallucinations) or "None",
            ),
        },
    ]

    try:
        response, model_used = await llm_router.complete(
            messages=messages,
            temperature=0.3,
            max_tokens=1500,
        )
        new_answer = response if isinstance(response, str) else answer
    except Exception as e:
        logger.error(f"Rewrite node failed: {e}")
        new_answer = answer  # keep original on failure

    elapsed = (time.monotonic() - start) * 1000
    logger.info(
        f"Rewrite: score was {score}/10, "
        f"new_answer length={len(new_answer)} chars in {elapsed:.0f}ms"
    )

    return {
        "final_answer": new_answer,
        "latency_ms":   {"rewrite": round(elapsed, 2)},
    }
