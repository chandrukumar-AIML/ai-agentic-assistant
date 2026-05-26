# backend/cost/classifier.py
"""
Query complexity classifier.
Routes queries to the cheapest model that can handle them well.

Complexity levels:
  TRIVIAL  → ollama (free)
  SIMPLE   → gpt-4o-mini (15x cheaper than gpt-4o)
  MEDIUM   → gpt-4o-mini
  COMPLEX  → gpt-4o
  VISION   → gpt-4o (only model with vision)
"""
import re
import logging
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class Complexity(str, Enum):
    TRIVIAL = "trivial"
    SIMPLE  = "simple"
    MEDIUM  = "medium"
    COMPLEX = "complex"
    VISION  = "vision"


# Model assignments per complexity
COMPLEXITY_TO_MODEL: dict[Complexity, str] = {
    Complexity.TRIVIAL: "ollama",
    Complexity.SIMPLE:  "gpt-4o-mini",
    Complexity.MEDIUM:  "gpt-4o-mini",
    Complexity.COMPLEX: "gpt-4o",
    Complexity.VISION:  "gpt-4o",
}

# Pricing per 1K tokens (input, output)
MODEL_PRICING: dict[str, tuple[float, float]] = {
    "gpt-4o":       (0.0025,  0.010),
    "gpt-4o-mini":  (0.00015, 0.0006),
    "ollama":        (0.0,     0.0),
    "ollama/llama3": (0.0,     0.0),
}

@dataclass
class ClassificationResult:
    complexity:     Complexity
    model:          str
    confidence:     float
    reasons:        list[str]


# ── Fast regex signals ───────────────────────────────────────────────────────

_TRIVIAL_PATTERNS = [
    re.compile(r'^(hi|hello|hey|thanks|thank you|ok|okay|yes|no|bye)\s*[!.?]*$', re.I),
    re.compile(r'^what is (?:a |an |the )?\w+\??$', re.I),
    re.compile(r'^define\s+\w+\??$', re.I),
    re.compile(r'^what does \w+ (?:mean|stand for)\??$', re.I),
]

_COMPLEX_SIGNALS = [
    re.compile(r'(compare|contrast|analyse|analyze|evaluate|critique)', re.I),
    re.compile(r'(step[- ]by[- ]step|detailed|comprehensive|in[- ]depth)', re.I),
    re.compile(r'(debug|fix|error|traceback|exception)', re.I),
    re.compile(r'(architecture|design pattern|system design)', re.I),
    re.compile(r'(multiple|several|various).{0,20}(sources?|aspects?|factors?)', re.I),
    re.compile(r'(explain why|explain how|reason for|cause of)', re.I),
]

_CODE_SIGNALS = [
    re.compile(r'(write|generate|create|implement|code|function|class|script)', re.I),
    re.compile(r'```', re.M),
    re.compile(r'(python|javascript|typescript|sql|bash|dockerfile)', re.I),
    re.compile(r'(bug|fix|test|refactor|optimise|optimize)', re.I),
]

_MEDIUM_SIGNALS = [
    re.compile(r'(summarise|summarize|explain|describe|list|what are)', re.I),
    re.compile(r'(how do I|how to|what is the best way)', re.I),
    re.compile(r'(pros and cons|advantages|disadvantages)', re.I),
]


def classify_query(
    query:          str,
    has_image:      bool = False,
    intent:         str  = "",
    tool_count:     int  = 1,
    reflection_on:  bool = True,
) -> ClassificationResult:
    """
    Classify query complexity using fast heuristics.
    No LLM call — pure regex + rule-based.

    Args:
        query:         The user's query text
        has_image:     Whether an image is attached
        intent:        Classified intent from supervisor
        tool_count:    Number of workers being dispatched
        reflection_on: Whether reflection loop is enabled

    Returns:
        ClassificationResult with model recommendation
    """
    reasons = []
    q_len   = len(query.split())

    # Vision always needs gpt-4o
    if has_image:
        return ClassificationResult(
            complexity=Complexity.VISION,
            model="gpt-4o",
            confidence=1.0,
            reasons=["image attached — vision requires gpt-4o"],
        )

    # Trivial: very short, matches simple patterns
    if q_len <= 5:
        for pattern in _TRIVIAL_PATTERNS:
            if pattern.match(query.strip()):
                return ClassificationResult(
                    complexity=Complexity.TRIVIAL,
                    model=COMPLEXITY_TO_MODEL[Complexity.TRIVIAL],
                    confidence=0.95,
                    reasons=["trivial query pattern — ollama sufficient"],
                )

    # Count complexity signals
    complex_hits = sum(1 for p in _COMPLEX_SIGNALS if p.search(query))
    code_hits    = sum(1 for p in _CODE_SIGNALS    if p.search(query))
    medium_hits  = sum(1 for p in _MEDIUM_SIGNALS  if p.search(query))

    # Multi-agent (multiple workers) → complex
    if tool_count >= 3:
        reasons.append(f"{tool_count} workers dispatched")
        complex_hits += 2

    # Long queries tend to be complex
    if q_len > 80:
        reasons.append(f"long query ({q_len} words)")
        complex_hits += 1
    elif q_len > 40:
        medium_hits += 1

    # Reflection requires better model
    if reflection_on and complex_hits >= 1:
        reasons.append("reflection enabled for complex query")
        complex_hits += 1

    # Code tasks benefit from gpt-4o
    if code_hits >= 2:
        reasons.append("code generation task")
        complex_hits += 1

    # Classify
    if complex_hits >= 2:
        complexity = Complexity.COMPLEX
        confidence = min(0.95, 0.70 + complex_hits * 0.05)
        reasons.insert(0, f"{complex_hits} complexity signals found")
    elif medium_hits >= 1 or code_hits >= 1 or q_len > 15:
        complexity = Complexity.MEDIUM
        confidence = 0.80
        reasons.insert(0, "medium complexity signals")
    elif q_len <= 8:
        complexity = Complexity.SIMPLE
        confidence = 0.85
        reasons.insert(0, "short, simple query")
    else:
        complexity = Complexity.MEDIUM
        confidence = 0.75
        reasons.insert(0, "default medium classification")

    model = COMPLEXITY_TO_MODEL[complexity]
    logger.debug(
        f"Query classified: {complexity} → {model} "
        f"(confidence={confidence:.0%}) — {reasons[0] if reasons else ''}"
    )

    return ClassificationResult(
        complexity=complexity,
        model=model,
        confidence=confidence,
        reasons=reasons,
    )


def estimate_cost(
    input_tokens:  int,
    output_tokens: int,
    model:         str,
) -> float:
    """Estimate cost in USD for a given token count and model."""
    pricing = MODEL_PRICING.get(model, MODEL_PRICING["gpt-4o"])
    input_cost  = (input_tokens  / 1000) * pricing[0]
    output_cost = (output_tokens / 1000) * pricing[1]
    return round(input_cost + output_cost, 6)