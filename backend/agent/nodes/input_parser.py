import time
import uuid
from backend.agent.state import AgentState


async def input_parser(state: AgentState) -> dict:
    start = time.monotonic()

    query = state["user_query"].strip()
    has_image = state.get("image_data") is not None

    if has_image and not query:
        query = "Describe and analyse this image in detail."

    elapsed = (time.monotonic() - start) * 1000

    return {
        "user_query":  query,
        "trace_id":    state.get("trace_id") or str(uuid.uuid4()),
        "retry_count": 0,
        "max_retries": 3,
        "tool_results": [],
        "sources":     [],
        "error":       None,
        "latency_ms":  {"input_parser": round(elapsed, 2)},
        "model_used":  "gpt-4o",
    } 

# backend/agent/nodes/input_parser.py  — UPDATED for Phase B
import time
import uuid
from backend.agent.state import AgentState


async def input_parser(state: AgentState) -> dict:
    start     = time.monotonic()
    query     = state["user_query"].strip()
    has_image = state.get("image_data") is not None

    if has_image and not query:
        query = "Describe and analyse this image in detail."

    elapsed = (time.monotonic() - start) * 1000

    return {
        "user_query":  query,
        "trace_id":    state.get("trace_id") or str(uuid.uuid4()),
        "retry_count": 0,
        "max_retries": 3,
        "tool_results": [],
        "sources":     [],
        "error":       None,
        "latency_ms":  {"input_parser": round(elapsed, 2)},
        "model_used":  "gpt-4o",
        # Phase B: initialise reflection fields
        "reflection_score":    0.0,
        "reflection_verdict":  "fail",
        "reflection_critique": "",
        "reflection_missing":  [],
        "reflection_attempts": 0,
        "reflection_history":  [],
    }