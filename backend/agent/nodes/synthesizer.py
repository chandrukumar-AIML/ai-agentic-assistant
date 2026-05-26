# backend/agent/nodes/synthesizer.py
import time
import logging
from langchain_core.messages import AIMessage
from backend.agent.state import AgentState
from backend.agent.prompts import SYNTHESIZER_PROMPT
from backend.llm.router import llm_router
from backend.utils.text import deduplicate_ordered
from backend.observability.mlflow_logger import log_agent_run

logger = logging.getLogger(__name__)


async def synthesizer(state: AgentState) -> dict:
    start   = time.monotonic()
    results = state.get("tool_results", [])

    tool_results_text = "\n\n".join(
        f"--- {r['tool_name']} (confidence: {r['confidence']:.2f}) ---\n{r['content']}"
        for r in results
    )
    sources      = deduplicate_ordered(r["source"] for r in results if r.get("source"))
    sources_text = "\n".join(f"[{i+1}] {s}" for i, s in enumerate(sources))

    # ── Inject memory context into system prompt ────────────────────────────────
    memory_context = state.get("memory_context", "")
    system_content = (
        f"You are a precise AI assistant with memory of this user."
        f"{memory_context}"
        f"\nUse the memory context above to personalise your response when relevant."
    )

    messages = [
        {"role": "system", "content": system_content},
        {
            "role": "user",
            "content": SYNTHESIZER_PROMPT.format(
                query=state["user_query"],
                tool_results=tool_results_text,
                sources=sources_text,
            ),
        },
    ]

    response, model_used = await llm_router.complete(
        messages=messages,
        temperature=0.3,
        max_tokens=1000,
    )

    final_answer = (
        response if isinstance(response, str)
        else "".join([t async for t in response])
    )

    elapsed = (time.monotonic() - start) * 1000

    try:
        log_agent_run(
            session_id=state.get("session_id", "unknown"),
            query=state["user_query"],
            intent=state.get("intent", ""),
            selected_tools=state.get("selected_tools", []),
            model_used=model_used,
            latency_ms={**state.get("latency_ms", {}), "synthesizer": round(elapsed, 2)},
            final_answer=final_answer,
            sources=sources,
            retry_count=state.get("retry_count", 0),
            error=state.get("error"),
        )
    except Exception:
        pass

    return {
        "final_answer": final_answer,
        "sources":      sources,
        "messages":     [AIMessage(content=final_answer)],
        "latency_ms":   {"synthesizer": round(elapsed, 2)},
        "model_used":   model_used,
    }
