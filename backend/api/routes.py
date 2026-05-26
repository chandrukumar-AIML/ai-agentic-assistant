import os
import json  # FIXED: added missing json import (required by /vertical/{vertical_name} handler)
import tempfile
import logging
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, Request
from fastapi.responses import JSONResponse

from backend.api.auth    import verify_token, limiter, create_access_token  # FIXED: from api.auth → from backend.api.auth
from backend.api.schema import (  # FIXED: from api.schema → from backend.api.schema
    HealthResponse, IngestResponse, HistoryResponse, MessageRecord,
    RAGStatsResponse, FeedbackRequest, FeedbackResponse, IngestURLRequest,
)
from backend.config import get_settings  # FIXED: from config → from backend.config
from backend.utils.upload import read_upload_limited  # FIXED: from utils.upload → from backend.utils.upload

# All imports at module level — not inside handlers
from backend.rag.ingestor              import ingest  # FIXED: missing backend. prefix
from backend.rag.faiss_store           import get_index_size  # FIXED: missing backend. prefix
from backend.rag.chroma_store          import get_count  # FIXED: missing backend. prefix
from backend.session.redis_client      import get_session, delete_session  # FIXED: missing backend. prefix
from backend.llm.router                import llm_router  # FIXED: missing backend. prefix
from backend.graph_db.neo4j_client     import health_check as neo4j_health  # FIXED: missing backend. prefix
from backend.observability.langsmith_tracer import submit_feedback as ls_feedback, get_project_stats  # FIXED: missing backend. prefix
from backend.observability.mlflow_logger    import compare_runs, get_best_run  # FIXED: missing backend. prefix
from backend.agent.tools.vision_tool        import vision_analyzer_node  # FIXED: missing backend. prefix
from backend.llm.vision_preprocessor        import validate_and_encode, ImageProcessingError  # FIXED: missing backend. prefix
from backend.auth.models                    import PlanTier  # FIXED: added missing PlanTier import (required by /cost/budget)

logger   = logging.getLogger(__name__)
settings = get_settings()
router   = APIRouter()

_50MB = 50 * 1024 * 1024
_20MB = 20 * 1024 * 1024


@router.get("/health", response_model=HealthResponse)
async def health_check():
    from backend.session.redis_client import get_redis  # FIXED: missing backend. prefix
    llm_status = await llm_router.health()
    neo4j_ok   = await neo4j_health()
    try:
        r = await get_redis()
        redis_ok = bool(await r.ping())
    except Exception:
        redis_ok = False

    return HealthResponse(
        status="ok",
        openai_healthy=llm_status["openai_healthy"],
        ollama_healthy=llm_status["ollama_healthy"],
        neo4j_healthy=neo4j_ok,
        redis_healthy=redis_ok,
        circuit_state=llm_status["circuit"]["state"],
    )


@router.post("/auth/token")
async def get_token(username: str, password: str):
    """
    Demo token endpoint — DISABLED in production.
    In production, use your OAuth provider.
    """
    if settings.app_env == "production":
        raise HTTPException(501, "Token endpoint disabled in production. Use your OAuth provider.")
    if not username or not password:
        raise HTTPException(400, "Username and password required")
    from backend.api.auth import UserRole, PlanTier
    token_resp = create_access_token(
        user_id=username,
        email=f"{username}@agentic.local",
        workspace_id="ws-default",
        workspace_slug="default",
        role=UserRole.ADMIN,
        plan_tier=PlanTier.ENTERPRISE,
    )
    return {"access_token": token_resp.access_token, "token_type": "bearer"}


@router.post("/ingest", response_model=IngestResponse)
@limiter.limit("10/minute")
async def ingest_file(
    request:  Request,
    file:     UploadFile = File(...),
    category: str        = Form(default="general"),
    _token:   dict       = Depends(verify_token),
):
    suffix = Path(file.filename or "upload.txt").suffix.lower()
    if suffix not in {".pdf", ".txt", ".md"}:
        raise HTTPException(400, f"Unsupported format '{suffix}'. Use .pdf, .txt, or .md")

    # Chunked read with 50MB limit — prevents DoS via unbounded file.read()
    content = await read_upload_limited(file, max_bytes=_50MB)
    source_type = "pdf" if suffix == ".pdf" else "txt"

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        result = await ingest(
            source=tmp_path,
            source_type=source_type,
            category=category,
            extra_meta={"original_filename": file.filename},
        )
    finally:
        os.unlink(tmp_path)

    if result["chunks_indexed"] == 0:
        raise HTTPException(422, "No content could be extracted from file")

    logger.info(f"Ingested {file.filename}: {result['chunks_indexed']} chunks")
    return IngestResponse(
        status="ok",
        chunks_indexed=result["chunks_indexed"],
        filename=file.filename or "",
        category=category,
    )


@router.post("/ingest/url")
@limiter.limit("20/minute")
async def ingest_url(
    request: Request,
    body:    IngestURLRequest,
    _token:  dict = Depends(verify_token),
):
    try:
        result = await ingest(source=body.url, source_type="url", category=body.category)
    except Exception as e:
        logger.error(f"URL ingestion failed for {body.url!r}: {e}", exc_info=True)  # FIXED: log internally
        raise HTTPException(422, "URL ingestion failed — check the URL and try again")  # FIXED: str(e) → generic message (prevents leaking internals)
    return IngestResponse(
        status="ok", chunks_indexed=result["chunks_indexed"],
        filename=body.url, category=body.category,
    )


@router.get("/history/{session_id}", response_model=HistoryResponse)
async def get_history(session_id: str, _token: dict = Depends(verify_token)):
    data = await get_session(session_id)
    if not data:
        return HistoryResponse(session_id=session_id, messages=[], count=0)
    messages = [
        MessageRecord(role=m.get("role", ""), content=m.get("content", ""))
        if isinstance(m, dict)
        else MessageRecord(role=m.__class__.__name__.replace("Message","").lower(), content=m.content)
        for m in data.get("messages", [])
    ]
    return HistoryResponse(session_id=session_id, messages=messages, count=len(messages))


@router.delete("/history/{session_id}")
async def clear_history(session_id: str, _token: dict = Depends(verify_token)):
    await delete_session(session_id)
    return {"status": "cleared", "session_id": session_id}


@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(body: FeedbackRequest, _token: dict = Depends(verify_token)):
    """Submit user feedback — routes to LangSmith, A/B tracker, and prompt performance tracker."""
    # FIXED: merged A/B attribution and prompt tracking into canonical definition (duplicate removed)
    ok = await ls_feedback(run_id=body.run_id, score=body.score, comment=body.comment)

    if getattr(body, "ab_log_entry_id", None):
        from backend.prompts.ab_router import record_ab_feedback
        completed_test = await record_ab_feedback(
            log_entry_id=body.ab_log_entry_id,
            score=body.score,
        )
        if completed_test:
            logger.info(f"A/B test auto-promoted: {completed_test}")

    if getattr(body, "prompt_version_id", None):
        from backend.prompts.registry import record_prompt_feedback
        await record_prompt_feedback(
            prompt_id=body.prompt_version_id,
            score=body.score,
        )

    return FeedbackResponse(submitted=ok, run_id=body.run_id)


@router.get("/rag/stats", response_model=RAGStatsResponse)
async def rag_stats(_token: dict = Depends(verify_token)):
    return RAGStatsResponse(faiss_vectors=get_index_size(), chroma_documents=get_count())


@router.get("/llm/health")
async def llm_health():
    return await llm_router.health()


@router.post("/llm/reset-circuit")
async def reset_circuit(_token: dict = Depends(verify_token)):
    llm_router.reset()
    return {"status": "reset"}


@router.get("/mlflow/compare")
async def mlflow_compare(
    experiment: str  = "rag_experiments",
    metric:     str  = "avg_score",
    n:          int  = 5,
    _token:     dict = Depends(verify_token),
):
    return {"experiment": experiment, "metric": metric, "runs": compare_runs(experiment, metric, n)}


@router.get("/mlflow/best")
async def mlflow_best(
    experiment:       str  = "rag_experiments",
    metric:           str  = "avg_score",
    higher_is_better: bool = True,
    _token:           dict = Depends(verify_token),
):
    return get_best_run(experiment, metric, higher_is_better) or {"message": "No runs found"}


@router.get("/tracing/stats")
async def tracing_stats(days: int = 7, _token: dict = Depends(verify_token)):
    return await get_project_stats(days=days)


@router.post("/vision/analyse")
@limiter.limit("30/minute")
async def analyse_image(
    request: Request,
    file:    UploadFile = File(...),
    query:   str        = Form(default="Describe this image."),
    _token:  dict       = Depends(verify_token),
):
    ALLOWED = {"image/jpeg", "image/png", "image/gif", "image/webp"}
    if file.content_type not in ALLOWED:
        raise HTTPException(400, f"Unsupported type: {file.content_type}")

    # Chunked read with 20MB limit
    image_bytes = await read_upload_limited(file, max_bytes=_20MB)

    try:
        img_meta = validate_and_encode(image_bytes, query=query)
    except ImageProcessingError as e:
        raise HTTPException(400, str(e))

    state = {
        "user_query":   query,
        "image_data":   img_meta["base64_data"],
        "tool_results": [],
        "latency_ms":   {},
    }
    result = await vision_analyzer_node(state)
    tr = result["tool_results"][0]

    return {
        "analysis":     tr["content"],
        "mode":         tr["metadata"].get("mode"),
        "detail":       tr["metadata"].get("detail"),
        "total_tokens": tr["metadata"].get("total_tokens"),
        "latency_ms":   result["latency_ms"].get("vision_analyzer"),
    }

@router.post("/eval/run")
async def run_eval(
    agent_type:       str | None = None,
    difficulty:       str | None = None,
    limit:            int | None = 10,
    save_as_baseline: bool       = False,
    _token:           dict       = Depends(verify_token),
):
    """
    Trigger evaluation run via API.
    Default: 10 samples (full 100 for CI/CD).
    """
    from backend.evaluation.eval_runner import run_evaluation
    report = await run_evaluation(
        agent_type=agent_type,
        difficulty=difficulty,
        limit=limit,
        save_as_baseline=save_as_baseline,
    )
    return report


@router.get("/eval/baseline")
async def get_baseline(_token: dict = Depends(verify_token)):
    """Return the current baseline scores."""
    from backend.evaluation.dataset import load_baseline
    baseline = load_baseline()
    return {"baseline": baseline, "exists": bool(baseline)}


@router.post("/eval/set-baseline")
async def set_baseline(_token: dict = Depends(verify_token)):
    """Run eval and save results as new baseline."""
    from backend.evaluation.eval_runner import run_evaluation
    report = await run_evaluation(limit=20, save_as_baseline=True)
    return {
        "saved":   True,
        "metrics": report.get("metrics", {}),
        "gate":    report.get("gate", {}),
    }


@router.get("/eval/report")
async def get_latest_report(_token: dict = Depends(verify_token)):
    """Return latest eval report if exists."""
    from pathlib import Path
    reports_dir = Path("data/eval_reports")
    if not reports_dir.exists():
        return {"report": None, "message": "No reports generated yet"}

    reports = sorted(reports_dir.glob("eval_report_*.md"), reverse=True)
    if not reports:
        return {"report": None}

    return {
        "report":   reports[0].read_text(),
        "filename": reports[0].name,
        "count":    len(reports),
    } 


# Add to backend/api/routes.py:

# ── Prompt Registry Endpoints ────────────────────────────────────────────────

@router.get("/prompts")
async def list_prompts(_token: dict = Depends(verify_token)):
    """List all prompts and their versions."""
    from backend.prompts.registry import list_all_prompts
    prompts = await list_all_prompts()
    return {
        name: [
            {
                "id":                pv.id,
                "version":           pv.version,
                "is_active":         pv.is_active,
                "performance_score": pv.performance_score,
                "query_count":       pv.query_count,
                "thumbs_up":         pv.thumbs_up,
                "thumbs_down":       pv.thumbs_down,
                "description":       pv.description,
                "created_at":        pv.created_at.isoformat(),
                "created_by":        pv.created_by,
                "content_preview":   pv.content[:200] + "..." if len(pv.content) > 200 else pv.content,
            }
            for pv in versions
        ]
        for name, versions in prompts.items()
    }


@router.post("/prompts/{prompt_name}")
async def create_prompt_version(
    prompt_name:  str,
    content:      str,
    version:      str,
    description:  str  = "",
    set_active:   bool = False,
    _token:       dict = Depends(verify_token),
):
    """Create a new prompt version."""
    from backend.prompts.registry import create_prompt
    pv = await create_prompt(
        prompt_name=prompt_name,
        version=version,
        content=content,
        description=description,
        set_active=set_active,
        created_by=_token.get("sub", "api_user"),
    )
    return {"created": True, "id": pv.id, "version": pv.version}


@router.post("/prompts/{prompt_name}/activate/{prompt_id}")
async def activate_prompt_version(
    prompt_name: str,
    prompt_id:   int,
    _token:      dict = Depends(verify_token),
):
    """Activate a specific prompt version (instant rollback)."""
    from backend.prompts.registry import set_active_version
    ok = await set_active_version(prompt_id=prompt_id, prompt_name=prompt_name)
    if not ok:
        raise HTTPException(404, "Prompt version not found")
    return {"activated": True, "prompt_id": prompt_id}


@router.delete("/prompts/version/{prompt_id}")
async def delete_prompt_version_endpoint(
    prompt_id: int,
    _token:    dict = Depends(verify_token),
):
    """Delete a non-active prompt version."""
    from backend.prompts.registry import delete_prompt_version
    try:
        ok = await delete_prompt_version(prompt_id)
        if not ok:
            raise HTTPException(404, "Version not found")
        return {"deleted": True}
    except ValueError as e:
        logger.warning(f"Cannot delete prompt version {prompt_id}: {e}")  # FIXED: log internally
        raise HTTPException(400, "Cannot delete an active prompt version")  # FIXED: str(e) → generic message (prevents leaking internals)


# ── A/B Test Endpoints ───────────────────────────────────────────────────────

@router.post("/prompts/ab-test")
async def create_ab_test_endpoint(
    test_name:     str,
    prompt_name:   str,
    variant_a_id:  int,
    variant_b_id:  int,
    min_queries:   int   = 100,
    auto_promote:  bool  = True,
    _token:        dict  = Depends(verify_token),
):
    """Start an A/B test between two prompt versions."""
    from backend.prompts.ab_router import create_ab_test
    test = await create_ab_test(
        test_name=test_name,
        prompt_name=prompt_name,
        variant_a_id=variant_a_id,
        variant_b_id=variant_b_id,
        min_queries=min_queries,
        auto_promote=auto_promote,
    )
    return {"created": True, "test_id": test.id, "test_name": test.test_name}


@router.get("/prompts/ab-test/{test_id}")
async def get_ab_test_stats_endpoint(
    test_id: int,
    _token:  dict = Depends(verify_token),
):
    """Get live A/B test statistics."""
    from backend.prompts.ab_router import get_ab_test_stats
    stats = await get_ab_test_stats(test_id)
    if not stats:
        raise HTTPException(404, "Test not found")
    return stats


@router.get("/prompts/ab-tests")
async def list_ab_tests_endpoint(
    status: str | None = None,
    _token: dict       = Depends(verify_token),
):
    """List all A/B tests."""
    from backend.prompts.ab_router import list_ab_tests
    return {"tests": await list_ab_tests(status=status)}


@router.post("/prompts/ab-test/{test_id}/pause")
async def pause_ab_test(test_id: int, _token: dict = Depends(verify_token)):
    """Pause a running A/B test."""
    from backend.prompts.registry import get_pool  # FIXED: get_pool was used but never imported at module level
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE ab_tests SET status = 'paused' WHERE id = $1", test_id
        )
    return {"paused": True, "test_id": test_id}


@router.post("/prompts/seed")
async def seed_prompts(_token: dict = Depends(verify_token)):
    """Seed DB with default prompts from code. Run once after Phase G deploy."""
    from backend.prompts.prompt_loader import seed_default_prompts
    await seed_default_prompts()
    return {"seeded": True} 

# FIXED: removed duplicate submit_feedback function definition that shadowed the canonical one above.
# A/B attribution and prompt tracking have been merged into the canonical submit_feedback below.

# Add to backend/api/routes.py:

@router.get("/cost/report")
async def get_cost_report(
    days:    int  = 30,
    token:   dict = Depends(verify_token),
):
    """Workspace cost breakdown by model and day."""
    from backend.cost.tracker import get_workspace_cost_report
    workspace_id = token.get("workspace_id", "")
    if not workspace_id:
        raise HTTPException(400, "workspace_id required")
    return await get_workspace_cost_report(workspace_id=workspace_id, days=days)


@router.get("/cost/budget")
async def get_budget_status(token: dict = Depends(verify_token)):
    """Current workspace budget status + alert state."""
    from backend.cost.budget import check_budget, get_budget_alerts
    workspace_id = token.get("workspace_id", "")
    plan_tier    = PlanTier(token.get("plan_tier", "free"))
    if not workspace_id:
        raise HTTPException(400, "workspace_id required")

    status = await check_budget(workspace_id, plan_tier)
    alerts = await get_budget_alerts(workspace_id)

    return {
        "workspace_id":    status.workspace_id,
        "plan_tier":       status.plan_tier,
        "monthly_budget":  status.monthly_budget,
        "monthly_spend":   status.monthly_spend,
        "remaining":       status.remaining,
        "pct_used":        status.pct_used,
        "alert_triggered": status.alert_triggered,
        "hard_limit_hit":  status.hard_limit_hit,
        "active_alert":    alerts,
    }


@router.get("/cost/cache-stats")
async def get_cache_stats(token: dict = Depends(verify_token)):
    """Redis cache performance stats."""
    from backend.cost.cache import get_cache_stats
    return get_cache_stats()


@router.delete("/cost/cache")
async def clear_cache(token: dict = Depends(verify_token)):
    """Clear the LLM response cache."""
    from backend.cost.cache import invalidate_cache
    deleted = await invalidate_cache()
    return {"cleared": True, "entries_deleted": deleted}


@router.post("/cost/classify")
async def classify_query_complexity(
    query:     str,
    has_image: bool = False,
    token:     dict = Depends(verify_token),
):
    """Preview how a query would be classified for model routing."""
    from backend.cost.classifier import classify_query
    result = classify_query(query=query, has_image=has_image)
    return {
        "query":       query[:100],
        "complexity":  result.complexity,
        "model":       result.model,
        "confidence":  result.confidence,
        "reasons":     result.reasons,
    } 


# Add to backend/api/routes.py:

@router.post("/mlops/drift-check")
async def run_drift_check(
    days:        int  = 7,
    _token:      dict = Depends(verify_token),
):
    """Run drift analysis for the current workspace."""
    from backend.mlops.drift_monitor import run_drift_analysis
    workspace_id = _token.get("workspace_id", "")
    if not workspace_id:
        raise HTTPException(400, "workspace_id required")
    report = await run_drift_analysis(workspace_id, window_days=days)
    return {
        "generated_at":  report.generated_at.isoformat(),
        "overall_drift": report.overall_drift,
        "needs_retrain": report.needs_retrain,
        "summary":       report.summary,
        "signals": [
            {
                "metric":    s.metric_name,
                "current":   s.current_value,
                "baseline":  s.baseline_value,
                "psi":       s.drift_score,
                "drifting":  s.is_drifting,
                "direction": s.direction,
                "threshold": s.threshold,
            }
            for s in report.signals
        ],
    }


@router.get("/mlops/drift-report")
async def get_drift_report(_token: dict = Depends(verify_token)):
    """Get latest saved drift report."""
    from backend.mlops.drift_monitor import get_latest_drift_report
    workspace_id = _token.get("workspace_id", "")
    report       = await get_latest_drift_report(workspace_id)
    if not report:
        return {"message": "No drift reports yet — run /mlops/drift-check first"}
    return report


@router.post("/mlops/collect-training-data")
async def collect_training_data(
    days_back:   int = 30,
    _token:      dict = Depends(verify_token),
):
    """Collect production conversations for fine-tuning dataset."""
    from backend.mlops.data_collector import collect_training_samples
    workspace_id = _token.get("workspace_id", "")
    result       = await collect_training_samples(
        workspace_id=workspace_id,
        days_back=days_back,
    )
    return result


@router.post("/mlops/canary/start")
async def start_canary_endpoint(
    model_name:  str,
    traffic_pct: float = 0.10,
    min_queries: int   = 100,
    _token:      dict  = Depends(verify_token),
):
    """Start a canary deployment for a new model."""
    from backend.mlops.canary import start_canary
    config = await start_canary(
        model_name=model_name,
        traffic_pct=traffic_pct,
        min_queries=min_queries,
    )
    return {
        "started":     True,
        "model_name":  config.model_name,
        "traffic_pct": config.traffic_pct,
        "started_at":  config.started_at.isoformat(),
    }


@router.get("/mlops/canary/status")
async def canary_status(_token: dict = Depends(verify_token)):
    """Get current canary deployment status."""
    from backend.mlops.canary import get_canary_status
    status = await get_canary_status()
    return status or {"status": "no_active_canary"}


@router.post("/mlops/canary/rollback")
async def canary_rollback(_token: dict = Depends(verify_token)):
    """Manually roll back the active canary deployment."""
    from backend.mlops.canary import rollback_canary
    ok = await rollback_canary()
    return {"rolled_back": ok}


@router.post("/mlops/weekly-report")
async def weekly_report(_token: dict = Depends(verify_token)):
    """Run full weekly MLOps report."""
    from backend.mlops.report_scheduler import run_weekly_mlops_report
    workspace_id = _token.get("workspace_id", "")
    return await run_weekly_mlops_report(workspace_id)  


# Add to backend/api/routes.py:

from backend.verticals.devops.agent   import DevOpsAgent
from backend.verticals.research.agent import ResearchVerticalAgent
from backend.verticals.analyst.agent  import DataAnalystAgent

_VERTICAL_AGENTS = {
    "devops":    DevOpsAgent(),
    "research":  ResearchVerticalAgent(),
    "analyst":   DataAnalystAgent(),
}


@router.post("/vertical/{vertical_name}")
@limiter.limit("20/minute")
async def run_vertical_agent(
    request:       Request,
    vertical_name: str,
    query:         str,
    context_json:  str        = "{}",
    _token:        dict       = Depends(verify_token),
):
    """
    Run a domain vertical agent directly.
    vertical_name: devops | research | analyst
    """
    if vertical_name not in _VERTICAL_AGENTS:
        raise HTTPException(
            400,
            f"Unknown vertical: '{vertical_name}'. "
            f"Available: {list(_VERTICAL_AGENTS.keys())}"
        )

    try:
        context = json.loads(context_json)
    except json.JSONDecodeError:
        context = {}

    agent  = _VERTICAL_AGENTS[vertical_name]
    result = await agent.run(
        query=query,
        context=context,
        memory_context="",
    )

    return {
        "vertical":   result.vertical,
        "content":    result.content,
        "sources":    result.sources,
        "charts":     result.charts[:3],   # limit to 3 charts per response
        "metadata":   result.metadata,
        "latency_ms": result.latency_ms,
        "error":      result.error,
    }


@router.get("/vertical/list")
async def list_verticals(_token: dict = Depends(verify_token)):
    """List available domain vertical agents."""
    return {
        "verticals": [
            {
                "name":        name,
                "description": agent.description,
            }
            for name, agent in _VERTICAL_AGENTS.items()
        ]
    }