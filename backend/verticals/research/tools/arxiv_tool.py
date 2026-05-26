# backend/verticals/research/tools/arxiv_tool.py
"""
ArXiv paper search and retrieval.
"""
import logging
import re
import httpx
from xml.etree import ElementTree as ET

logger  = logging.getLogger(__name__)
_client = httpx.AsyncClient(timeout=20.0)

ARXIV_BASE = "http://export.arxiv.org/api/query"


async def search_papers(
    query:      str,
    max_results: int = 10,
    sort_by:     str = "relevance",  # relevance | lastUpdatedDate | submittedDate
) -> list[dict]:
    """Search ArXiv for papers."""
    try:
        params = {
            "search_query": f"all:{query}",
            "max_results":  max_results,
            "sortBy":       sort_by,
            "sortOrder":    "descending",
        }
        r    = await _client.get(ARXIV_BASE, params=params)
        r.raise_for_status()
        root = ET.fromstring(r.content)

        ns      = {"atom": "http://www.w3.org/2005/Atom"}
        entries = root.findall("atom:entry", ns)

        papers = []
        for entry in entries:
            arxiv_id = (entry.findtext("atom:id", "", ns) or "").split("/abs/")[-1]
            title    = (entry.findtext("atom:title", "", ns) or "").strip().replace("\n", " ")
            summary  = (entry.findtext("atom:summary", "", ns) or "").strip().replace("\n", " ")
            published = entry.findtext("atom:published", "", ns) or ""
            authors  = [
                a.findtext("atom:name", "", ns) or ""
                for a in entry.findall("atom:author", ns)
            ]
            papers.append({
                "arxiv_id":  arxiv_id,
                "title":     title[:120],
                "abstract":  summary[:500],
                "authors":   authors[:5],
                "published": published[:10],
                "url":       f"https://arxiv.org/abs/{arxiv_id}",
                "pdf_url":   f"https://arxiv.org/pdf/{arxiv_id}",
            })

        return papers
    except Exception as e:
        logger.error(f"ArXiv search failed: {e}")
        return []


async def get_paper_details(arxiv_id: str) -> dict | None:
    """Get detailed info for a specific paper."""
    papers = await search_papers(f"id:{arxiv_id}", max_results=1)
    return papers[0] if papers else None