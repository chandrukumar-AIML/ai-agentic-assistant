# backend/agent/nodes/aggregator_node.py
"""
Aggregates worker results into a single coherent final answer.
Strategy: merge | primary | sequential
"""
import time
import logging
from langchain_core.messages import AIMessage
from backend.agent.state     import AgentState
from backend.llm.router      import llm_router
from backend.utils.text      import deduplicate_ordered
from backend.observability.mlflow_logger import log_agent_run

logger = logging.getLogger(__name__)

MERGE_PROMPT = """You are an answer aggregator. Multiple specialist agents have worked on a query.
Synthesise their outputs into ONE coherent, well-structured answer.

User query: {query}

Worker outputs:
{worker_outputs}

Rules:
1. Do NOT say "Agent 1 says... Agent 2 says..." — synthesise directly
2. Resolve any contradictions (prefer higher-confidence source)
3. Cite sources where provided
4. Produce the best possible unified answer
5. Include code blocks if any worker generated code
6. Be comprehensive but not repetitive"""


async def aggregator_node(state: AgentState) -> dict:
    """
    Merges worker results into a final answer.
    Handles three aggregation strategies.
    """
    start         = time.monotonic()
    worker_results = state.get("worker_results", [])
    strategy      = state.get("supervisor_aggregation", "merge")
    query         = state["user_query"]

    if not worker_results:
        return {
            "final_answer": "No worker agents produced results. Please try again.",
            "sources":      [],
            "model_used":   "none",
            "latency_ms":   {"aggregator": 0.0},
        }

    # Collect all sources
    all_sources = deduplicate_ordered(
        src
        for w in worker_results
        for src in w.get("sources", [])
    )

    # Handle single worker — no aggregation needed
    if len(worker_results) == 1:
        result = worker_results[0]
        return {
            "final_answer": result["content"],
            "sources":      all_sources,
            "model_used":   state.get("model_used", "gpt-4o"),
            "messages":     [AIMessage(content=result["content"])],
            "latency_ms":   {"aggregator": round((time.monotonic() - start) * 1000, 2)},
        }

    if strategy == "primary":
        # First (highest priority) worker is main, others supplement
        primary     = worker_results[0]
        supplements = worker_results[1:]
        sup_text    = "\n\n".join(
            f"[{w['worker_name']}]: {w['content'][:400]}"
            for w in supplements
            if not w.get("error")
        )
        final_answer = primary["content"]
        if sup_text:
            final_answer += f"\n\n---\n**Additional context:**\n{sup_text}"

    elif strategy == "sequential":
        # Outputs are already chained — last worker has the final answer
        final_answer = worker_results[-1]["content"]

    else:
        # Merge strategy — LLM synthesises all outputs
        worker_outputs = "\n\n---\n\n".join(
            f"**{w['worker_name']}** (confidence: {w['confidence']:.1%}):\n{w['content']}"
            for w in worker_results
            if not w.get("error") and w.get("content")
        )

        memory_context = state.get("memory_context", "")
        system = (
            f"You synthesise multiple expert outputs into one answer."
            f"{memory_context}"
        )
        messages = [
            {"role": "system", "content": system},
            {
                "role": "user",
                "content": MERGE_PROMPT.format(
                    query=query,
                    worker_outputs=worker_outputs,
                ),
            },
        ]

        session_id = state.get("session_id", "")

        from backend.agent.nodes.response_streamer import (
            is_streaming, push_token,
        )

        if is_streaming(session_id):
            # ── True token streaming path (WebSocket) ─────────────────────
            # Use stream=True so LLM emits tokens one by one into the queue.
            response, model_used = await llm_router.complete(
                messages=messages,
                temperature=0.2,
                max_tokens=1500,
                stream=True,
            )
            chunks: list[str] = []
            if isinstance(response, str):
                # Router returned a string despite stream=True (e.g. Ollama error fallback)
                await push_token(session_id, response)
                chunks.append(response)
            else:
                # response is an async generator of token strings
                async for token in response:
                    await push_token(session_id, token)
                    chunks.append(token)
            final_answer = "".join(chunks)
        else:
            # ── Non-streaming path (REST / unit tests) ────────────────────
            response, model_used = await llm_router.complete(
                messages=messages,
                temperature=0.2,
                max_tokens=1500,
            )
            final_answer = response if isinstance(response, str) else worker_results[0]["content"]

    elapsed = (time.monotonic() - start) * 1000

    # Log to MLflow
    try:
        log_agent_run(
            session_id=state.get("session_id", "unknown"),
            query=query,
            intent=state.get("intent", "multi_agent"),
            selected_tools=[w["worker_name"] for w in worker_results],
            model_used=state.get("model_used", "gpt-4o"),
            latency_ms={**state.get("latency_ms", {}), "aggregator": round(elapsed, 2)},
            final_answer=final_answer,
            sources=all_sources,
            retry_count=0,
            error=None,
        )
    except Exception as e:  # FIXED: bare except silently swallowed MLflow logging errors
        logger.warning(f"MLflow logging failed (non-fatal): {e}")

    logger.info(
        f"Aggregator: strategy={strategy}, "
        f"workers={len(worker_results)}, "
        f"answer_len={len(final_answer)}"
    )

    return {
        "final_answer": final_answer,
        "sources":      all_sources,
        "model_used":   state.get("model_used", "gpt-4o"),
        "messages":     [AIMessage(content=final_answer)],
        "latency_ms":   {"aggregator": round(elapsed, 2)},
    }