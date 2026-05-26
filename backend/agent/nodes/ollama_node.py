"""
Ollama fallback node — invoked by the evaluator when the OpenAI circuit is OPEN
or when max retries are exhausted. Forces Ollama regardless of circuit state.
"""
import time
import logging
from langchain_core.messages import AIMessage

from backend.agent.state import AgentState  # FIXED: wrong import path
from backend.agent.prompts import SYNTHESIZER_PROMPT  # FIXED: wrong import path
from backend.llm.router import llm_router  # FIXED: wrong import path
from backend.utils.text import deduplicate_ordered  # FIXED: wrong import path

logger = logging.getLogger(__name__)


async def ollama_node(state: AgentState) -> dict:
    start = time.monotonic()

    results = state.get("tool_results", [])

    tool_results_text = "\n\n".join(
        f"--- {r['tool_name']} (confidence: {r['confidence']:.2f}) ---\n{r['content']}"
        for r in results
    ) if results else "No tool results available."

    sources = deduplicate_ordered(
        r["source"] for r in results if r.get("source")
    )
    sources_text = "\n".join(f"[{i+1}] {s}" for i, s in enumerate(sources))

    messages = [
        {"role": "system", "content": "You are a helpful AI assistant."},
        {
            "role": "user",
            "content": SYNTHESIZER_PROMPT.format(
                query=state["user_query"],
                tool_results=tool_results_text,
                sources=sources_text,
            ),
        },
    ]

    # force_model="ollama" bypasses the circuit breaker entirely
    response, model_used = await llm_router.complete(
        messages=messages,
        temperature=0.3,
        max_tokens=1000,
        force_model="ollama",
    )

    final_answer = (
        response if isinstance(response, str)
        else "".join([t async for t in response])
    )

    elapsed = (time.monotonic() - start) * 1000

    return {
        "final_answer": final_answer,
        "sources":      sources,
        "messages":     [AIMessage(content=final_answer)],
        "latency_ms":   {"ollama_node": round(elapsed, 2)},
        "model_used":   model_used,
    }
