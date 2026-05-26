"""
Seed Neo4j with sample knowledge graph data.
Run: python -m backend.graph_db.seeder
"""
import asyncio
import logging
from backend.graph_db.neo4j_client import run_write_query, run_bulk_write, run_query, close_driver  # FIXED: was missing `backend.` package prefix

logger = logging.getLogger(__name__)

PEOPLE = [
    {"name": "Alice Chen",     "role": "CEO",           "email": "alice@techcorp.com"},
    {"name": "Bob Martinez",   "role": "CTO",           "email": "bob@techcorp.com"},
    {"name": "Carol Williams", "role": "AI Researcher", "email": "carol@ailab.org"},
    {"name": "David Park",     "role": "Data Engineer", "email": "david@dataflow.io"},
    {"name": "Eve Johnson",    "role": "Product Lead",  "email": "eve@techcorp.com"},
    {"name": "Frank Liu",      "role": "ML Engineer",   "email": "frank@ailab.org"},
]

COMPANIES = [
    {"name": "TechCorp",    "industry": "Software",      "founded": 2015},
    {"name": "AILab",       "industry": "AI Research",   "founded": 2018},
    {"name": "DataFlow",    "industry": "Data Platform", "founded": 2019},
    {"name": "FinanceBank", "industry": "Banking",       "founded": 1990},
]

TOPICS = [
    {"name": "Large Language Models",         "category": "AI"},
    {"name": "Retrieval Augmented Generation","category": "AI"},
    {"name": "Vector Databases",              "category": "Data"},
    {"name": "Knowledge Graphs",              "category": "Data"},
    {"name": "Interest Rate Risk",            "category": "Finance"},
    {"name": "Banking Regulation",            "category": "Finance"},
    {"name": "LangGraph",                     "category": "AI"},
]

DOCUMENTS = [
    {"doc_id": "doc_001", "title": "State of AI Report 2024",  "source": "ailab_report_2024.pdf", "date": "2024-01-15"},
    {"doc_id": "doc_002", "title": "RAG Best Practices",       "source": "rag_practices.pdf",      "date": "2024-03-20"},
    {"doc_id": "doc_003", "title": "Banking Crisis Analysis",  "source": "banking_analysis.pdf",   "date": "2023-06-01"},
]

EVENTS = [
    {"event_id": "evt_001", "name": "AI Summit 2024",              "date": "2024-06-15", "type": "Conference"},
    {"event_id": "evt_002", "name": "SVB Collapse",                "date": "2023-03-10", "type": "Financial Crisis"},
    {"event_id": "evt_003", "name": "LLM Breakthrough Announcement","date": "2024-02-01", "type": "Product Launch"},
]

WORKS_AT        = [("Alice Chen","TechCorp"),("Bob Martinez","TechCorp"),("Eve Johnson","TechCorp"),("Carol Williams","AILab"),("Frank Liu","AILab"),("David Park","DataFlow")]
KNOWS           = [("Alice Chen","Carol Williams"),("Alice Chen","David Park"),("Bob Martinez","Frank Liu"),("Carol Williams","Frank Liu"),("David Park","Frank Liu")]
AUTHORED        = [("Carol Williams","doc_001"),("Frank Liu","doc_001"),("Carol Williams","doc_002"),("David Park","doc_002"),("Alice Chen","doc_003")]
DOC_MENTIONS    = [("doc_001","Large Language Models"),("doc_001","Retrieval Augmented Generation"),("doc_002","Vector Databases"),("doc_002","Retrieval Augmented Generation"),("doc_003","Interest Rate Risk"),("doc_003","Banking Regulation")]
COMPANY_TOPIC   = [("AILab","Large Language Models"),("AILab","Knowledge Graphs"),("TechCorp","LangGraph"),("DataFlow","Vector Databases")]
INVOLVES_PERSON = [("evt_001","Alice Chen"),("evt_001","Carol Williams"),("evt_003","Frank Liu")]
OCCURRED_AT     = [("evt_001","AILab"),("evt_002","FinanceBank"),("evt_003","TechCorp")]


async def seed_nodes():
    logger.info("Seeding nodes...")
    await run_bulk_write("MERGE (p:Person {name: row.name}) SET p.role = row.role, p.email = row.email", PEOPLE)
    await run_bulk_write("MERGE (c:Company {name: row.name}) SET c.industry = row.industry, c.founded = row.founded", COMPANIES)
    await run_bulk_write("MERGE (t:Topic {name: row.name}) SET t.category = row.category", TOPICS)
    await run_bulk_write("MERGE (d:Document {doc_id: row.doc_id}) SET d.title = row.title, d.source = row.source, d.date = row.date", DOCUMENTS)
    await run_bulk_write("MERGE (e:Event {event_id: row.event_id}) SET e.name = row.name, e.date = row.date, e.type = row.type", EVENTS)
    logger.info("  Nodes seeded")


async def seed_relationships():
    logger.info("Seeding relationships...")

    # Use bulk_write for all relationship types
    await run_bulk_write(
        "MATCH (p:Person {name: row.person}), (c:Company {name: row.company}) MERGE (p)-[:WORKS_AT]->(c)",
        [{"person": p, "company": c} for p, c in WORKS_AT],
    )
    await run_bulk_write(
        "MATCH (a:Person {name: row.a}), (b:Person {name: row.b}) MERGE (a)-[:KNOWS]->(b) MERGE (b)-[:KNOWS]->(a)",
        [{"a": a, "b": b} for a, b in KNOWS],
    )
    await run_bulk_write(
        "MATCH (p:Person {name: row.person}), (d:Document {doc_id: row.doc_id}) MERGE (p)-[:AUTHORED]->(d)",
        [{"person": p, "doc_id": d} for p, d in AUTHORED],
    )
    await run_bulk_write(
        "MATCH (d:Document {doc_id: row.doc_id}), (t:Topic {name: row.topic}) MERGE (d)-[:MENTIONS]->(t)",
        [{"doc_id": d, "topic": t} for d, t in DOC_MENTIONS],
    )
    await run_bulk_write(
        "MATCH (c:Company {name: row.company}), (t:Topic {name: row.topic}) MERGE (c)-[:RELATED_TO]->(t)",
        [{"company": c, "topic": t} for c, t in COMPANY_TOPIC],
    )
    await run_bulk_write(
        "MATCH (e:Event {event_id: row.event_id}), (p:Person {name: row.person}) MERGE (e)-[:INVOLVES]->(p)",
        [{"event_id": e, "person": p} for e, p in INVOLVES_PERSON],
    )
    await run_bulk_write(
        "MATCH (e:Event {event_id: row.event_id}), (c:Company {name: row.company}) MERGE (e)-[:OCCURRED_AT]->(c)",
        [{"event_id": e, "company": c} for e, c in OCCURRED_AT],
    )
    logger.info("  Relationships seeded")


async def main():
    logging.basicConfig(level=logging.INFO)
    logger.info("=== Neo4j Seeder ===")
    await seed_nodes()
    await seed_relationships()

    counts = await get_node_counts()
    logger.info(f"Node counts: {counts}")

    # Use run_query (read) not run_write_query for MATCH
    rel_count = await run_query("MATCH ()-[r]->() RETURN count(r) AS total")
    logger.info(f"Relationships: {rel_count[0]['total'] if rel_count else 0}")

    await close_driver()
    logger.info("=== Seeding complete ===")


if __name__ == "__main__":
    from backend.graph_db.neo4j_client import get_node_counts
    asyncio.run(main())