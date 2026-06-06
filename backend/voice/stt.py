# backend/voice/stt.py
"""
Speech-to-Text using faster-whisper (local, no API cost).
Model: large-v3 for best accuracy, or base for fastest inference.
Auto-detects language.
"""
import io
import logging
import asyncio
import time
from functools import lru_cache
from typing import Optional

try:
    from faster_whisper import WhisperModel
    _WHISPER_AVAILABLE = True
except ImportError:
    WhisperModel = None  # type: ignore
    _WHISPER_AVAILABLE = False

from backend.voice.audio_utils import pcm_float32_to_wav_bytes, is_silent
from backend.config import get_settings

logger   = logging.getLogger(__name__)
settings = get_settings()

# Whisper model sizes: tiny / base / small / medium / large-v3
# large-v3 = best accuracy (~1.5GB), base = fastest (~145MB)
WHISPER_MODEL_SIZE = "base"     # change to "large-v3" in production
WHISPER_DEVICE     = "cpu"      # "cuda" if GPU available
WHISPER_COMPUTE    = "int8"     # quantised for CPU efficiency


@lru_cache(maxsize=1)
def _get_whisper_model() -> WhisperModel:
    """
    Load Whisper model once. Cached via lru_cache.
    Loading takes ~5s for base, ~20s for large-v3.
    """
    logger.info(f"Loading Whisper {WHISPER_MODEL_SIZE} model...")
    start = time.monotonic()
    model = WhisperModel(
        WHISPER_MODEL_SIZE,
        device=WHISPER_DEVICE,
        compute_type=WHISPER_COMPUTE,
        download_root="./data/whisper_models",
    )
    elapsed = (time.monotonic() - start) * 1000
    logger.info(f"Whisper model loaded in {elapsed:.0f}ms")
    return model


async def transcribe_audio(
    pcm_data:     bytes,
    language:     Optional[str] = None,   # None = auto-detect
    min_duration: float = 0.5,            # seconds — ignore very short clips
) -> dict:
    """
    Transcribe PCM Float32 audio bytes to text.
    Returns dict with: text, language, confidence, duration_s.

    Runs Whisper in a thread (CPU-bound, would block event loop).
    """
    if is_silent(pcm_data):
        return {"text": "", "language": "en", "confidence": 0.0, "duration_s": 0.0}

    wav_bytes = pcm_float32_to_wav_bytes(pcm_data)

    def _run_whisper() -> dict:
        model  = _get_whisper_model()
        audio  = io.BytesIO(wav_bytes)

        segments, info = model.transcribe(
            audio,
            language=language,       # None = auto-detect
            beam_size=5,
            vad_filter=True,         # Voice Activity Detection — skip silence
            vad_parameters={
                "min_silence_duration_ms": 300,
                "speech_pad_ms":           400,
            },
        )

        # Collect all segments
        transcript_parts = []
        avg_logprob_sum  = 0.0
        segment_count    = 0

        for seg in segments:
            transcript_parts.append(seg.text.strip())
            avg_logprob_sum += seg.avg_logprob
            segment_count   += 1

        text       = " ".join(transcript_parts).strip()
        confidence = (
            float(2 ** (avg_logprob_sum / segment_count))
            if segment_count > 0 else 0.0
        )

        return {
            "text":        text,
            "language":    info.language,
            "confidence":  min(confidence, 1.0),
            "duration_s":  info.duration,
        }

    try:
        # Run Whisper in thread pool — it's CPU-bound
        # FIXED: added timeout to prevent indefinite hang if Whisper model stalls
        result = await asyncio.wait_for(
            asyncio.to_thread(_run_whisper),
            timeout=120.0,  # 2 min max for large-v3 on CPU
        )
        logger.info(
            f"STT: '{result['text'][:60]}' "
            f"(lang={result['language']}, conf={result['confidence']:.2f})"
        )
        return result
    except asyncio.TimeoutError:
        logger.error("Whisper transcription timed out after 120s")  # FIXED: timeout on STT call
        return {"text": "", "language": "en", "confidence": 0.0, "duration_s": 0.0, "error": "transcription timeout"}
    except Exception as e:
        logger.error(f"Whisper transcription failed: {e}", exc_info=True)
        return {"text": "", "language": "en", "confidence": 0.0, "duration_s": 0.0, "error": str(e)}


async def warmup_whisper():
    """
    Pre-load the Whisper model at startup.
    Call from FastAPI lifespan to avoid cold start on first voice message.
    """
    try:
        await asyncio.to_thread(_get_whisper_model)
        logger.info("Whisper warmup complete")
    except Exception as e:
        logger.warning(f"Whisper warmup failed (non-fatal): {e}")