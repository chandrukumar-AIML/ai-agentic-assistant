"""
Neo4j schema setup — constraints and indexes.
Called once at startup; non-fatal if Neo4j is unavailable.
"""
import logging
from backend.graph_db.neo4j_client import run_write_query

logger = logging.getLogger(__name__)

# Uniqueness constraints ensure MERGE is idempotent and fast
_CONSTRAINTS = [
    "CREATE CONSTRAINT person_name IF NOT EXISTS FOR (p:Person)   REQUIRE p.name     IS UNIQUE",
    "CREATE CONSTRAINT company_name IF NOT EXISTS FOR (c:Company) REQUIRE c.name     IS UNIQUE",
    "CREATE CONSTRAINT topic_name IF NOT EXISTS   FOR (t:Topic)   REQUIRE t.name     IS UNIQUE",
    "CREATE CONSTRAINT doc_id IF NOT EXISTS       FOR (d:Document) REQUIRE d.doc_id  IS UNIQUE",
    "CREATE CONSTRAINT event_id IF NOT EXISTS     FOR (e:Event)   REQUIRE e.event_id IS UNIQUE",
]

# Full-text indexes for keyword search
_INDEXES = [
    """CREATE FULLTEXT INDEX person_fulltext IF NOT EXISTS
       FOR (p:Person) ON EACH [p.name, p.role]""",
    """CREATE FULLTEXT INDEX document_fulltext IF NOT EXISTS
       FOR (d:Document) ON EACH [d.title, d.source]""",
    """CREATE FULLTEXT INDEX topic_fulltext IF NOT EXISTS
       FOR (t:Topic) ON EACH [t.name, t.category]""",
]


async def apply_schema() -> None:
    """Apply all constraints and indexes. Safe to run multiple times (IF NOT EXISTS)."""
    logger.info("Applying Neo4j schema constraints and indexes...")

    for stmt in _CONSTRAINTS:
        try:
            await run_write_query(stmt)
        except Exception as e:
            logger.warning(f"Constraint skipped (may already exist): {e}")

    for stmt in _INDEXES:
        try:
            await run_write_query(stmt)
        except Exception as e:
            logger.warning(f"Index skipped (may already exist): {e}")

    logger.info("Neo4j schema applied successfully")
