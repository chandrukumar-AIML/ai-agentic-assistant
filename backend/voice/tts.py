# backend/voice/tts.py
"""
Text-to-Speech with two backends:
  1. Coqui TTS (default) — self-hosted, free, runs in Docker
  2. ElevenLabs API      — cloud, best quality, set ELEVENLABS_API_KEY

Auto-selects based on ELEVENLABS_API_KEY presence in config.
"""
import io
import asyncio
import logging
import time
from typing import AsyncGenerator

import httpx

from backend.config import get_settings

logger   = logging.getLogger(__name__)
settings = get_settings()

# Coqui TTS Docker service URL — FIXED: use settings instead of hardcoded localhost URL
COQUI_TTS_URL   = getattr(settings, "coqui_tts_url", "http://aaa_coqui_tts:5002/api/tts")  # FIXED: from settings, fallback for backward compat
ELEVENLABS_URL   = "https://api.elevenlabs.io/v1/text-to-speech"

# Default ElevenLabs voice — "Rachel" (natural, clear)
DEFAULT_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"

_httpx_client = httpx.AsyncClient(timeout=30.0)


class TTSError(Exception):
    pass


async def synthesise_speech_coqui(
    text:      str,
    speaker:   str = "p230",     # Coqui speaker ID
    speed:     float = 1.0,
) -> bytes:
    """
    Synthesise speech via Coqui TTS Docker service.
    Returns MP3 bytes.
    """
    try:
        response = await _httpx_client.get(
            COQUI_TTS_URL,
            params={
                "text":    text,
                "speaker": speaker,
                "speed":   speed,
            },
        )
        response.raise_for_status()
        return response.content    # WAV bytes from Coqui
    except httpx.HTTPError as e:
        raise TTSError(f"Coqui TTS request failed: {e}")


async def synthesise_speech_elevenlabs(
    text:     str,
    voice_id: str   = DEFAULT_VOICE_ID,
    stability:         float = 0.5,
    similarity_boost:  float = 0.75,
    style:             float = 0.0,
    use_speaker_boost: bool  = True,
) -> bytes:
    """
    Synthesise speech via ElevenLabs API.
    Returns MP3 bytes.
    """
    if not settings.elevenlabs_api_key:
        raise TTSError("ELEVENLABS_API_KEY not set")

    payload = {
        "text":           text,
        "model_id":       "eleven_turbo_v2",   # fastest + cheapest model
        "voice_settings": {
            "stability":         stability,
            "similarity_boost":  similarity_boost,
            "style":             style,
            "use_speaker_boost": use_speaker_boost,
        },
    }

    try:
        response = await _httpx_client.post(
            f"{ELEVENLABS_URL}/{voice_id}",
            json=payload,
            headers={
                "xi-api-key":   settings.elevenlabs_api_key,
                "Accept":       "audio/mpeg",
                "Content-Type": "application/json",
            },
        )
        response.raise_for_status()
        return response.content   # MP3 bytes
    except httpx.HTTPError as e:
        raise TTSError(f"ElevenLabs request failed: {e}")


async def synthesise_speech(
    text:     str,
    voice_id: str | None = None,
) -> bytes:
    """
    Auto-select TTS backend.
    ElevenLabs if API key set, else Coqui.
    """
    if not text.strip():
        return b""

    start = time.monotonic()

    # Truncate very long responses — TTS is expensive for long text
    # Split into sentences for streaming (Phase L will improve this)
    text_capped = text[:1500] if len(text) > 1500 else text
    if len(text) > 1500:
        text_capped += "... [response truncated for voice]"

    try:
        if settings.elevenlabs_api_key:
            audio_bytes = await synthesise_speech_elevenlabs(
                text=text_capped,
                voice_id=voice_id or DEFAULT_VOICE_ID,
            )
            backend = "elevenlabs"
        else:
            audio_bytes = await synthesise_speech_coqui(text=text_capped)
            backend     = "coqui"

        elapsed = (time.monotonic() - start) * 1000
        logger.info(
            f"TTS [{backend}]: {len(text_capped)} chars → "
            f"{len(audio_bytes)} bytes in {elapsed:.0f}ms"
        )
        return audio_bytes

    except TTSError as e:
        logger.error(f"TTS failed: {e}")
        return b""


async def synthesise_streaming(
    text:     str,
    chunk_size: int = 4096,
) -> AsyncGenerator[bytes, None]:
    """
    Stream audio in chunks for lower latency.
    Yields audio bytes as they become available.
    """
    audio_bytes = await synthesise_speech(text)
    if not audio_bytes:
        return

    for i in range(0, len(audio_bytes), chunk_size):
        yield audio_bytes[i: i + chunk_size]
        await asyncio.sleep(0)   # yield control to event loop