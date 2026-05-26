# backend/prompts/ab_router.py
"""
A/B test traffic router.
Routes requests 50/50 between two prompt variants.
Auto-promotes winner after min_queries threshold.
"""
import random
import logging
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import Optional

from backend.prompts.registry import (
    get_pool, get_prompt_by_id,
    set_active_version, record_prompt_feedback,
    PromptVersion,
)

logger = logging.getLogger(__name__)


@dataclass
class ABTest:
    id:           int
    test_name:    str
    prompt_name:  str
    variant_a_id: int
    variant_b_id: int
    traffic_split: float
    status:       str
    winner_id:    Optional[int]
    min_queries:  int
    auto_promote: bool
    created_at:   datetime


@dataclass
class ABRoutingResult:
    prompt:      PromptVersion
    variant:     str            # "A" or "B"
    test_id:     Optional[int]
    log_entry_id: Optional[int]


async def create_ab_test(
    test_name:     str,
    prompt_name:   str,
    variant_a_id:  int,
    variant_b_id:  int,
    min_queries:   int   = 100,
    traffic_split: float = 0.5,
    auto_promote:  bool  = True,
) -> ABTest:
    """
    Create a new A/B test between two prompt versions.
    Both variants must exist for the same prompt_name.
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO ab_tests
                (test_name, prompt_name, variant_a_id, variant_b_id,
                 traffic_split, min_queries, auto_promote)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING *
            """,
            test_name, prompt_name, variant_a_id, variant_b_id,
            traffic_split, min_queries, auto_promote,
        )
    logger.info(
        f"A/B test created: {test_name} "
        f"(A=v{variant_a_id} vs B=v{variant_b_id}, split={traffic_split:.0%})"
    )
    return _row_to_test(row)


async def get_prompt_for_request(
    prompt_name: str,
    session_id:  str = "",
    user_id:     str = "",
    trace_id:    str = "",
) -> ABRoutingResult:
    """
    Get the right prompt version for this request.
    If an A/B test is running: route by traffic split.
    Otherwise: return the active version.
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        # Check for active A/B test on this prompt
        test_row = await conn.fetchrow(
            """
            SELECT * FROM ab_tests
            WHERE prompt_name = $1 AND status = 'running'
            ORDER BY created_at DESC
            LIMIT 1
            """,
            prompt_name,
        )

    if not test_row:
        # No test running — serve active version
        from backend.prompts.registry import get_active_prompt
        prompt = await get_active_prompt(prompt_name)
        if not prompt:
            raise ValueError(f"No active prompt found: {prompt_name}")
        return ABRoutingResult(
            prompt=prompt,
            variant="active",
            test_id=None,
            log_entry_id=None,
        )

    test = _row_to_test(test_row)

    # Route: random split based on traffic_split
    use_variant_a = random.random() < test.traffic_split
    variant_id    = test.variant_a_id if use_variant_a else test.variant_b_id
    variant_label = "A" if use_variant_a else "B"

    prompt = await get_prompt_by_id(variant_id)
    if not prompt:
        raise ValueError(f"Variant {variant_id} not found")

    # Log this routing decision for later analysis
    pool = await get_pool()
    async with pool.acquire() as conn:
        log_row = await conn.fetchrow(
            """
            INSERT INTO ab_query_log
                (test_id, variant_id, session_id, user_id, trace_id)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id
            """,
            test.id, variant_id, session_id, user_id, trace_id,
        )

    logger.debug(
        f"A/B routing: {prompt_name} → variant {variant_label} "
        f"(test={test.test_name})"
    )

    return ABRoutingResult(
        prompt=prompt,
        variant=variant_label,
        test_id=test.id,
        log_entry_id=log_row["id"],
    )


async def record_ab_feedback(
    log_entry_id: int,
    score:        float,
) -> Optional[ABTest]:
    """
    Record user feedback for an A/B log entry.
    Checks if auto-promotion threshold has been reached.
    Returns completed test if promoted, else None.
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        # Update feedback score on log entry
        await conn.execute(
            "UPDATE ab_query_log SET feedback_score = $1 WHERE id = $2",
            score, log_entry_id,
        )

        # Get the test this log entry belongs to
        log_row = await conn.fetchrow(
            "SELECT * FROM ab_query_log WHERE id = $1", log_entry_id
        )
        if not log_row:
            return None

        test_row = await conn.fetchrow(
            "SELECT * FROM ab_tests WHERE id = $1", log_row["test_id"]
        )
        if not test_row or test_row["status"] != "running":
            return None

    test = _row_to_test(test_row)

    # Check if we have enough data to auto-promote
    pool = await get_pool()
    async with pool.acquire() as conn:
        stats = await conn.fetch(
            """
            SELECT
                variant_id,
                COUNT(*) as total,
                AVG(feedback_score) FILTER (WHERE feedback_score IS NOT NULL) as avg_score,
                COUNT(feedback_score) as rated_count
            FROM ab_query_log
            WHERE test_id = $1
            GROUP BY variant_id
            """,
            test.id,
        )

    stats_map = {row["variant_id"]: row for row in stats}
    a_stats   = stats_map.get(test.variant_a_id, {})
    b_stats   = stats_map.get(test.variant_b_id, {})

    total_rated = (
        (a_stats.get("rated_count") or 0) +
        (b_stats.get("rated_count") or 0)
    )

    if total_rated < test.min_queries:
        logger.debug(
            f"A/B test {test.test_name}: {total_rated}/{test.min_queries} "
            f"rated queries — not ready to promote"
        )
        return None

    # Enough data — determine winner
    a_score = float(a_stats.get("avg_score") or 0.5)
    b_score = float(b_stats.get("avg_score") or 0.5)
    winner_id = test.variant_a_id if a_score >= b_score else test.variant_b_id
    winner_label = "A" if a_score >= b_score else "B"

    logger.info(
        f"A/B test {test.test_name} complete: "
        f"A={a_score:.3f} B={b_score:.3f} → winner={winner_label}"
    )

    if test.auto_promote:
        await set_active_version(winner_id, test.prompt_name)
        logger.info(f"Auto-promoted variant {winner_label} (id={winner_id})")

    # Mark test completed
    pool = await get_pool()
    async with pool.acquire() as conn:
        completed_row = await conn.fetchrow(
            """
            UPDATE ab_tests
            SET status = 'completed',
                winner_id = $1,
                completed_at = NOW()
            WHERE id = $2
            RETURNING *
            """,
            winner_id, test.id,
        )

    return _row_to_test(completed_row)


async def get_ab_test_stats(test_id: int) -> dict:
    """Return current A/B test statistics for admin UI."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        test_row = await conn.fetchrow(
            "SELECT * FROM ab_tests WHERE id = $1", test_id
        )
        if not test_row:
            return {}

        stats = await conn.fetch(
            """
            SELECT
                variant_id,
                COUNT(*)                    AS total_served,
                COUNT(feedback_score)       AS total_rated,
                AVG(feedback_score)         AS avg_score,
                SUM(CASE WHEN feedback_score >= 0.5 THEN 1 ELSE 0 END) AS thumbs_up,
                SUM(CASE WHEN feedback_score  < 0.5 THEN 1 ELSE 0 END) AS thumbs_down
            FROM ab_query_log
            WHERE test_id = $1
            GROUP BY variant_id
            """,
            test_id,
        )

    test = _row_to_test(test_row)
    stats_map = {row["variant_id"]: dict(row) for row in stats}

    def format_stats(variant_id: int, label: str) -> dict:
        s = stats_map.get(variant_id, {})
        return {
            "variant":       label,
            "variant_id":    variant_id,
            "total_served":  s.get("total_served", 0),
            "total_rated":   s.get("total_rated",  0),
            "avg_score":     round(float(s.get("avg_score") or 0), 4),
            "thumbs_up":     s.get("thumbs_up",    0),
            "thumbs_down":   s.get("thumbs_down",  0),
        }

    return {
        "test_id":     test.id,
        "test_name":   test.test_name,
        "prompt_name": test.prompt_name,
        "status":      test.status,
        "winner_id":   test.winner_id,
        "min_queries": test.min_queries,
        "variant_a":   format_stats(test.variant_a_id, "A"),
        "variant_b":   format_stats(test.variant_b_id, "B"),
        "total_queries": sum(
            int(stats_map.get(vid, {}).get("total_served", 0) or 0)
            for vid in [test.variant_a_id, test.variant_b_id]
        ),
        "completion_pct": min(100, round(  # FIXED: guard against division by zero when min_queries=0
            sum(
                int(stats_map.get(vid, {}).get("total_rated", 0) or 0)
                for vid in [test.variant_a_id, test.variant_b_id]
            ) / max(test.min_queries, 1) * 100, 1
        )),
    }


async def list_ab_tests(status: Optional[str] = None) -> list[dict]:
    """List all A/B tests, optionally filtered by status."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        if status:
            rows = await conn.fetch(
                "SELECT * FROM ab_tests WHERE status = $1 ORDER BY created_at DESC",
                status,
            )
        else:
            rows = await conn.fetch(
                "SELECT * FROM ab_tests ORDER BY created_at DESC"
            )

    results = []
    for row in rows:
        test  = _row_to_test(row)
        stats = await get_ab_test_stats(test.id)
        results.append(stats)
    return results


def _row_to_test(row) -> ABTest:
    return ABTest(
        id=row["id"],
        test_name=row["test_name"],
        prompt_name=row["prompt_name"],
        variant_a_id=row["variant_a_id"],
        variant_b_id=row["variant_b_id"],
        traffic_split=float(row["traffic_split"]),
        status=row["status"],
        winner_id=row.get("winner_id"),
        min_queries=row["min_queries"],
        auto_promote=row["auto_promote"],
        created_at=row["created_at"],
    )