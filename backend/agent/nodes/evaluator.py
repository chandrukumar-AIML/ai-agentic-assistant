import time
import json
import logging
from backend.agent.state import AgentState  # FIXED: wrong import path
from backend.agent.prompts import EVALUATOR_PROMPT  # FIXED: wrong import path
from backend.llm.router import llm_router  # FIXED: wrong import path
from backend.utils.text import strip_code_fence  # FIXED: wrong import path

logger = logging.getLogger(__name__)


async def evaluator(state: AgentState) -> dict:
    start = time.monotonic()
    results = state.get("tool_results", [])

    # Fast-path: no results at all
    if not results:
        elapsed = (time.monotonic() - start) * 1000
        return {
            "retry_count": state["retry_count"] + 1,
            "error":       "No tool results returned. Try different tools.",
            "tool_results": [],
            "latency_ms":  {"evaluator": round(elapsed, 2)},
        }

    # Fast-path: high confidence — skip LLM call
    max_conf = max((r["confidence"] for r in results), default=0.0)
    if max_conf >= 0.75:
        elapsed = (time.monotonic() - start) * 1000
        return {
            "error":      None,
            "latency_ms": {"evaluator": round(elapsed, 2)},
        }

    # Fast-path: retries exhausted
    if state["retry_count"] >= state["max_retries"]:
        elapsed = (time.monotonic() - start) * 1000
        return {
            "retry_count": state["retry_count"] + 1,
            "error":       "Max retries reached.",
            "latency_ms":  {"evaluator": round(elapsed, 2)},
        }

    # LLM evaluation for ambiguous confidence (0–0.75)
    results_summary = "\n".join(
        f"[{r['tool_name']}] confidence={r['confidence']:.2f}: {r['content'][:200]}..."
        for r in results
    )

    messages = [
        {
            "role": "user",
            "content": EVALUATOR_PROMPT.format(
                query=state["user_query"],
                results_summary=results_summary,
                retry_count=state["retry_count"],
                max_retries=state["max_retries"],
            ),
        }
    ]

    response, _ = await llm_router.complete(
        messages=messages,
        temperature=0,
        max_tokens=100,
    )

    try:
        clean = strip_code_fence(response if isinstance(response, str) else "")
        parsed = json.loads(clean)
        sufficient = parsed.get("sufficient", False)
        reason = parsed.get("reason", "")
    except (json.JSONDecodeError, KeyError, AttributeError) as e:  # FIXED: was silently swallowing parse errors without logging
        logger.warning(f"Evaluator JSON parse failed, defaulting to sufficient=True: {e}")
        sufficient = True
        reason = "parse fallback"

    elapsed = (time.monotonic() - start) * 1000

    if sufficient:
        return {"error": None, "latency_ms": {"evaluator": round(elapsed, 2)}}
    else:
        return {
            "retry_count":  state["retry_count"] + 1,
            "error":        reason,
            "tool_results": [],   # replace reducer clears the list
            "latency_ms":   {"evaluator": round(elapsed, 2)},
        }