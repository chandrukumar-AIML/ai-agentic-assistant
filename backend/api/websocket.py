# FIXED: file had multiple duplicate class/function definitions and bare module-level await statements.
# Removed all earlier draft sections (original, Phase D, Phase E/H comment fragments).
# Kept only the canonical Phase L version (ConnectionManager + websocket_endpoint below).
# Also fixed: bare api.* imports → backend.api.* throughout.

import json
import logging
import asyncio
import time
import uuid
from fastapi import WebSocket, WebSocketDisconnect

# FIXED: all imports below updated from bare api./session./observability. → backend.* prefix
from backend.api.auth              import verify_ws_token
from backend.session.redis_client  import get_session, save_session
from backend.observability.metrics import record_agent_run, active_sessions
from backend.guardrails.guard_engine import check_input, check_output_response
from backend.auth.rate_limiter       import check_rate_limit
from backend.audit.audit_logger      import log_agent_action
from backend.auth.models             import UserRole, PlanTier
from backend.auth.workspace          import WorkspaceContext as WsCtx
from backend.agent.nodes.response_streamer import (
    register_stream, unregister_stream, read_stream,
)
from langchain_core.messages import HumanMessage, AIMessage

logger = logging.getLogger(__name__)

_MAX_IMAGE_B64 = 28_000_000
_MAX_AUDIO_B64 = 10_000_000


# FIXED: removed original websocket_endpoint (Phase A), bare module-level await blocks (Phase B/C),
# Phase D rewrite, Phase E/H comment fragments with bare statements, and duplicate
# ConnectionManager/manager/websocket_endpoint definitions.
# Canonical Phase L version follows below.


class ConnectionManager:  # FIXED: single canonical definition kept
    def __init__(self):
        self._connections: dict[str, WebSocket] = {}

    async def connect(self, session_id: str, ws: WebSocket):
        await ws.accept()
        self._connections[session_id] = ws
        active_sessions.set(len(self._connections))

    def disconnect(self, session_id: str):
        self._connections.pop(session_id, None)
        active_sessions.set(len(self._connections))

    async def send(self, session_id: str, data: dict):
        ws = self._connections.get(session_id)
        if ws:
            try:
                await ws.send_json(data)
            except Exception:
                pass

    def is_connected(self, session_id: str) -> bool:
        return session_id in self._connections


manager = ConnectionManager()


async def _send_step(
    websocket:   WebSocket,
    session_id:  str,
    step:        str,
    description: str = "",
    metadata:    dict = None,
):
    """Send a reasoning step event to the React UI."""
    if not manager.is_connected(session_id):
        return
    try:
        await websocket.send_json({
            "type":        "agent_step",
            "step":        step,
            "description": description,
            "metadata":    metadata or {},
            "timestamp":   time.time(),
        })
    except Exception:
        pass


async def websocket_endpoint(websocket: WebSocket):
    token_payload = await verify_ws_token(websocket)
    if token_payload is None:
        return

    session_id = websocket.query_params.get("session_id", str(uuid.uuid4()))
    await manager.connect(session_id, websocket)

    # Lazy-compile LangGraph agent on first connection (saves ~150MB RAM at startup)
    if websocket.app.state.agent is None:
        async with websocket.app.state.agent_lock:
            if websocket.app.state.agent is None:   # double-check after lock
                try:
                    from backend.agent.graph import compile_graph
                    from langgraph.checkpoint.memory import MemorySaver
                    websocket.app.state.agent = compile_graph(checkpointer=MemorySaver())
                    logger.info("LangGraph agent compiled on first WS connection")
                except Exception as e:
                    logger.warning(f"LangGraph compile failed: {e}")

    graph = websocket.app.state.agent

    try:
        while True:
            try:
                raw = await asyncio.wait_for(websocket.receive_text(), timeout=300.0)
            except asyncio.TimeoutError:
                await websocket.send_json({"type": "error", "message": "Session timeout", "code": 408})
                break

            try:
                payload = json.loads(raw)
            except json.JSONDecodeError as e:
                logger.debug(f"WS JSON parse error from {session_id}: {e}")  # FIXED: log internally
                await websocket.send_json({"type": "error", "message": "Invalid JSON message", "code": 400})  # FIXED: str(e) → generic message (prevents leaking parse internals)
                continue

            msg_type = payload.get("type", "text")

            if msg_type == "ping":
                await websocket.send_json({"type": "pong"})
                continue

            if msg_type == "audio_chunk":
                session_data = await get_session(session_id) or {}
                from backend.api.websocket_voice import handle_voice_message
                await handle_voice_message(websocket, payload, session_id, graph, session_data, manager)
                continue

            # ── Text / Vision message ──────────────────────────────────────
            content    = payload.get("content", "")
            image_data = payload.get("image")

            if image_data and len(image_data) > _MAX_IMAGE_B64:
                await websocket.send_json({"type": "error", "message": "Image too large", "code": 413})
                continue

            # Workspace context
            workspace_ctx = WsCtx.from_slug(
                workspace_slug=token_payload.get("workspace_slug", "default"),
                workspace_id=token_payload.get("workspace_id", ""),
                user_id=token_payload.get("sub", "anonymous"),
                user_email=token_payload.get("email", ""),
                role=UserRole(token_payload.get("role", "user")),
                plan_tier=PlanTier(token_payload.get("plan_tier", "free")),
            )

            # Rate limit — Redis may be down; default to allow on failure
            try:
                allowed, count, limit = await check_rate_limit(
                    user_id=workspace_ctx.user_id,
                    workspace_id=workspace_ctx.workspace_id,
                    plan_tier=workspace_ctx.plan_tier,
                )
            except Exception as rl_err:
                logger.warning("Rate limit check failed (allowing): %s", rl_err)
                allowed, count, limit = True, 0, 9_999
            if not allowed:
                await websocket.send_json({
                    "type":    "error",
                    "message": f"Daily limit reached ({count}/{limit}). Resets midnight UTC.",
                    "code":    429,
                })
                continue

            # ── Step 1: Input guardrail ────────────────────────────────────
            await _send_step(websocket, session_id, "guardrail_check",
                             "Checking input safety...")

            # Guardrail may fail (Presidio/OpenAI down); treat as safe on error
            try:
                guard_result = await check_input(
                    user_input=content,
                    user_id=workspace_ctx.user_id,
                    domain=payload.get("domain", "general"),
                    session_id=session_id,
                )
            except Exception as guard_err:
                logger.warning("Input guardrail failed (bypassing): %s", guard_err)
                guard_result = None

            if guard_result is not None and not guard_result.passed:
                await websocket.send_json({
                    "type":       "error",
                    "message":    guard_result.block_reason or "Request blocked",
                    "code":       400,
                    "guard_flag": guard_result.flag,
                })
                continue

            if guard_result is not None and guard_result.pii_detected:
                await websocket.send_json({
                    "type":    "guard_event",
                    "flag":    "redacted",
                    "message": f"PII detected and masked: {guard_result.pii_types}",
                })

            safe_content = guard_result.processed_input if guard_result is not None else content

            # ── Step 2: Load session history ───────────────────────────────
            session_data   = await get_session(session_id) or {}
            prior_messages = session_data.get("messages", [])

            history = []
            for m in prior_messages[-20:]:
                if isinstance(m, (HumanMessage, AIMessage)):
                    history.append(m)
                elif isinstance(m, dict):
                    cls_map = {"human": HumanMessage, "ai": AIMessage}
                    cls = cls_map.get(m.get("role"))
                    if cls:
                        history.append(cls(content=m["content"]))

            trace_id = str(uuid.uuid4())

            # ── Step 3: Memory loading ─────────────────────────────────────
            await _send_step(websocket, session_id, "memory_load",
                             "Loading your memory context...")

            initial_state = {
                "messages":              history + [HumanMessage(content=safe_content)],
                "user_query":            safe_content,
                "image_data":            image_data,
                "session_id":            session_id,
                "user_id":               workspace_ctx.mem0_user_id,
                "workspace_id":          workspace_ctx.workspace_id,
                "workspace_slug":        workspace_ctx.workspace_slug,
                "chroma_collection":     workspace_ctx.chroma_collection,
                "neo4j_workspace":       workspace_ctx.neo4j_workspace,
                "memory_context":        "",
                "intent":                "",
                "plan":                  [],
                "selected_tools":        [],
                "tool_results":          [],
                "retry_count":           0,
                "max_retries":           3,
                "final_answer":          None,
                "sources":               [],
                "trace_id":              trace_id,
                "latency_ms":            {},
                "model_used":            "gpt-4o",
                "error":                 None,
                "reflection_score":      0.0,
                "reflection_verdict":    "fail",
                "reflection_critique":   "",
                "reflection_missing":    [],
                "reflection_attempts":   0,
                "reflection_history":    [],
                "supervisor_workers":    [],
                "supervisor_parallel":   True,
                "supervisor_aggregation":"merge",
                "supervisor_decision":   "",
                "worker_results":        [],
                "ab_log_entry_id":       None,
                "browser_screenshots":   [],
                "browser_actions_log":   [],
                "browser_final_url":     None,
                "plan_tier":             workspace_ctx.plan_tier.value,
            }

            run_start = time.monotonic()

            try:
                # ── Step 4: Supervisor routing ─────────────────────────────
                await _send_step(websocket, session_id, "supervisor",
                                 "Analysing query and routing to specialists...")

                # Register streaming queue BEFORE ainvoke so aggregator can
                # push tokens as soon as the LLM starts generating.
                _tokens_sent_ = 0   # initialise here; updated in the else branch
                if graph is not None:
                    register_stream(session_id)

                if graph is None:
                    # ── Ollama fallback (LangGraph/PyTorch unavailable) ─────
                    await _send_step(websocket, session_id, "ollama_fallback",
                                     "LangGraph unavailable — using Ollama llama3.2 directly...")
                    try:
                        from backend.llm.ollama_client import ollama_chat

                        # Build message list from session history + new message
                        ollama_messages: list[dict] = [
                            {"role": "system", "content": (
                                "You are a helpful, knowledgeable AI assistant. "
                                "Answer clearly and concisely. If you are unsure, say so."
                            )}
                        ]
                        for m in history:
                            if isinstance(m, HumanMessage):
                                ollama_messages.append({"role": "user",      "content": str(m.content)})
                            elif isinstance(m, AIMessage):
                                ollama_messages.append({"role": "assistant", "content": str(m.content)})
                        ollama_messages.append({"role": "user", "content": safe_content})
                        # Keep window manageable — system + last 10 turns
                        if len(ollama_messages) > 11:
                            ollama_messages = ollama_messages[:1] + ollama_messages[-10:]

                        answer = await ollama_chat(
                            messages=ollama_messages,
                            max_tokens=600,
                            num_ctx=1024,
                            stream=False,
                        ) or "I'm sorry, I couldn't generate a response. Please try again."
                    except Exception as ollama_err:
                        logger.error("Ollama WS fallback failed for %s: %s", session_id, ollama_err)
                        answer = "The AI assistant is temporarily unavailable. Please try again shortly."

                    final_state = {
                        "final_answer":          answer,
                        "model_used":            "ollama/llama3.2",
                        "sources":               [],
                        "latency_ms":            {},
                        "intent":                "general",
                        "reflection_score":      0.0,
                        "reflection_attempts":   0,
                        "reflection_history":    [],
                        "supervisor_decision":   "ollama_direct",
                        "supervisor_workers":    [],
                        "worker_results":        [],
                        "browser_final_url":     None,
                        "browser_actions_log":   [],
                        "ab_log_entry_id":       None,
                        "error":                 None,
                    }
                else:
                    # ── True token streaming via asyncio.Queue ─────────────
                    # Run ainvoke() and queue reader concurrently.
                    # The aggregator_node pushes LLM tokens when it uses the
                    # merge LLM call (multiple workers).  For single-worker
                    # results the queue is empty — we detect this and fall back
                    # to word-split streaming after ainvoke() completes.

                    tokens_sent = 0

                    async def _run_graph():
                        return await graph.ainvoke(initial_state)

                    async def _stream_tokens():
                        """Forward LLM tokens to WebSocket as they arrive."""
                        nonlocal tokens_sent
                        async for token in read_stream(session_id):
                            if not manager.is_connected(session_id):
                                break
                            try:
                                await websocket.send_json({"type": "token", "data": token})
                                tokens_sent += 1
                            except Exception:
                                break

                    graph_task  = asyncio.create_task(_run_graph())
                    stream_task = asyncio.create_task(_stream_tokens())

                    try:
                        await asyncio.gather(stream_task, graph_task)
                    except Exception:
                        graph_task.cancel()
                        stream_task.cancel()
                        raise
                    finally:
                        unregister_stream(session_id)

                    final_state    = graph_task.result()
                    _tokens_sent_  = tokens_sent  # capture for fallback check below

                # Send supervisor decision as a step
                if final_state.get("supervisor_decision"):
                    workers = [
                        w.get("worker", w.get("worker_name", ""))
                        for w in (
                            final_state.get("supervisor_workers") or
                            final_state.get("worker_results") or []
                        )
                    ]
                    await _send_step(
                        websocket, session_id, "routing_decision",
                        f"Routing to: {', '.join(workers) or 'research agent'}",
                        metadata={"workers": workers, "parallel": final_state.get("supervisor_parallel")},
                    )

                # Worker steps
                for worker in final_state.get("worker_results", []):
                    name    = worker.get("worker_name", "")
                    latency = worker.get("latency_ms", 0)
                    had_err = bool(worker.get("error"))
                    await _send_step(
                        websocket, session_id, "worker_complete",
                        f"{name} finished in {latency:.0f}ms",
                        metadata={
                            "worker":     name,
                            "latency_ms": latency,
                            "error":      had_err,
                            "confidence": worker.get("confidence", 0),
                        },
                    )

                # Reflection steps
                for entry in final_state.get("reflection_history", []):
                    await _send_step(
                        websocket, session_id, "reflection",
                        f"Quality check loop {entry.get('attempt')}: {entry.get('score')}/10 — {entry.get('verdict')}",
                        metadata={
                            "loop":     entry.get("attempt"),
                            "score":    entry.get("score"),
                            "verdict":  entry.get("verdict"),
                            "critique": entry.get("critique", "")[:120],
                        },
                    )
                    if entry.get("verdict") == "fail":
                        await _send_step(
                            websocket, session_id, "rewrite",
                            f"Rewriting answer (score was {entry.get('score')}/10)...",
                        )

                # ── Step 5: Output guardrail ───────────────────────────────
                await _send_step(websocket, session_id, "output_check",
                                 "Verifying response safety...")

                final_answer = final_state.get("final_answer") or ""

                output_guard = await check_output_response(
                    response=final_answer,
                    tool_results=final_state.get("tool_results", []),
                    domain=payload.get("domain", "general"),
                    user_id=workspace_ctx.user_id,
                    session_id=session_id,
                )
                safe_response = output_guard.processed_response

                # ── Word-split fallback ────────────────────────────────────
                # Used when (a) the Ollama direct-fallback path ran (graph is
                # None) or (b) the aggregator used a single-worker shortcut
                # and pushed zero tokens to the queue.
                needs_fallback = (graph is None) or (
                    graph is not None and _tokens_sent_ == 0
                )
                if needs_fallback and safe_response:
                    words = [w + " " for w in safe_response.split()]
                    for token in words:
                        if not manager.is_connected(session_id):
                            break
                        await websocket.send_json({"type": "token", "data": token})
                        await asyncio.sleep(0)

                # ── Done signal ────────────────────────────────────────────
                await websocket.send_json({
                    "type":                 "done",
                    "sources":              final_state.get("sources", []),
                    "model":                final_state.get("model_used", "gpt-4o"),
                    "latency_ms":           final_state.get("latency_ms", {}),
                    "trace_id":             trace_id,
                    "intent":               final_state.get("intent", ""),
                    "reflection_score":     final_state.get("reflection_score", 0.0),
                    "reflection_attempts":  final_state.get("reflection_attempts", 0),
                    "reflection_history":   final_state.get("reflection_history", []),
                    "supervisor_decision":  final_state.get("supervisor_decision", ""),
                    "workers_used": [
                        {
                            "name":       w.get("worker_name", ""),
                            "confidence": w.get("confidence", 0),
                            "latency_ms": w.get("latency_ms", 0),
                        }
                        for w in final_state.get("worker_results", [])
                    ],
                    "guard_input_flag":     guard_result.flag if guard_result else "none",
                    "guard_output_flag":    output_guard.flag,
                    "pii_masked":           guard_result.pii_detected if guard_result else False,
                    "hallucination_flag":   output_guard.hallucination_flag,
                    "browser_final_url":    final_state.get("browser_final_url"),
                    "browser_actions_log":  final_state.get("browser_actions_log", []),
                    "ab_log_entry_id":      final_state.get("ab_log_entry_id"),
                })

                # ── Persist ────────────────────────────────────────────────
                updated = prior_messages + [
                    {"role": "human", "content": safe_content},
                    {"role": "ai",    "content": safe_response, "ts": time.time()},
                ]
                await save_session(session_id, {"messages": updated})

                log_agent_action(
                    user_id=workspace_ctx.user_id,
                    workspace_id=workspace_ctx.workspace_id,
                    session_id=session_id,
                    trace_id=trace_id,
                    action="query",
                    worker_agents=[w.get("worker_name", "") for w in final_state.get("worker_results", [])],
                    latency_ms=int(sum(final_state.get("latency_ms", {}).values())),
                    model_used=final_state.get("model_used", "gpt-4o"),
                    reflection_loops=final_state.get("reflection_attempts", 0),
                    pii_detected=guard_result.pii_detected if guard_result else False,
                    guardrail_triggered=not guard_result.passed if guard_result else False,
                    error=final_state.get("error"),
                )

                record_agent_run(
                    status="error" if final_state.get("error") else "success",
                    latency_s=time.monotonic() - run_start,
                    node_times=final_state.get("latency_ms", {}),
                )

            except Exception as e:
                logger.error(f"Agent error {session_id}: {e}", exc_info=True)
                await websocket.send_json({
                    "type": "error", "message": "Agent failed — please try again", "code": 500
                })

    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(session_id)