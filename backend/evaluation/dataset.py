# backend/evaluation/dataset.py
"""
Eval dataset loader and sample builder.
Loads from eval_dataset.json + allows programmatic sample addition.

FIXED: Added support for train/val/test splits to prevent overfitting.
"""
import json
import logging
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum

logger = logging.getLogger(__name__)

# FIXED: Added split enum for dataset stratification
class DatasetSplit(str, Enum):
    TRAIN = "train"
    VAL = "val"
    TEST = "test"

DATA_DIR  = Path(__file__).parent / "data"
DATASET_PATH  = DATA_DIR / "eval_dataset.json"
BASELINE_PATH = DATA_DIR / "baseline_scores.json"


@dataclass
class EvalSample:
    id:                  str
    query:               str
    agent_type:          str
    expected_topics:     list[str]
    expected_tools:      list[str]
    difficulty:          str           = "medium"
    split:               str           = DatasetSplit.TEST  # FIXED: Add split indicator
    requires_citation:   bool          = False
    requires_executable: bool          = False
    requires_graph:      bool          = False
    is_safety_query:     bool          = False
    metadata:            dict          = field(default_factory=dict)


def load_eval_dataset(
    agent_type: Optional[str] = None,
    difficulty: Optional[str] = None,
    limit:      Optional[int] = None,
) -> list[EvalSample]:
    """
    Load eval dataset from JSON.
    Filter by agent_type and/or difficulty if specified.
    
    # FIXED: Added validation and error handling for malformed records
    """
    if not DATASET_PATH.exists():
        logger.error(f"Eval dataset not found: {DATASET_PATH}")
        return []

    with open(DATASET_PATH) as f:
        raw = json.load(f)

    samples = []
    invalid_count = 0
    
    for i, item in enumerate(raw):
        try:
            # FIXED: Validate required fields
            required_fields = ["id", "query", "agent_type", "expected_topics", "expected_tools"]
            if not all(field in item for field in required_fields):
                missing = [f for f in required_fields if f not in item]
                logger.warning(f"Sample {i} missing fields: {missing}. Skipping.")
                invalid_count += 1
                continue
            
            # FIXED: Validate field types
            if not isinstance(item.get("expected_topics"), list):
                logger.warning(f"Sample {i}: expected_topics must be list. Skipping.")
                invalid_count += 1
                continue
            if not isinstance(item.get("expected_tools"), list):
                logger.warning(f"Sample {i}: expected_tools must be list. Skipping.")
                invalid_count += 1
                continue
            
            sample = EvalSample(**item)
            samples.append(sample)
        except Exception as e:
            logger.warning(f"Failed to parse sample {i}: {e}")
            invalid_count += 1
            continue

    if invalid_count > 0:
        logger.info(f"Loaded {len(samples)} eval samples ({invalid_count} invalid records skipped)")
    else:
        logger.info(f"Loaded {len(samples)} eval samples")

    if agent_type:
        samples = [s for s in samples if s.agent_type == agent_type or agent_type == "all"]
    if difficulty:
        samples = [s for s in samples if s.difficulty == difficulty]
    if limit:
        samples = samples[:limit]

    return samples


def load_eval_dataset_by_split(
    split:      DatasetSplit | str,
    agent_type: Optional[str] = None,
    difficulty: Optional[str] = None,
    limit:      Optional[int] = None,
) -> list[EvalSample]:
    """
    # FIXED: Load only specified split to prevent overfitting.
    Load eval dataset from JSON filtered by split (train/val/test).
    Prevents model from seeing validation data during training.
    """
    if isinstance(split, str):
        split = DatasetSplit(split)
    
    samples = load_eval_dataset(agent_type=agent_type, difficulty=difficulty)
    
    # Filter by split
    samples = [s for s in samples if s.split == split.value]
    
    if limit:
        samples = samples[:limit]
    
    logger.info(f"Loaded {len(samples)} eval samples for split: {split.value}")
    return samples


def save_baseline(scores: dict):
    """Save current scores as the new baseline for regression detection."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(BASELINE_PATH, "w") as f:
        json.dump(scores, f, indent=2)
    logger.info(f"Baseline saved: {BASELINE_PATH}")


def load_baseline() -> dict:
    """Load baseline scores for regression comparison."""
    if not BASELINE_PATH.exists():
        return {}
    with open(BASELINE_PATH) as f:
        return json.load(f)