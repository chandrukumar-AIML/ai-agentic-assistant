# backend/agents/vision_agent.py
"""
Vision Agent: GPT-4o Vision — OCR, chart analysis, diagram understanding.
Best for: image analysis, chart data extraction, screenshot reading.
"""
import time
import logging
from typing import Any

from backend.agent.base_agent        import BaseWorkerAgent, WorkerResult
from backend.llm.vision_preprocessor  import encode_from_base64, ImageProcessingError
from backend.config                   import get_settings
from backend.llm.ollama_openai        import ollama_chat_completion, OLLAMA_MODEL

logger   = logging.getLogger(__name__)
settings = get_settings()


def _get_vision_client():
    """Lazy OpenAI vision client — only if valid API key available."""
    try:
        from openai import AsyncOpenAI
        key = settings.openai_api_key
        if key and key.startswith("sk-"):
            return AsyncOpenAI(api_key=key)
    except Exception:
        pass
    return None

VISION_MODES = {
    "ocr":     "Extract ALL text verbatim. Preserve structure and formatting.",
    "chart":   "Analyse: chart type, axes, all data values, trends, key insight.",
    "diagram": "Analyse: diagram type, components, connections, labels, process flow.",
    "code":    "Extract code as plain text, preserving indentation. Note language and errors.",
    "general": "Analyse in detail, focusing on what is relevant to the user's question.",
}


class VisionAgent(BaseWorkerAgent):
    name        = "vision_agent"
    description = (
        "Expert at understanding images, screenshots, charts, diagrams, "
        "and documents. Uses GPT-4o Vision. Best for: image analysis, "
        "OCR, chart data extraction, diagram interpretation."
    )

    @property
    def system_prompt(self) -> str:
        return """You are a Vision Analysis Specialist Agent.

Your capabilities:
- OCR: extract text from images with perfect accuracy
- Chart/graph analysis: read data values, identify trends
- Diagram interpretation: understand architecture, flowcharts, UML
- Screenshot analysis: identify UI elements, error messages, code
- Document scanning: extract structured data from forms, tables

Rules:
- Be precise with numbers — read them directly, do not estimate
- If text is present, extract it verbatim
- Describe what you see, not what you assume
- For charts: always include axis labels and data values"""

    def _detect_mode(self, query: str) -> str:
        q = query.lower()
        if any(w in q for w in ["text", "read", "ocr", "extract text", "written"]):
            return "ocr"
        if any(w in q for w in ["chart", "graph", "plot", "trend", "data", "values"]):
            return "chart"
        if any(w in q for w in ["diagram", "flow", "architecture", "uml", "schema"]):
            return "diagram"
        if any(w in q for w in ["code", "function", "class", "error", "syntax"]):
            return "code"
        return "general"

    async def run(
        self,
        query:          str,
        context:        dict[str, Any],
        memory_context: str = "",
    ) -> WorkerResult:
        start      = time.monotonic()
        image_data = context.get("image_data")

        if not image_data:
            return WorkerResult(
                worker_name="vision_agent",
                content="No image provided. Please attach an image to use the Vision Agent.",
                confidence=0.0,
                latency_ms=(time.monotonic() - start) * 1000,
                error="no_image",
            )

        # Preprocess image
        try:
            img_meta = encode_from_base64(image_data, query=query)
        except ImageProcessingError as e:
            return WorkerResult(
                worker_name="vision_agent",
                content=f"Image preprocessing failed: {e}",
                confidence=0.0,
                latency_ms=(time.monotonic() - start) * 1000,
                error=str(e),
            )

        mode           = self._detect_mode(query)
        mode_prompt    = VISION_MODES[mode]
        system_content = f"{self.system_prompt}\n\nTask mode: {mode}\n{mode_prompt}"
        if memory_context:
            system_content += f"\n\nUser context:\n{memory_context}"

        messages = [
            {"role": "system", "content": system_content},
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url":    f"data:{img_meta['media_type']};base64,{img_meta['base64_data']}",
                            "detail": img_meta["detail"],
                        },
                    },
                    {"type": "text", "text": query or "Analyse this image."},
                ],
            },
        ]

        vision_client = _get_vision_client()
        try:
            if vision_client is None:
                raise RuntimeError("OpenAI Vision not available")
            response = await vision_client.chat.completions.create(
                model=settings.openai_model,
                messages=messages,
                max_tokens=1500,
                temperature=0.1,
            )
            content       = response.choices[0].message.content
            finish_reason = response.choices[0].finish_reason

            if finish_reason == "length":
                content += "\n\n[Response truncated — image analysis was cut short]"

            vision_confidence = 0.92 if finish_reason != "length" else 0.70

        except Exception as e:
            logger.warning(f"Vision agent GPT-4o call failed, using text fallback: {type(e).__name__}")
            # Ollama text fallback
            content = await ollama_chat_completion(
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user",   "content": f"Image analysis unavailable. The user asked: '{query}'. Provide helpful guidance based on the question alone."},
                ],
                model=OLLAMA_MODEL,
                temperature=0.1,
                max_tokens=300,
            )
            vision_confidence = 0.3

        return WorkerResult(
            worker_name="vision_agent",
            content=content or "Vision analysis temporarily unavailable.",
            confidence=vision_confidence,
            metadata={
                "mode":            mode,
                "detail":          img_meta["detail"],
                "image_size":      f"{img_meta['width']}×{img_meta['height']}",
                "confidence_basis":"heuristic",
            },
            latency_ms=(time.monotonic() - start) * 1000,
        )