# backend/agent/nodes/response_streamer.py
"""
Phase 13 — True LLM token streaming via asyncio.Queue.

Architecture:
  1. Before graph.ainvoke(), websocket registers a Queue for the session:
       register_stream(session_id)  →  AsyncGenerator via read_stream()
  2. aggregator_node streams each LLM token into the queue:
       push_token(session_id, token_str)
  3. response_streamer node (last graph node) sends the DONE sentinel:
       finalize_stream(session_id)
  4. websocket reads tokens from read_stream() while ainvoke() runs.

If no Queue is registered (HTTP/REST path), push_token/finalize_stream are no-ops
and the word-split fallback in the REST handler handles streaming.
"""
import asyncio
import logging
from backend.agent.state import AgentState

logger = logging.getLogger(__name__)

_DONE = object()  # sentinel value

# session_id → asyncio.Queue
_queues: dict[str, asyncio.Queue] = {}


def register_stream(session_id: str, maxsize: int = 512) -> None:
    """Create a streaming queue for the session. Call before graph.ainvoke()."""
    _queues[session_id] = asyncio.Queue(maxsize=maxsize)
    logger.debug("Stream queue registered for session %s", session_id)


def unregister_stream(session_id: str) -> None:
    """Remove the queue after streaming is complete."""
    _queues.pop(session_id, None)


async def push_token(session_id: str, token: str) -> None:
    """
    Push one LLM token into the session's queue.
    No-op if no queue is registered (REST path).
    """
    q = _queues.get(session_id)
    if q is not None and token:
        try:
            await q.put(token)
        except Exception as exc:
            logger.warning("push_token failed for %s: %s", session_id, exc)


async def finalize_stream(session_id: str) -> None:
    """Send the DONE sentinel so the WebSocket reader knows streaming is over."""
    q = _queues.get(session_id)
    if q is not None:
        try:
            await q.put(_DONE)
        except Exception as exc:
            logger.warning("finalize_stream failed for %s: %s", session_id, exc)


async def read_stream(session_id: str):
    """
    Async generator — yields token strings until the DONE sentinel is received.
    Used by the websocket handler to forward tokens to the client.
    """
    q = _queues.get(session_id)
    if q is None:
        return
    while True:
        item = await q.get()
        if item is _DONE:
            break
        yield item


def is_streaming(session_id: str) -> bool:
    """True if a queue is registered for this session."""
    return session_id in _queues


# ── LangGraph node ────────────────────────────────────────────────────────────

async def response_streamer(state: AgentState) -> dict:
    """
    Final graph node.  Sends the DONE sentinel so the WebSocket reader unblocks.
    On the non-streaming (REST) path this is a fast no-op.
    """
    session_id = state.get("session_id", "")
    if session_id:
        await finalize_stream(session_id)

    return {}
