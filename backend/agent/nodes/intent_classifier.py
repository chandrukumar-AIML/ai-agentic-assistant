import time
from backend.agent.state import AgentState  # FIXED: wrong import path
from backend.agent.prompts import INTENT_CLASSIFIER_PROMPT  # FIXED: wrong import path
from backend.llm.router import llm_router  # FIXED: wrong import path

VALID_INTENTS = {"rag", "web_search", "code", "vision", "graph", "hybrid"}


async def intent_classifier(state: AgentState) -> dict:
    start = time.monotonic()

    messages = [
        {
            "role": "user",
            "content": INTENT_CLASSIFIER_PROMPT.format(
                query=state["user_query"],
                has_image=str(state.get("image_data") is not None),
            ),
        }
    ]

    response, model_used = await llm_router.complete(
        messages=messages,
        temperature=0,
        max_tokens=10,
    )

    raw = response.strip().lower() if isinstance(response, str) else "rag"
    intent = raw if raw in VALID_INTENTS else "rag"

    if state.get("image_data") and intent not in {"vision", "hybrid"}:
        intent = "vision"

    elapsed = (time.monotonic() - start) * 1000

    return {
        "intent":     intent,
        "latency_ms": {"intent_classifier": round(elapsed, 2)},
        "model_used": model_used,
    }