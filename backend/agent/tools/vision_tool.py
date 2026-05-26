import time
import base64
import logging
from backend.agent.state import AgentState
from backend.agent.tools.base_tool import make_tool_result
from backend.llm.vision_preprocessor import encode_from_base64, ImageProcessingError
from backend.config import get_settings
from backend.llm.ollama_openai import ollama_chat_completion, OLLAMA_MODEL

logger = logging.getLogger(__name__)
settings = get_settings()


def _get_vision_client():
    """Lazy-load OpenAI vision client (only if API key is set)."""
    try:
        from openai import AsyncOpenAI
        key = settings.openai_api_key
        if key and key.startswith("sk-"):
            return AsyncOpenAI(api_key=key)
    except Exception:
        pass
    return None

VISION_PROMPTS = {
    "ocr": (
        "Extract ALL text from this image verbatim. Preserve formatting. "
        "If there is no text, respond: '[No text found]'"
    ),
    "chart": (
        "Analyse this chart in detail: 1) Chart type 2) Title and axis labels "
        "3) Key data values and trends 4) Main insight. Be precise with numbers."
    ),
    "diagram": (
        "Analyse this diagram: 1) Type of diagram 2) Components and connections "
        "3) Labels and annotations 4) Overall system or process depicted."
    ),
    "code": (
        "Extract the complete code as plain text, preserving indentation. "
        "Note: the language, any visible errors, and what the code does."
    ),
    "general": (
        "Analyse this image in detail. Focus on elements relevant to the user's question."
    ),
}


def _detect_analysis_mode(query: str) -> str:
    q = query.lower()
    if any(w in q for w in ["text", "read", "ocr", "extract", "written", "says", "write"]):
        return "ocr"
    if any(w in q for w in ["chart", "graph", "plot", "bar", "pie", "trend", "data"]):
        return "chart"
    if any(w in q for w in ["diagram", "flow", "architecture", "uml", "schema"]):
        return "diagram"
    if any(w in q for w in ["code", "function", "class", "error", "exception", "syntax"]):
        return "code"
    return "general"


def _detect_mime_type(b64_data: str) -> str:
    """Detect image MIME type from base64 header bytes."""
    try:
        header = base64.b64decode(b64_data[:16])
        if header[:4] == b'\x89PNG':
            return "image/png"
        if header[:6] in (b'GIF87a', b'GIF89a'):
            return "image/gif"
        if header[:4] == b'RIFF':
            return "image/webp"
    except Exception:
        pass
    return "image/jpeg"  # safe default


async def vision_analyzer_node(state: AgentState) -> dict:
    start = time.monotonic()
    image_data = state.get("image_data")
    query = state.get("user_query", "")

    if not image_data:
        result = make_tool_result(
            tool_name="vision_tool",
            content="No image attached — vision tool skipped.",
            source="vision_skip",
            confidence=0.95,
            metadata={"skipped": True},
        )
        elapsed = (time.monotonic() - start) * 1000
        return {
            "tool_results": state.get("tool_results", []) + [result],
            "latency_ms":   {"vision_analyzer": round(elapsed, 2)},
        }

    # Preprocess image
    try:
        img_meta = encode_from_base64(image_data, query=query)
    except ImageProcessingError as e:
        result = make_tool_result(
            tool_name="vision_tool",
            content=f"Image preprocessing failed: {str(e)}",
            confidence=0.0,
            metadata={"error": str(e)},
        )
        elapsed = (time.monotonic() - start) * 1000
        return {
            "tool_results": state.get("tool_results", []) + [result],
            "latency_ms":   {"vision_analyzer": round(elapsed, 2)},
        }

    mode = _detect_analysis_mode(query)
    media_type = img_meta["media_type"]

    messages = [
        {"role": "system", "content": VISION_PROMPTS[mode]},
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url":    f"data:{media_type};base64,{img_meta['base64_data']}",
                        "detail": img_meta["detail"],
                    },
                },
                {"type": "text", "text": query or "Describe this image."},
            ],
        },
    ]

    vision_client = _get_vision_client()
    try:
        if vision_client is None:
            raise RuntimeError("OpenAI Vision not available — no valid API key")
        response = await vision_client.chat.completions.create(
            model=settings.openai_model,
            messages=messages,
            max_tokens=1500,
            temperature=0.1,
        )
        vision_text = response.choices[0].message.content
        finish_reason = response.choices[0].finish_reason
        usage = response.usage

        if finish_reason == "length":
            vision_text += "\n\n[Note: response truncated — increase max_tokens]"
            logger.warning("Vision response truncated")

        vision_confidence = 0.92 if finish_reason != "length" else 0.70
        result = make_tool_result(
            tool_name="vision_tool",
            content=vision_text,
            source="gpt-4o-vision",
            confidence=vision_confidence,
            metadata={
                "mode":            mode,
                "detail":          img_meta["detail"],
                "image_size":      f"{img_meta['width']}×{img_meta['height']}",
                "finish_reason":   finish_reason,
                "confidence_basis":"heuristic",
            },
        )

    except Exception as e:
        logger.warning(f"Vision tool call failed, using text fallback: {type(e).__name__}")
        # Ollama text fallback — describe image without vision
        fallback_text = await ollama_chat_completion(
            messages=[
                {"role": "system", "content": VISION_PROMPTS.get(mode, VISION_PROMPTS["general"])},
                {"role": "user",   "content": f"The user attached an image and asked: {query or 'Describe this image.'}. Vision analysis is unavailable. Provide helpful guidance based on the question alone."},
            ],
            model=OLLAMA_MODEL,
            temperature=0.1,
            max_tokens=400,
        )
        result = make_tool_result(
            tool_name="vision_tool",
            content=fallback_text or "Vision analysis unavailable — no image model configured.",
            source="ollama-text-fallback",
            confidence=0.3,
            metadata={"mode": mode, "vision_unavailable": True},
        )

    elapsed = (time.monotonic() - start) * 1000
    return {
        "tool_results": state.get("tool_results", []) + [result],
        "latency_ms":   {"vision_analyzer": round(elapsed, 2)},
    }