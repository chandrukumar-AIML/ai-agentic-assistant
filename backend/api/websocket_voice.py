# backend/api/websocket_voice.py
"""
Voice / audio-chunk WebSocket handler.

Receives base64-encoded audio frames from the browser, transcribes them with
Whisper (faster-whisper), runs the agent graph, and streams back TTS audio.

When faster_whisper / TTS are unavailable the handler degrades gracefully:
  - STT failure  → asks the user to send a text message instead
  - TTS failure  → returns the answer as a plain text 'token' event
"""
from __future__ import annotations

import asyncio
import base64
import logging
import time
from typing import TYPE_CHECKING

from fastapi import WebSocket

if TYPE_CHECKING:
    from backend.api.websocket import ConnectionManager

logger = logging.getLogger(__name__)

# ── Optional heavy deps ───────────────────────────────────────────────────────

try:
    from faster_whisper import WhisperModel as _WhisperModel  # type: ignore

    _whisper: "_WhisperModel | None" = _WhisperModel(
        "tiny",
        device="cpu",
        compute_type="int8",
    )
except Exception:
    _whisper = None

try:
    import httpx as _httpx  # already a project dep — used to call Coqui TTS
    _tts_available = True
except ImportError:
    _tts_available = False


# ── Public API ────────────────────────────────────────────────────────────────

async def handle_voice_message(
    websocket: WebSocket,
    payload: dict,
    session_id: str,
    graph,
    session_data: dict,
    manager: "ConnectionManager",
) -> None:
    """
    Entry point called from websocket_endpoint when msg_type == 'audio_chunk'.

    payload keys:
      audio   : base64-encoded PCM / WebM audio bytes
      final   : bool — True when this is the last chunk of an utterance
      language: optional ISO-639-1 language hint (default "en")
    """
    audio_b64: str = payload.get("audio", "")
    is_final:  bool = payload.get("final", True)
    language:  str = payload.get("language", "en")

    if not audio_b64:
        await _send(websocket, {"type": "error", "message": "Empty audio payload", "code": 400})
        return

    # Non-final chunks: buffer on client side; we only process complete utterances
    if not is_final:
        await _send(websocket, {"type": "audio_ack", "buffered": True})
        return

    # ── 1. Speech-to-text ────────────────────────────────────────────────────
    transcript = await _transcribe(audio_b64, language)
    if transcript is None:
        await _send(websocket, {
            "type": "error",
            "message": "Speech recognition unavailable — please type your message instead.",
            "code": 503,
        })
        return

    if not transcript.strip():
        await _send(websocket, {"type": "audio_ack", "transcript": "", "silence": True})
        return

    # Echo transcript back so the UI can display it
    await _send(websocket, {"type": "transcript", "data": transcript})

    # ── 2. Run agent graph ───────────────────────────────────────────────────
    if graph is None:
        answer = "Agent not available. Please try again later."
    else:
        try:
            from langchain_core.messages import HumanMessage
            from backend.agent.nodes.response_streamer import (
                register_stream, unregister_stream, read_stream,
            )

            voice_session = f"{session_id}_voice_{int(time.monotonic() * 1000)}"
            history = session_data.get("history", [])

            initial_state = {
                "messages":    history + [HumanMessage(content=transcript)],
                "user_query":  transcript,
                "session_id":  voice_session,
                "tool_results": [],
                "latency_ms":  {},
            }

            register_stream(voice_session)
            tokens: list[str] = []

            async def _run():
                return await graph.ainvoke(initial_state)

            async def _collect():
                async for tok in read_stream(voice_session):
                    tokens.append(tok)
                    # Forward tokens as text events so the UI shows them in real-time
                    await _send(websocket, {"type": "token", "data": tok})

            graph_task  = asyncio.create_task(_run())
            stream_task = asyncio.create_task(_collect())
            try:
                final_state, _ = await asyncio.gather(graph_task, stream_task)
            finally:
                unregister_stream(voice_session)

            answer = "".join(tokens) or (
                final_state.get("final_answer")
                or final_state.get("messages", [{}])[-1].get("content", "")
                or "Sorry, I could not generate a response."
            )
        except Exception as exc:
            logger.exception("Voice graph error: %s", exc)
            answer = "An error occurred while processing your request."

    # ── 3. Text-to-speech ────────────────────────────────────────────────────
    tts_audio = await _synthesise(answer)
    if tts_audio:
        await _send(websocket, {
            "type":   "audio_response",
            "audio":  base64.b64encode(tts_audio).decode(),
            "format": "wav",
        })
    else:
        # Degrade gracefully: answer already sent as token events above
        await _send(websocket, {"type": "voice_done", "text_fallback": True})


# ── Internal helpers ──────────────────────────────────────────────────────────

async def _transcribe(audio_b64: str, language: str) -> str | None:
    """Run Whisper STT in a thread pool. Returns None if unavailable."""
    if _whisper is None:
        return None
    try:
        audio_bytes = base64.b64decode(audio_b64)
        import io
        import numpy as np

        # faster-whisper needs a file-like or numpy array; use bytes buffer
        audio_buf = io.BytesIO(audio_bytes)

        def _sync_transcribe():
            segments, _ = _whisper.transcribe(audio_buf, language=language, beam_size=1)
            return " ".join(seg.text for seg in segments).strip()

        return await asyncio.to_thread(_sync_transcribe)
    except Exception as exc:
        logger.warning("STT error: %s", exc)
        return None


async def _synthesise(text: str) -> bytes | None:
    """Call Coqui TTS service. Returns raw audio bytes or None if unavailable."""
    if not _tts_available or not text:
        return None
    try:
        from backend.config import get_settings
        settings = get_settings()
        tts_url = getattr(settings, "coqui_tts_url", None) or "http://localhost:5002"

        async with _httpx.AsyncClient(timeout=30) as client:
            r = await client.get(f"{tts_url}/api/tts", params={"text": text[:500]})
            if r.status_code == 200:
                return r.content
    except Exception as exc:
        logger.warning("TTS synthesis error: %s", exc)
    return None


async def _send(websocket: WebSocket, data: dict) -> None:
    try:
        await websocket.send_json(data)
    except Exception:
        pass
