# backend/verticals/research/tools/semantic_scholar_tool.py
"""
Semantic Scholar API — citation counts, references, influential papers.
"""
import logging
import httpx

logger  = logging.getLogger(__name__)
_client = httpx.AsyncClient(
    base_url="https://api.semanticscholar.org/graph/v1",
    timeout=15.0,
)


async def search_papers(query: str, limit: int = 5) -> list[dict]:
    """Search Semantic Scholar for papers with citation data."""
    try:
        r = await _client.get(
            "/paper/search",
            params={
                "query":  query,
                "limit":  limit,
                "fields": "title,abstract,year,citationCount,authors,externalIds,url",
            },
        )
        r.raise_for_status()
        papers = r.json().get("data", [])
        return [
            {
                "paper_id":      p.get("paperId", ""),
                "title":         p.get("title", "")[:120],
                "abstract":      (p.get("abstract") or "")[:400],
                "year":          p.get("year"),
                "citations":     p.get("citationCount", 0),
                "authors":       [a.get("name", "") for a in (p.get("authors") or [])[:4]],
                "arxiv_id":      (p.get("externalIds") or {}).get("ArXiv"),
                "url":           p.get("url", ""),
            }
            for p in papers
        ]
    except Exception as e:
        logger.error(f"Semantic Scholar search failed: {e}")
        return []


async def get_citations(paper_id: str, limit: int = 5) -> list[dict]:
    """Get papers that cite a given paper."""
    try:
        r = await _client.get(
            f"/paper/{paper_id}/citations",
            params={"fields": "title,year,citationCount", "limit": limit},
        )
        r.raise_for_status()
        cites = r.json().get("data", [])
        return [
            {
                "title":     c["citingPaper"].get("title", ""),
                "year":      c["citingPaper"].get("year"),
                "citations": c["citingPaper"].get("citationCount", 0),
            }
            for c in cites
        ]
    except Exception as e:
        logger.error(f"Citation fetch failed: {e}")
        return []