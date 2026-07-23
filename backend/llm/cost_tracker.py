"""
LLM cost tracker — logs provider, model, token usage, and cost per call.
Rates are per 1M tokens (input/output). Update when providers change pricing.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger("llm.cost")

# Cost in USD per 1M tokens — (input_per_1m, output_per_1m)
COST_RATES: dict[str, tuple[float, float]] = {
    # Groq
    "llama-3.1-8b-instant":    (0.05,  0.08),
    "llama-3.3-70b-versatile": (0.59,  0.79),
    "mixtral-8x7b-32768":      (0.24,  0.24),
    # Gemini
    "gemini-2.0-flash":        (0.075, 0.30),
    "gemini-1.5-flash":        (0.075, 0.30),
    "gemini-1.5-pro":          (1.25,  5.00),
    # OpenAI
    "gpt-4o":                  (2.50,  10.00),
    "gpt-4o-mini":             (0.15,  0.60),
    "gpt-3.5-turbo":           (0.50,  1.50),
    # Ollama — free (local)
    "llama3.2":                (0.0,   0.0),
    "deepseek-coder":          (0.0,   0.0),
}


@dataclass
class LLMCallRecord:
    provider:      str
    model:         str
    action:        str          = ""
    input_tokens:  int          = 0
    output_tokens: int          = 0
    latency_ms:    float        = 0.0
    cost_usd:      float        = 0.0
    fallback:      bool         = False
    error:         Optional[str] = None


def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    rates = COST_RATES.get(model, (0.0, 0.0))
    return (input_tokens * rates[0] + output_tokens * rates[1]) / 1_000_000


def log_llm_call(record: LLMCallRecord) -> None:
    logger.info(
        "llm_call provider=%s model=%s action=%s input_tokens=%d output_tokens=%d "
        "latency_ms=%.1f cost_usd=%.6f fallback=%s error=%s",
        record.provider, record.model, record.action or "-",
        record.input_tokens, record.output_tokens,
        record.latency_ms, record.cost_usd,
        record.fallback, record.error or "-",
    )
