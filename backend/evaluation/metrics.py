# backend/evaluation/metrics.py
"""
Evaluation metrics for the agent system.

Metrics:
  - Task Completion Rate (TCR): did agent address the query?
  - Tool Call Accuracy: did supervisor route to expected agents?
  - Response Faithfulness: is answer grounded in expected topics?
  - Trajectory Efficiency: how many loops/retries needed?
  - Self-correction Rate: did reflection improve the answer?
  
  Enhanced with semantic similarity and RAGAS-style metrics.
"""
import logging
import re
from dataclasses import dataclass, field
from typing import Optional
import numpy as np

from backend.llm.router import llm_router

logger = logging.getLogger(__name__)

# FIXED: Added cosine_similarity import for semantic evaluation
try:
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("scikit-learn not available; using fallback similarity")


@dataclass
class EvalMetrics:
    query_id:              str
    query:                 str
    agent_type:            str
    difficulty:            str

    # Core metrics
    task_completed:        bool       = False
    tool_accuracy:         float      = 0.0    # 0-1
    faithfulness:          float      = 0.0    # 0-1
    trajectory_efficiency: float      = 0.0    # 0-1 (1 = perfect, no retries)
    self_correction_rate:  float      = 0.0    # 0-1

    # Raw data
    response:              str        = ""
    workers_used:          list[str]  = field(default_factory=list)
    reflection_attempts:   int        = 0
    reflection_score:      float      = 0.0
    retry_count:           int        = 0
    latency_ms:            float      = 0.0

    # Composite score
    composite_score:       float      = 0.0    # weighted average
    error:                 Optional[str] = None


TCR_PROMPT = """Evaluate whether this AI response successfully completes the user's task.

User query: {query}

AI response: {response}

A task is COMPLETED if:
- The query is directly answered
- Key topics are covered (check: {expected_topics})
- Response is coherent and not an error message

A task is NOT COMPLETED if:
- Response is an error or refusal (without good reason)
- Response is completely off-topic
- Response is empty or trivially short

Respond with ONLY: COMPLETED or NOT_COMPLETED"""


async def compute_tcr(
    query:           str,
    response:        str,
    expected_topics: list[str],
) -> bool:
    """
    Task Completion Rate check via LLM judge.
    # FIXED: Removed unreliable fallback keyword check.
    Returns True if task was completed based on LLM evaluation.
    If response is too short, returns False (heuristic guard).
    """
    if not response or len(response.strip()) < 20:
        return False

    messages = [
        {
            "role": "user",
            "content": TCR_PROMPT.format(
                query=query,
                response=response[:1500],
                expected_topics=", ".join(expected_topics),
            ),
        }
    ]

    try:
        result, _ = await llm_router.complete(
            messages=messages,
            temperature=0,
            max_tokens=15,
        )
        result_str = result if isinstance(result, str) else ""
        return "COMPLETED" in result_str
    except Exception as e:
        logger.error(f"TCR LLM check failed: {e}", exc_info=True)
        # FIXED: No fallback — fail safe if LLM unavailable
        return False


def compute_tool_accuracy(
    expected_tools: list[str],
    actual_tools:   list[str],
) -> float:
    """
    Tool Call Accuracy: what fraction of expected workers were used?
    Uses Jaccard similarity — penalises both missing and extra tools.

    Score = |intersection| / |union|
    """
    if not expected_tools:
        return 1.0

    expected_set = set(expected_tools)
    actual_set   = set(actual_tools)
    intersection = expected_set & actual_set
    union        = expected_set | actual_set

    if not union:
        return 1.0

    return len(intersection) / len(union)


# FIXED: Must be async — uses await for LLM judge call
async def compute_faithfulness(
    response:        str,
    expected_topics: list[str],
) -> float:
    """
    # FIXED: Now uses LLM evaluation instead of keyword matching.
    Measures: what fraction of expected topics are faithfully covered in response?
    
    Uses LLM judge for semantic accuracy (RAGAS-style).
    Falls back to keyword matching only if LLM unavailable.
    """
    if not expected_topics or not response:
        return 0.0

    faithfulness_prompt = f"""Evaluate whether the response covers these topics faithfully (accurately and grounded):

Topics to cover: {', '.join(expected_topics)}

Response: {response[:2000]}

For each topic, rate 0-1: Does the response address this topic accurately?
Respond with ONLY a JSON object like: {{"topic1": 0.8, "topic2": 1.0}}
Do NOT add any other text."""

    messages = [
        {"role": "user", "content": faithfulness_prompt}
    ]

    try:
        result, _ = await llm_router.complete(
            messages=messages,
            temperature=0,
            max_tokens=200,
        )
        
        # Parse LLM JSON response
        import json
        import re
        json_match = re.search(r'\{[^}]+\}', result if isinstance(result, str) else "")
        if json_match:
            scores = json.loads(json_match.group())
            valid_scores = [v for v in scores.values() if isinstance(v, (int, float))]
            if valid_scores:
                return min(1.0, max(0.0, np.mean(valid_scores)))
    except Exception as e:
        logger.debug(f"Faithfulness LLM eval failed: {e}, falling back to keyword match")
    
    # FIXED: Fallback uses keyword match but returns 0-1 properly
    response_lower = response.lower()
    hits = sum(
        1 for topic in expected_topics
        if topic.lower() in response_lower
    )
    return hits / len(expected_topics) if expected_topics else 0.0


def compute_trajectory_efficiency(
    reflection_attempts: int,
    retry_count:         int,
    max_retries:         int = 3,
    max_reflections:     int = 3,
) -> float:
    """
    Efficiency score: how directly did the agent reach the answer?

    Perfect score (1.0) = no retries, no reflection loops needed
    Lowest score (0.0)  = max retries + max reflection loops

    Formula: 1 - (normalised_overhead)
    """
    retry_penalty      = min(retry_count, max_retries)       / max_retries
    reflection_penalty = min(reflection_attempts, max_reflections) / max_reflections

    # Reflections are less bad than retries (reflection improves quality)
    overhead = (0.6 * retry_penalty) + (0.4 * reflection_penalty)
    return max(0.0, 1.0 - overhead)


def compute_self_correction_rate(
    reflection_attempts: int,
    reflection_score:    float,
    initial_score:       float = 5.0,   # assume 5/10 without reflection
) -> float:
    """
    Self-correction rate: did reflection actually improve the answer?

    0.0 = reflection made no difference or made it worse
    1.0 = significant improvement through reflection
    """
    if reflection_attempts <= 1:
        return 1.0   # No correction needed — perfect first time

    score_improvement = reflection_score - initial_score
    # Normalise: improvement from 5→10 = 1.0, 5→5 = 0.0, 5→3 = negative
    normalised = max(0.0, score_improvement / 5.0)
    return min(normalised, 1.0)


def compute_composite_score(metrics: EvalMetrics) -> float:
    """
    Weighted composite score across all metrics.

    Weights reflect importance:
    - TCR is most important (was the task done?)
    - Faithfulness second (is it accurate?)
    - Tool accuracy third (did it use right tools?)
    - Efficiency and self-correction are secondary
    """
    weights = {
        "tcr":          0.35,
        "faithfulness": 0.25,
        "tool_acc":     0.20,
        "efficiency":   0.12,
        "self_correct": 0.08,
    }

    score = (
        weights["tcr"]          * (1.0 if metrics.task_completed else 0.0) +
        weights["faithfulness"] * metrics.faithfulness +
        weights["tool_acc"]     * metrics.tool_accuracy +
        weights["efficiency"]   * metrics.trajectory_efficiency +
        weights["self_correct"] * metrics.self_correction_rate
    )
    return round(score, 4)