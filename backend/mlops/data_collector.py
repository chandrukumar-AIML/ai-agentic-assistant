# backend/mlops/data_collector.py
"""
Collects low-quality conversations from production for fine-tuning.

Collection criteria:
  - User gave thumbs down feedback (score < 0.5)
  - Reflection loop count >= 2 (agent struggled)
  - Guardrail did NOT block (real agent failure, not safety issue)
  - Response length >= 100 chars (non-trivial)

Output format: JSONL instruction-tuning format for LoRA.
"""
import json
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)

DATASET_DIR = Path("data/training_data")


async def collect_training_samples(
    workspace_id:  str,
    days_back:     int   = 30,
    min_samples:   int   = 50,
    max_samples:   int   = 2000,
) -> dict:
    """
    Collect conversation samples from production audit logs.

    Two-pass collection:
      Pass 1: Negative examples — thumbs down + high reflection loops
      Pass 2: Positive examples — thumbs up, low reflection, high score

    Returns: {"collected": int, "path": str, "breakdown": dict}
    """
    try:
        from backend.prompts.registry import get_pool
        pool = await get_pool()
        async with pool.acquire() as conn:
            # Pass 1: Negative examples (agent struggled)
            # FIXED: INTERVAL '$2 days' is not substituted by asyncpg — use $2 * INTERVAL '1 day'
            negative_rows = await conn.fetch(
                """
                SELECT
                    a.session_id,
                    a.trace_id,
                    (a.metadata->>'user_query')   AS user_query,
                    (a.metadata->>'final_answer')  AS final_answer,
                    (a.metadata->>'reflection_score')::float AS reflection_score,
                    a.reflection_loops,
                    a.model_used
                FROM audit_log a
                LEFT JOIN ab_query_log ab ON a.trace_id = ab.trace_id
                WHERE a.workspace_id = $1::uuid
                  AND a.action = 'query'
                  AND a.timestamp >= NOW() - $2 * INTERVAL '1 day'
                  AND a.guardrail_triggered = false
                  AND a.error IS NULL
                  AND (
                    a.reflection_loops >= 2
                    OR ab.feedback_score < 0.5
                  )
                  AND length(a.metadata->>'final_answer') >= 100
                ORDER BY a.timestamp DESC
                LIMIT $3
                """,
                workspace_id, days_back, max_samples // 2,
            )

            # Pass 2: Positive examples (agent did well)
            positive_rows = await conn.fetch(
                """
                SELECT
                    a.session_id,
                    a.trace_id,
                    (a.metadata->>'user_query')    AS user_query,
                    (a.metadata->>'final_answer')  AS final_answer,
                    (a.metadata->>'reflection_score')::float AS reflection_score,
                    a.reflection_loops,
                    a.model_used
                FROM audit_log a
                LEFT JOIN ab_query_log ab ON a.trace_id = ab.trace_id
                WHERE a.workspace_id = $1::uuid
                  AND a.action = 'query'
                  AND a.timestamp >= NOW() - $2 * INTERVAL '1 day'
                  AND a.guardrail_triggered = false
                  AND a.error IS NULL
                  AND a.reflection_loops <= 1
                  AND (
                    ab.feedback_score >= 0.8
                    OR (a.metadata->>'reflection_score')::float >= 8.0
                  )
                  AND length(a.metadata->>'final_answer') >= 100
                ORDER BY a.timestamp DESC
                LIMIT $3
                """,
                workspace_id, days_back, max_samples // 2,
            )

    except Exception as e:
        logger.error(f"Data collection failed: {e}")
        return {"collected": 0, "error": str(e)}

    samples  = []
    negative = 0
    positive = 0

    # Format negative examples for instruction tuning
    for row in negative_rows:
        query  = row.get("user_query")  or ""
        answer = row.get("final_answer") or ""
        if not query or not answer:
            continue

        # For negative examples: we include them so the model learns
        # what queries look like — paired with IMPROVED responses.
        # In practice, you'd want a human reviewer to improve these.
        # We flag them for review.
        samples.append({
            "type":       "negative",
            "trace_id":   row.get("trace_id", ""),
            "messages": [
                {"role": "system",    "content": "You are a precise AI assistant."},
                {"role": "user",      "content": query},
                {"role": "assistant", "content": answer},
            ],
            "reflection_loops": row.get("reflection_loops", 0),
            "reflection_score": row.get("reflection_score", 0),
            "needs_review":     True,
        })
        negative += 1

    # Format positive examples
    for row in positive_rows:
        query  = row.get("user_query")  or ""
        answer = row.get("final_answer") or ""
        if not query or not answer:
            continue
        samples.append({
            "type":       "positive",
            "trace_id":   row.get("trace_id", ""),
            "messages": [
                {"role": "system",    "content": "You are a precise AI assistant."},
                {"role": "user",      "content": query},
                {"role": "assistant", "content": answer},
            ],
            "reflection_loops": row.get("reflection_loops", 0),
            "reflection_score": row.get("reflection_score", 5.0),
            "needs_review":     False,
        })
        positive += 1

    if len(samples) < min_samples:
        logger.warning(
            f"Insufficient training data: {len(samples)} samples "
            f"(minimum {min_samples}). Need more production traffic."
        )

    # Save JSONL dataset
    DATASET_DIR.mkdir(parents=True, exist_ok=True)
    ts   = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M")  # FIXED: use timezone-aware datetime
    path = DATASET_DIR / f"training_{workspace_id[:8]}_{ts}.jsonl"

    with open(path, "w") as f:
        for sample in samples:
            f.write(json.dumps(sample) + "\n")

    logger.info(
        f"Training data collected: {len(samples)} samples "
        f"({positive} positive, {negative} negative) → {path}"
    )

    return {
        "collected":  len(samples),
        "positive":   positive,
        "negative":   negative,
        "path":       str(path),
        "breakdown":  {"positive": positive, "negative": negative},
    }


async def export_for_huggingface(
    jsonl_path: str,
    output_dir: str = "data/hf_dataset",
) -> dict:
    """
    Convert JSONL dataset to HuggingFace datasets format.
    Used by the Colab fine-tuning notebook.
    """
    import csv

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    samples = []
    with open(jsonl_path) as f:
        for line in f:
            samples.append(json.loads(line))

    # Only use positive examples for fine-tuning
    # (negative ones need human review first)
    positive = [s for s in samples if s["type"] == "positive"]

    # Format as Alpaca-style instruction tuning
    alpaca_data = []
    for s in positive:
        msgs    = s["messages"]
        user    = next((m["content"] for m in msgs if m["role"] == "user"),    "")
        asst    = next((m["content"] for m in msgs if m["role"] == "assistant"), "")
        system  = next((m["content"] for m in msgs if m["role"] == "system"),  "")
        alpaca_data.append({
            "instruction": system,
            "input":       user,
            "output":      asst,
        })

    # FIXED: 80/20 train/val split to prevent overfitting
    import random
    random.shuffle(alpaca_data)
    split_idx  = max(1, int(len(alpaca_data) * 0.8))
    train_data = alpaca_data[:split_idx]
    val_data   = alpaca_data[split_idx:]

    train_file = output_path / "train.json"
    val_file   = output_path / "val.json"
    train_file.write_text(json.dumps(train_data, indent=2))
    val_file.write_text(json.dumps(val_data,   indent=2))

    logger.info(f"Exported {len(train_data)} train + {len(val_data)} val samples")
    return {
        "exported":   len(alpaca_data),
        "train":      len(train_data),
        "val":        len(val_data),
        "train_path": str(train_file),
        "val_path":   str(val_file),
        "format":     "alpaca",
    }