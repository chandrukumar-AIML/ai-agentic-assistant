import re
import time
import logging

from backend.agent.state import AgentState  # FIXED: wrong import path
from backend.agent.tools.base_tool import make_tool_result  # FIXED: wrong import path
from backend.graph_db.neo4j_client import run_query  # FIXED: wrong import path
from backend.config import get_settings  # FIXED: wrong import path (was `from config import get_settings`)
from backend.llm.ollama_openai import ollama_chat_completion, OLLAMA_MODEL

logger = logging.getLogger(__name__)
settings = get_settings()

GRAPH_SCHEMA = """
Node labels and properties:
  Person   (name: str, role: str, email: str)
  Company  (name: str, industry: str, founded: int)
  Document (doc_id: str, title: str, source: str, date: str)
  Topic    (name: str, category: str)
  Event    (event_id: str, name: str, date: str, type: str)

Relationship types (directional):
  (Person)   -[:WORKS_AT]->    (Company)
  (Person)   -[:KNOWS]->       (Person)
  (Person)   -[:AUTHORED]->    (Document)
  (Document) -[:MENTIONS]->    (Topic)
  (Company)  -[:RELATED_TO]->  (Topic)
  (Event)    -[:INVOLVES]->    (Person)
  (Event)    -[:OCCURRED_AT]-> (Company)

Fulltext index: entity_search covers Person.name, Company.name, Topic.name, Event.name
"""

CYPHER_SYSTEM_PROMPT = f"""You are a Neo4j Cypher expert.
Convert natural language queries into valid Cypher for this schema:

{GRAPH_SCHEMA}

Rules:
1. Return ONLY the Cypher query — no explanation, no markdown fences
2. Always use LIMIT 15 unless user asks for more
3. For name searches use: WHERE toLower(n.name) CONTAINS toLower($term)
4. Return readable properties as named columns, never raw node objects
5. If unanswerable with schema: RETURN 'no_match' AS result
"""

FORBIDDEN_CYPHER_OPS = {"DELETE", "DETACH DELETE", "CREATE", "SET", "REMOVE", "DROP"}


async def _generate_cypher(query: str) -> str:
    messages = [
        {"role": "system", "content": CYPHER_SYSTEM_PROMPT},
        {"role": "user",   "content": f"Natural language query: {query}"},
    ]
    cypher = (await ollama_chat_completion(
        messages=messages,
        model=OLLAMA_MODEL,
        temperature=0,
        max_tokens=300,
    )).strip()
    # Strip markdown fences
    if "```" in cypher:
        lines = cypher.split("\n")
        cypher = "\n".join(l for l in lines if not l.strip().startswith("```")).strip()
    return cypher


async def _fulltext_fallback(query: str) -> list[dict]:
    words = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', query)
    if not words:
        return []
    search_term = " OR ".join(words[:3])
    cypher = """
    CALL db.index.fulltext.queryNodes('entity_search', $term)
    YIELD node, score
    RETURN labels(node)[0] AS label, node.name AS name, score
    ORDER BY score DESC LIMIT 5
    """
    try:
        return await run_query(cypher, {"term": search_term})
    except Exception as e:
        logger.warning(f"Fulltext fallback failed: {e}")
        return []


def _format_graph_results(records: list[dict]) -> str:
    if not records:
        return "No matching records found."
    lines = []
    for i, record in enumerate(records, 1):
        parts = [f"{k}: {v}" for k, v in record.items() if v is not None and v != "no_match"]
        if parts:
            lines.append(f"{i}. {' | '.join(parts)}")
    return "\n".join(lines) if lines else "No meaningful results returned."


async def graph_querier_node(state: AgentState) -> dict:
    start = time.monotonic()
    query = state["user_query"]

    try:
        cypher = await _generate_cypher(query)
        logger.info(f"Graph tool Cypher: {cypher[:120]}")

        # Block write operations (prompt injection protection)
        cypher_upper = cypher.upper()
        if any(op in cypher_upper for op in FORBIDDEN_CYPHER_OPS):
            logger.warning(f"Blocked write Cypher: {cypher[:80]}")
            raise ValueError("Write operation in generated Cypher — blocked for safety.")

        records = await run_query(cypher)

        is_no_match = (
            not records or
            (len(records) == 1 and records[0].get("result") == "no_match")
        )

        if is_no_match:
            records = await _fulltext_fallback(query)
            confidence = 0.45 if records else 0.1
            content = (
                f"Direct query found nothing. Related entities:\n{_format_graph_results(records)}"
                if records else "No matching entities found in the knowledge graph."
            )
        else:
            confidence = 0.88
            content = _format_graph_results(records)

        result = make_tool_result(
            tool_name="graph_tool",
            content=content,
            source="neo4j",
            confidence=confidence,
            metadata={
                "cypher":        cypher,
                "record_count":  len(records),
                "fallback_used": is_no_match,
            },
        )

    except Exception as e:
        logger.error(f"Graph tool failed: {e}", exc_info=True)
        result = make_tool_result(
            tool_name="graph_tool",
            content=f"Knowledge graph query failed: {str(e)}",
            confidence=0.0,
            metadata={"error": str(e)},
        )

    elapsed = (time.monotonic() - start) * 1000
    return {
        "tool_results": state.get("tool_results", []) + [result],
        "latency_ms":   {"graph_querier": round(elapsed, 2)},
    }