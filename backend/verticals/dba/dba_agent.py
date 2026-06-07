"""
DBA (Database Administrator) Vertical — AI-powered database management assistant.

Actions:
  optimize_query    — Analyze and optimize slow SQL queries
  design_schema     — Design normalized database schema from requirements
  index_recommend   — Recommend indexes for a given query workload
  migration_script  — Generate safe DB migration scripts
  health_analysis   — Analyze database health metrics and recommend fixes
  query_explain     — Explain an EXPLAIN plan in plain English
"""
from __future__ import annotations

import logging
import time

from backend.llm.router import llm_router

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a Senior Database Administrator with 15+ years of experience in
PostgreSQL, MySQL, and MongoDB at scale. You are expert in: query optimization, index design,
schema normalization, partitioning, replication, backup strategies, migration safety, ACID guarantees,
and database performance tuning. You think in terms of: execution plans, I/O cost, lock contention,
connection pooling, and production safety. Output is always structured, precise, and actionable."""


async def _llm(messages: list[dict], max_tokens: int = 600) -> str:
    text, _ = await llm_router.complete(messages=messages, temperature=0.1, max_tokens=max_tokens)
    return text


async def optimize_query(
    sql: str,
    explain_output: str = "",
    db_type: str = "postgresql",
    table_sizes: dict = None,
    language: str = "en",
) -> dict:
    """Analyze and optimize a slow SQL query."""
    explain_section = f"\n\nEXPLAIN ANALYZE output:\n{explain_output[:3000]}" if explain_output else ""
    sizes_text = "\n".join(f"- {t}: {s}" for t, s in (table_sizes or {}).items())
    sizes_section = f"\n\nTable sizes:\n{sizes_text}" if sizes_text else ""

    prompt = f"""Optimize this slow {db_type} query.

ORIGINAL QUERY:
```sql
{sql[:3000]}
```{explain_section}{sizes_section}

Provide:
1. **Problem Diagnosis** — what is making this query slow (seq scan, join type, sort, etc.)
2. **Optimized Query** — rewritten SQL with explanation of each change
3. **Index Recommendations** — exact CREATE INDEX statements needed
4. **Query Plan Analysis** — interpret the EXPLAIN output if provided
5. **Estimated Improvement** — expected speedup with reasoning
6. **Alternative Approaches** — CTEs, materialized views, denormalization options
7. **Avoid List** — anti-patterns in the original query
8. **Monitoring** — how to track this query's performance in production"""

    start = time.monotonic()
    result = await _llm([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": prompt},
    ], max_tokens=700)
    latency_ms = round((time.monotonic() - start) * 1000)

    return {"action": "optimize_query", "optimization": result, "latency_ms": latency_ms}


async def design_schema(
    requirements: str,
    entities: list[str] = None,
    db_type: str = "postgresql",
    scale: str = "medium",
    language: str = "en",
) -> dict:
    """Design a normalized database schema from business requirements."""
    entities_text = ", ".join(entities) if entities else "inferred from requirements"

    prompt = f"""Design a production-ready {db_type} database schema for:

REQUIREMENTS:
{requirements}

ENTITIES: {entities_text}
SCALE: {scale} (small=<1M rows, medium=1M-100M, large=100M+)

Provide:
1. **Entity Relationship Diagram** — ASCII ERD showing all entities and relationships
2. **Table Definitions** — complete CREATE TABLE SQL for each entity with:
   - Primary keys (UUID vs BIGSERIAL decision with justification)
   - Foreign keys with ON DELETE strategy
   - NOT NULL constraints
   - CHECK constraints
   - Default values
3. **Normalization Analysis** — which normal form achieved and why
4. **Index Strategy** — indexes for all foreign keys + expected query patterns
5. **Partitioning Strategy** — if scale is large
6. **Soft Delete Pattern** — deleted_at vs separate archive table
7. **Audit Columns** — created_at, updated_at, created_by
8. **Migration Script** — Alembic migration file structure"""

    start = time.monotonic()
    result = await _llm([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": prompt},
    ], max_tokens=700)
    latency_ms = round((time.monotonic() - start) * 1000)

    return {"action": "design_schema", "schema": result, "latency_ms": latency_ms}


async def recommend_indexes(
    queries: list[str],
    table_schema: str = "",
    db_type: str = "postgresql",
    language: str = "en",
) -> dict:
    """Recommend optimal indexes for a query workload."""
    queries_text = "\n\n".join(f"Query {i+1}:\n```sql\n{q}\n```" for i, q in enumerate(queries[:10]))
    schema_section = f"\n\nTable Schema:\n{table_schema[:2000]}" if table_schema else ""

    prompt = f"""Recommend indexes for this {db_type} query workload.

QUERIES:
{queries_text}{schema_section}

Provide:
1. **Column Usage Analysis** — which columns appear in WHERE, JOIN, ORDER BY, GROUP BY
2. **Recommended Indexes** — exact CREATE INDEX statements, ordered by priority
   - Specify: B-tree vs GIN vs GiST vs BRIN for each
   - Partial index conditions where appropriate
   - Covering indexes (INCLUDE clause) where beneficial
3. **Composite Index Strategy** — column ordering and selectivity reasoning
4. **Indexes to Avoid** — what NOT to index and why
5. **Index Bloat Risk** — write amplification impact estimate
6. **Monitoring Query** — pg_stat_user_indexes query to track index usage
7. **Maintenance** — VACUUM / ANALYZE / REINDEX schedule
8. **Test Plan** — how to validate index effectiveness"""

    start = time.monotonic()
    result = await _llm([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": prompt},
    ], max_tokens=700)
    latency_ms = round((time.monotonic() - start) * 1000)

    return {"action": "index_recommend", "recommendations": result, "latency_ms": latency_ms}


async def generate_migration(
    change_description: str,
    current_schema: str = "",
    db_type: str = "postgresql",
    language: str = "en",
) -> dict:
    """Generate safe database migration scripts."""
    schema_section = f"\n\nCurrent schema:\n```sql\n{current_schema[:2000]}\n```" if current_schema else ""

    prompt = f"""Generate a safe {db_type} database migration for:

CHANGE: {change_description}{schema_section}

Provide:
1. **Migration Safety Assessment** — is this zero-downtime? What locks are acquired?
2. **Up Migration (SQL)** — complete ALTER/CREATE/DROP statements
3. **Down Migration (SQL)** — complete rollback script
4. **Alembic Migration File** — Python Alembic up() and down() functions
5. **Zero-Downtime Strategy** — if this would cause locks, show expand-contract pattern
6. **Pre-migration Checklist** — backup, test on staging, monitoring setup
7. **Estimated Migration Time** — based on common table sizes
8. **Rollback Decision Tree** — when and how to trigger rollback"""

    start = time.monotonic()
    result = await _llm([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": prompt},
    ], max_tokens=700)
    latency_ms = round((time.monotonic() - start) * 1000)

    return {"action": "migration_script", "migration": result, "latency_ms": latency_ms}


async def analyze_health(
    metrics: dict,
    db_type: str = "postgresql",
    language: str = "en",
) -> dict:
    """Analyze database health metrics and provide recommendations."""
    metrics_text = "\n".join(f"- {k}: {v}" for k, v in metrics.items())

    prompt = f"""Analyze these {db_type} database health metrics.

METRICS:
{metrics_text}

Provide:
1. **Health Score** (1-10) with traffic-light summary (🟢/🟡/🔴 per category)
2. **Critical Issues** — items requiring immediate attention
3. **Performance Issues** — slow queries, connection pressure, cache miss rate
4. **Storage Issues** — bloat, table/index size growth projection
5. **Replication Lag** — if applicable, interpret lag and recommend action
6. **Connection Pool** — pool sizing recommendation based on metrics
7. **Vacuum / Autovacuum** — dead tuple buildup, autovacuum tuning
8. **Immediate Action Plan** — top 5 things to fix this week, in priority order
9. **Monitoring Queries** — PostgreSQL system queries to track each issue"""

    start = time.monotonic()
    result = await _llm([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": prompt},
    ], max_tokens=700)
    latency_ms = round((time.monotonic() - start) * 1000)

    return {"action": "health_analysis", "analysis": result, "latency_ms": latency_ms}


async def explain_query_plan(
    explain_output: str,
    db_type: str = "postgresql",
    language: str = "en",
) -> dict:
    """Translate EXPLAIN ANALYZE output into plain English."""
    prompt = f"""Translate this {db_type} EXPLAIN ANALYZE output into plain English for a developer.

EXPLAIN OUTPUT:
{explain_output[:4000]}

Provide:
1. **Plain English Summary** — what is the database doing, step by step
2. **Bottleneck Identification** — the single most expensive operation and why
3. **Node-by-Node Breakdown** — explain each operation (Seq Scan, Hash Join, Sort, etc.)
4. **Actual vs Estimated Rows** — are row estimates accurate? What if not?
5. **Cost Interpretation** — what do the cost numbers mean in practice?
6. **Buffer Usage** — shared_blks_hit vs read interpretation
7. **Fix Recommendations** — specific changes to improve this plan
8. **Rewritten Query** — if optimization is possible, show it"""

    start = time.monotonic()
    result = await _llm([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": prompt},
    ], max_tokens=600)
    latency_ms = round((time.monotonic() - start) * 1000)

    return {"action": "query_explain", "explanation": result, "latency_ms": latency_ms}


async def dba_agent(
    action: str,
    payload: dict,
    language: str = "en",
) -> dict:
    """Main DBA agent dispatcher."""
    action = action.lower().strip()

    dispatch = {
        "optimize_query":  lambda: optimize_query(
            sql=payload.get("sql", ""),
            explain_output=payload.get("explain_output", ""),
            db_type=payload.get("db_type", "postgresql"),
            table_sizes=payload.get("table_sizes", {}),
            language=language,
        ),
        "design_schema":   lambda: design_schema(
            requirements=payload.get("requirements", ""),
            entities=payload.get("entities", []),
            db_type=payload.get("db_type", "postgresql"),
            scale=payload.get("scale", "medium"),
            language=language,
        ),
        "index_recommend": lambda: recommend_indexes(
            queries=payload.get("queries", []),
            table_schema=payload.get("table_schema", ""),
            db_type=payload.get("db_type", "postgresql"),
            language=language,
        ),
        "migration_script": lambda: generate_migration(
            change_description=payload.get("change_description", ""),
            current_schema=payload.get("current_schema", ""),
            db_type=payload.get("db_type", "postgresql"),
            language=language,
        ),
        "health_analysis": lambda: analyze_health(
            metrics=payload.get("metrics", {}),
            db_type=payload.get("db_type", "postgresql"),
            language=language,
        ),
        "query_explain":   lambda: explain_query_plan(
            explain_output=payload.get("explain_output", ""),
            db_type=payload.get("db_type", "postgresql"),
            language=language,
        ),
    }

    handler = dispatch.get(action)
    if handler:
        return await handler()
    return {
        "error": f"Unknown action '{action}'. Valid: optimize_query, design_schema, index_recommend, migration_script, health_analysis, query_explain"
    }
