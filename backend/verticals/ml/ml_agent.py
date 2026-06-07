"""
ML Engineer Vertical — AI-powered machine learning workflow assistant.

Actions:
  experiment_design   — Design ML experiments with hypothesis and evaluation plan
  model_eval          — Evaluate model performance from metrics, suggest improvements
  feature_engineering — Suggest features from dataset description
  drift_analysis      — Analyze data/concept drift from metrics
  training_plan       — Generate full model training plan with hyperparameter strategy
  prompt_eval         — Evaluate LLM prompts for a given task
"""
from __future__ import annotations

import logging
import time

from backend.llm.router import llm_router

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a Senior ML Engineer and Applied Scientist with 10+ years of experience
in production machine learning systems. You are expert in: model design, feature engineering,
experiment tracking (MLflow, W&B), hyperparameter optimization (Optuna, Ray Tune), data quality,
model drift, A/B testing, LLM fine-tuning, prompt engineering, and ML system design.
Output is always structured, precise, and production-focused."""


async def _llm(messages: list[dict], max_tokens: int = 600) -> str:
    text, _ = await llm_router.complete(messages=messages, temperature=0.2, max_tokens=max_tokens)
    return text


async def design_experiment(
    problem_statement: str,
    dataset_description: str,
    model_type: str = "classification",
    baseline_metric: float = 0.0,
    language: str = "en",
) -> dict:
    """Design a complete ML experiment with hypothesis and evaluation plan."""
    prompt = f"""Design a complete ML experiment for:

PROBLEM: {problem_statement}
DATASET: {dataset_description}
TASK TYPE: {model_type}
BASELINE METRIC: {baseline_metric or 'Not established'}

Provide:
1. **Experiment Hypothesis** — clear, testable hypothesis
2. **Success Metrics** — primary metric + guard rails (precision, latency, fairness)
3. **Baseline Models** — 2-3 simple baselines to beat first
4. **Proposed Models** — main model candidates with justification
5. **Train/Val/Test Split Strategy** — ratio, stratification, time-based split if needed
6. **Feature Engineering Plan** — top 10 features to engineer
7. **Evaluation Protocol** — cross-validation strategy, statistical significance test
8. **Experiment Tracking** — MLflow experiment structure with logged artifacts
9. **Risk Register** — data leakage, class imbalance, distribution shift
10. **Timeline** — 2-week sprint plan for experiment"""

    start = time.monotonic()
    result = await _llm([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": prompt},
    ], max_tokens=700)
    latency_ms = round((time.monotonic() - start) * 1000)

    return {"action": "experiment_design", "experiment": result, "latency_ms": latency_ms}


async def evaluate_model(
    metrics: dict,
    model_name: str = "model",
    task_type: str = "classification",
    threshold: float = 0.0,
    language: str = "en",
) -> dict:
    """Evaluate model performance from metrics dict and suggest improvements."""
    metrics_text = "\n".join(f"- {k}: {v}" for k, v in metrics.items())
    thresh_text  = f"\nProduction threshold: {threshold}" if threshold else ""

    prompt = f"""Evaluate this {task_type} model's performance and suggest improvements.

Model: {model_name}
Metrics:
{metrics_text}{thresh_text}

Provide:
1. **Performance Assessment** — is this good/acceptable/poor for {task_type}? Industry benchmarks?
2. **Bottleneck Analysis** — where is the model failing? (bias, variance, data quality)
3. **Top 5 Improvement Strategies** — ranked by expected impact
4. **Error Analysis Plan** — how to investigate failures
5. **Feature Importance Investigation** — SHAP/LIME analysis recommendations
6. **Production Readiness** — is it ready to ship? What monitoring to add?
7. **A/B Test Design** — how to safely roll out vs baseline
8. **Code: Sklearn Pipeline Stub** — training pipeline skeleton with preprocessing + model"""

    start = time.monotonic()
    result = await _llm([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": prompt},
    ], max_tokens=700)
    latency_ms = round((time.monotonic() - start) * 1000)

    return {"action": "model_eval", "evaluation": result, "model": model_name, "latency_ms": latency_ms}


async def feature_engineering(
    dataset_description: str,
    target_variable: str,
    existing_features: list[str] = None,
    domain: str = "general",
    language: str = "en",
) -> dict:
    """Suggest engineered features from dataset description."""
    existing = "\n".join(f"- {f}" for f in (existing_features or []))
    existing_section = f"\nExisting features:\n{existing}" if existing else ""

    prompt = f"""Suggest feature engineering for:

Dataset: {dataset_description}
Target: {target_variable}
Domain: {domain}{existing_section}

Provide:
1. **Numerical Features** — 5 transformations (log, binning, polynomial, ratios, rolling stats)
2. **Categorical Features** — encoding strategies (target encoding, frequency, embeddings)
3. **Temporal Features** — if any dates: day-of-week, seasonality, lag, rolling window
4. **Interaction Features** — 5 high-signal feature crosses
5. **Domain-Specific Features** — {domain}-specific engineered features
6. **Feature Selection Strategy** — mutual information, LASSO, RFECV approach
7. **Leakage Risk Flags** — features that might leak target information
8. **Python Code** — pandas feature engineering snippet for top 5 features"""

    start = time.monotonic()
    result = await _llm([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": prompt},
    ], max_tokens=700)
    latency_ms = round((time.monotonic() - start) * 1000)

    return {"action": "feature_engineering", "suggestions": result, "latency_ms": latency_ms}


async def analyze_drift(
    production_metrics: dict,
    baseline_metrics: dict,
    model_name: str = "model",
    days_since_training: int = 0,
    language: str = "en",
) -> dict:
    """Analyze data/model drift and recommend action."""
    prod_text = "\n".join(f"- {k}: {v}" for k, v in production_metrics.items())
    base_text = "\n".join(f"- {k}: {v}" for k, v in baseline_metrics.items())

    prompt = f"""Analyze model drift for: {model_name}
Days since training: {days_since_training or 'unknown'}

PRODUCTION (current):
{prod_text}

BASELINE (training):
{base_text}

Provide:
1. **Drift Severity** (Critical/High/Medium/Low) with justification
2. **Drift Type** — data drift vs concept drift vs both
3. **Root Cause Hypotheses** — ordered by likelihood
4. **PSI / KS Interpretation** — explain statistical drift signals
5. **Immediate Actions** — what to do in next 24 hours
6. **Retraining Strategy** — full retrain vs fine-tune vs feature update
7. **Monitoring Alerts** — thresholds to set for future drift detection
8. **Rollback Decision** — should we roll back? Criteria for the decision"""

    start = time.monotonic()
    result = await _llm([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": prompt},
    ], max_tokens=600)
    latency_ms = round((time.monotonic() - start) * 1000)

    return {"action": "drift_analysis", "analysis": result, "latency_ms": latency_ms}


async def create_training_plan(
    model_architecture: str,
    dataset_size: str,
    compute: str = "GPU single",
    task: str = "classification",
    language: str = "en",
) -> dict:
    """Generate a full model training plan with hyperparameter strategy."""
    prompt = f"""Create a complete ML training plan for:

Architecture: {model_architecture}
Dataset size: {dataset_size}
Compute: {compute}
Task: {task}

Provide:
1. **Data Pipeline** — loading, preprocessing, augmentation strategy
2. **Model Architecture Details** — layer config, activation functions, regularization
3. **Loss Function** — choice and justification for {task}
4. **Optimizer Config** — optimizer, LR schedule, warmup, gradient clipping
5. **Hyperparameter Search Space** — Optuna study config with 10 key HPs
6. **Training Loop** — epochs, batch size, early stopping criteria
7. **Checkpointing Strategy** — what to save, when, where
8. **Experiment Tracking** — MLflow autolog config + custom metrics to log
9. **Compute Estimate** — estimated training time and GPU memory on {compute}
10. **Python Code** — PyTorch Lightning training module skeleton"""

    start = time.monotonic()
    result = await _llm([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": prompt},
    ], max_tokens=700)
    latency_ms = round((time.monotonic() - start) * 1000)

    return {"action": "training_plan", "plan": result, "latency_ms": latency_ms}


async def evaluate_prompt(
    prompt_text: str,
    task_description: str,
    sample_outputs: list[str] = None,
    language: str = "en",
) -> dict:
    """Evaluate an LLM prompt and suggest improvements."""
    outputs_text = "\n".join(f"Output {i+1}: {o[:300]}" for i, o in enumerate(sample_outputs or []))
    outputs_section = f"\nSample outputs from this prompt:\n{outputs_text}" if outputs_text else ""

    prompt = f"""Evaluate this LLM prompt for the given task.

TASK: {task_description}

PROMPT TO EVALUATE:
---
{prompt_text[:2000]}
---{outputs_section}

Provide:
1. **Clarity Score** (1-10) — is the instruction clear and unambiguous?
2. **Specificity Score** (1-10) — does it define output format and constraints?
3. **Failure Modes** — 5 ways this prompt will fail in production
4. **Improved Prompt** — rewritten prompt with all fixes applied
5. **Few-Shot Examples** — 2-3 examples to add for better performance
6. **Chain-of-Thought Enhancement** — add CoT reasoning if appropriate
7. **System vs User split** — how to split between system and user message
8. **A/B Test Plan** — how to evaluate original vs improved prompt"""

    start = time.monotonic()
    result = await _llm([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": prompt},
    ], max_tokens=600)
    latency_ms = round((time.monotonic() - start) * 1000)

    return {"action": "prompt_eval", "evaluation": result, "latency_ms": latency_ms}


async def ml_agent(
    action: str,
    payload: dict,
    language: str = "en",
) -> dict:
    """Main ML agent dispatcher."""
    action = action.lower().strip()

    if action == "experiment_design":
        return await design_experiment(
            problem_statement=payload.get("problem_statement", ""),
            dataset_description=payload.get("dataset_description", ""),
            model_type=payload.get("model_type", "classification"),
            baseline_metric=float(payload.get("baseline_metric", 0)),
            language=language,
        )
    elif action == "model_eval":
        return await evaluate_model(
            metrics=payload.get("metrics", {}),
            model_name=payload.get("model_name", "model"),
            task_type=payload.get("task_type", "classification"),
            threshold=float(payload.get("threshold", 0)),
            language=language,
        )
    elif action == "feature_engineering":
        return await feature_engineering(
            dataset_description=payload.get("dataset_description", ""),
            target_variable=payload.get("target_variable", "target"),
            existing_features=payload.get("existing_features", []),
            domain=payload.get("domain", "general"),
            language=language,
        )
    elif action == "drift_analysis":
        return await analyze_drift(
            production_metrics=payload.get("production_metrics", {}),
            baseline_metrics=payload.get("baseline_metrics", {}),
            model_name=payload.get("model_name", "model"),
            days_since_training=int(payload.get("days_since_training", 0)),
            language=language,
        )
    elif action == "training_plan":
        return await create_training_plan(
            model_architecture=payload.get("model_architecture", ""),
            dataset_size=payload.get("dataset_size", ""),
            compute=payload.get("compute", "GPU single"),
            task=payload.get("task", "classification"),
            language=language,
        )
    elif action == "prompt_eval":
        return await evaluate_prompt(
            prompt_text=payload.get("prompt_text", ""),
            task_description=payload.get("task_description", ""),
            sample_outputs=payload.get("sample_outputs", []),
            language=language,
        )
    else:
        return {
            "error": f"Unknown action '{action}'. Valid: experiment_design, model_eval, feature_engineering, drift_analysis, training_plan, prompt_eval"
        }
