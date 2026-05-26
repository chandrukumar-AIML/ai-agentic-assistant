# backend/agent/nodes/reflection_node.py
"""
Reflexion pattern implementation.
Critiques the current answer and produces a structured score + feedback.
"""
import time
import json
import logging
from backend.agent.state   import AgentState
from backend.llm.router    import llm_router
from backend.utils.text    import strip_code_fence

logger = logging.getLogger(__name__)

MAX_REFLECTION_LOOPS = 3
PASS_THRESHOLD       = 7.0    # score ≥ 7 → accept answer

REFLECTION_PROMPT = """You are a rigorous quality critic for an AI assistant.

User query:
{query}

Tool results used:
{tool_results}

Agent's current answer:
{answer}

Critique this answer. Be specific and harsh — not vague.
Check for:
1. Does it directly answer what was asked? (no topic drift)
2. Are all claims supported by the tool results? (no hallucination)
3. Are there sub-questions left unanswered?
4. Is the code (if any) correct and runnable?
5. Are sources cited where claims are made?
6. Is anything factually wrong or misleading?

Respond ONLY with this JSON:
{{
  "score": <integer 1-10>,
  "verdict": "pass" or "fail",
  "critique": "<specific problems found, or 'None' if score >= 7>",
  "missing": ["<specific thing 1 not addressed>", "<specific thing 2>"],
  "hallucinations": ["<claim not supported by tool results>"]
}}

Rules:
- score >= 7 → verdict must be "pass"
- score < 7  → verdict must be "fail"
- critique must be specific, not generic
- missing list can be empty []
- hallucinations list can be empty []"""


async def reflection_node(state: AgentState) -> dict:
    """
    Reflects on the current final_answer.
    Returns updated reflection fields.
    Does NOT rewrite — that's the rewrite_node's job.
    """
    start    = time.monotonic()
    answer   = state.get("final_answer") or ""
    attempts = state.get("reflection_attempts", 0)

    # Hard stop — don't reflect more than MAX loops
    if attempts >= MAX_REFLECTION_LOOPS:
        logger.info(f"Reflection: max loops ({MAX_REFLECTION_LOOPS}) reached — accepting answer")
        return {
            "reflection_score":   state.get("reflection_score", 7.0),
            "reflection_verdict": "pass",
            "latency_ms":         {"reflection": 0.0},
        }

    # Format tool results summary for reflection context
    tool_results_text = "\n".join(
        f"[{r['tool_name']}]: {r['content'][:300]}"
        for r in state.get("tool_results", [])
    ) or "No tool results."

    messages = [
        {
            "role":    "system",
            "content": "You are a strict quality critic. Respond only with valid JSON.",
        },
        {
            "role": "user",
            "content": REFLECTION_PROMPT.format(
                query=state["user_query"],
                tool_results=tool_results_text,
                answer=answer[:2000],   # cap to avoid token explosion
            ),
        },
    ]

    try:
        response, _ = await llm_router.complete(
            messages=messages,
            temperature=0,
            max_tokens=400,
        )
        raw    = strip_code_fence(response if isinstance(response, str) else "")
        parsed = json.loads(raw)

        score       = float(parsed.get("score", 5))
        verdict     = parsed.get("verdict", "fail")
        critique    = parsed.get("critique", "")
        missing     = parsed.get("missing", [])
        hallucinations = parsed.get("hallucinations", [])

        # Override verdict based on threshold (don't trust LLM's own verdict 100%)
        verdict = "pass" if score >= PASS_THRESHOLD else "fail"

    except (json.JSONDecodeError, ValueError, KeyError) as e:
        logger.warning(f"Reflection parse failed: {e} — defaulting to pass")
        score          = 7.0
        verdict        = "pass"
        critique       = ""
        missing        = []
        hallucinations = []

    elapsed = (time.monotonic() - start) * 1000

    # Build history entry for React UI display
    history_entry = {
        "attempt":        attempts + 1,
        "answer_preview": answer[:200] + "..." if len(answer) > 200 else answer,
        "score":          score,
        "verdict":        verdict,
        "critique":       critique,
        "missing":        missing,
        "hallucinations": hallucinations,
        "latency_ms":     round(elapsed, 2),
    }

    # Merge into existing history
    existing_history = state.get("reflection_history", [])

    logger.info(
        f"Reflection attempt {attempts + 1}: score={score}/10, "
        f"verdict={verdict}, critique={critique[:80]}"
    )

    return {
        "reflection_score":    score,
        "reflection_verdict":  verdict,
        "reflection_critique": critique,
        "reflection_missing":  missing,
        "reflection_attempts": attempts + 1,
        "reflection_history":  existing_history + [history_entry],
        "latency_ms":          {"reflection": round(elapsed, 2)},
    }