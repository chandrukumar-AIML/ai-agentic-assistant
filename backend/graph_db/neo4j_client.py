import logging
from typing import Any
from neo4j import AsyncGraphDatabase, AsyncDriver
from neo4j.exceptions import ServiceUnavailable, AuthError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from backend.config import get_settings  # FIXED: was bare `config` import, must be absolute package path

logger   = logging.getLogger(__name__)
settings = get_settings()

_driver: AsyncDriver | None = None


async def get_driver() -> AsyncDriver:
    global _driver
    if _driver is None:
        _driver = AsyncGraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
            max_connection_pool_size=50,
            connection_acquisition_timeout=5,
        )
        await _driver.verify_connectivity()
        logger.info("Neo4j driver connected")
    return _driver


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    retry=retry_if_exception_type(ServiceUnavailable),
    reraise=True,
)
async def run_query(
    cypher: str,
    params: dict | None = None,
    database: str = "neo4j",
) -> list[dict[str, Any]]:
    """Execute a read Cypher query."""
    driver = await get_driver()
    async with driver.session(database=database) as session:
        result = await session.run(cypher, params or {})
        return [record.data() async for record in result]


def _make_write_tx(cypher: str, params: dict):
    """Factory function — avoids late-binding closure bug with lambdas in loops."""
    async def tx_fn(tx):
        await tx.run(cypher, params)
    return tx_fn


def _make_bulk_tx(cypher: str, batch: list):
    """Factory function for bulk UNWIND writes."""
    async def tx_fn(tx):
        await tx.run(cypher, {"batch": batch})
    return tx_fn


async def run_write_query(
    cypher: str,
    params: dict | None = None,
    database: str = "neo4j",
) -> None:
    """Execute a write Cypher query inside a transaction."""
    driver = await get_driver()
    async with driver.session(database=database) as session:
        await session.execute_write(_make_write_tx(cypher, params or {}))


async def run_bulk_write(
    cypher: str,
    params_list: list[dict],
    database: str = "neo4j",
    batch_size: int = 500,
) -> int:
    """
    Execute a parameterised write for many records.
    Uses UNWIND for efficiency — single round trip per batch.
    Returns total records processed.
    """
    driver = await get_driver()
    total = 0

    for i in range(0, len(params_list), batch_size):
        batch = params_list[i: i + batch_size]
        bulk_cypher = f"UNWIND $batch AS row {cypher}"

        async with driver.session(database=database) as session:
            await session.execute_write(_make_bulk_tx(bulk_cypher, batch))
        total += len(batch)
        logger.debug(f"Bulk write: {total}/{len(params_list)} records")

    return total


async def close_driver():
    global _driver
    if _driver:
        await _driver.close()
        _driver = None
        logger.info("Neo4j driver closed")


async def health_check() -> bool:
    try:
        records = await run_query("RETURN 1 AS ok")
        return bool(records and records[0].get("ok") == 1)
    except Exception as e:
        logger.error(f"Neo4j health check failed: {e}")
        return False


_ALLOWED_NODE_LABELS = frozenset({"Person", "Company", "Document", "Topic", "Event"})  # FIXED: allowlist guards label injection


async def get_node_counts() -> dict[str, int]:
    labels = list(_ALLOWED_NODE_LABELS)
    counts = {}
    for label in labels:
        if label not in _ALLOWED_NODE_LABELS:  # FIXED: reject any label not in the allowlist to prevent Cypher injection
            logger.warning(f"get_node_counts: rejected unlisted label '{label}'")
            continue
        result = await run_query(f"MATCH (n:{label}) RETURN count(n) AS cnt")  # label is allowlist-validated above
        counts[label] = result[0]["cnt"] if result else 0
    return counts