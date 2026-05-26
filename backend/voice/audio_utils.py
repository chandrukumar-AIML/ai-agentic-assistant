# backend/voice/audio_utils.py
"""
Audio format conversion utilities.
Browser sends raw PCM (Float32, 16kHz, mono).
Whisper needs WAV. TTS outputs MP3.
"""
import io
import wave
import struct
import base64
import numpy as np
import logging

logger = logging.getLogger(__name__)

SAMPLE_RATE    = 16000   # Whisper requirement
CHANNELS       = 1       # mono
SAMPLE_WIDTH   = 2       # 16-bit PCM


def pcm_float32_to_wav_bytes(
    pcm_data: bytes,
    sample_rate: int = SAMPLE_RATE,
) -> bytes:
    """
    Convert raw Float32 PCM bytes (from browser AudioWorklet)
    to a WAV file in memory.
    Whisper's faster-whisper accepts WAV or numpy array.
    """
    # Float32 bytes → numpy array
    float_array = np.frombuffer(pcm_data, dtype=np.float32)

    # Clamp to [-1, 1] to avoid clipping
    float_array = np.clip(float_array, -1.0, 1.0)

    # Convert to 16-bit signed PCM
    int_array = (float_array * 32767).astype(np.int16)

    # Write WAV to buffer
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(SAMPLE_WIDTH)
        wf.setframerate(sample_rate)
        wf.writeframes(int_array.tobytes())

    return buffer.getvalue()


def base64_to_pcm_bytes(b64_data: str) -> bytes:
    """Decode base64-encoded PCM from browser."""
    try:
        return base64.b64decode(b64_data)
    except Exception as e:
        logger.error(f"Base64 decode failed: {e}")
        return b""


def audio_bytes_to_base64(audio_bytes: bytes) -> str:
    """Encode audio bytes (MP3/WAV) to base64 for WebSocket transport."""
    return base64.b64encode(audio_bytes).decode("utf-8")


def is_silent(pcm_data: bytes, threshold: float = 0.01) -> bool:
    """
    Detect silence in PCM Float32 data.
    Used to avoid sending empty audio chunks to Whisper.
    """
    if not pcm_data:
        return True
    float_array = np.frombuffer(pcm_data, dtype=np.float32)
    rms = float(np.sqrt(np.mean(float_array ** 2)))
    return rms < threshold