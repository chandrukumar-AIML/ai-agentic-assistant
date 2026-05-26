# backend/verticals/research/tools/pubmed_tool.py
"""
PubMed search for biomedical literature.
"""
import logging
import httpx
from xml.etree import ElementTree as ET

logger  = logging.getLogger(__name__)
_client = httpx.AsyncClient(timeout=15.0)

ESEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
EFETCH  = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"


async def search_pubmed(query: str, max_results: int = 5) -> list[dict]:
    """Search PubMed and return structured paper data."""
    try:
        # Step 1: Get PMIDs
        search_r = await _client.get(
            ESEARCH,
            params={"db": "pubmed", "term": query, "retmax": max_results,
                    "retmode": "json", "sort": "relevance"},
        )
        search_r.raise_for_status()
        pmids = search_r.json().get("esearchresult", {}).get("idlist", [])

        if not pmids:
            return []

        # Step 2: Fetch abstracts
        fetch_r = await _client.get(
            EFETCH,
            params={"db": "pubmed", "id": ",".join(pmids),
                    "retmode": "xml", "rettype": "abstract"},
        )
        fetch_r.raise_for_status()
        root    = ET.fromstring(fetch_r.content)
        articles = root.findall(".//PubmedArticle")

        papers = []
        for article in articles:
            pmid    = article.findtext(".//PMID", "")
            title   = article.findtext(".//ArticleTitle", "")
            abstract_el = article.find(".//AbstractText")
            abstract = abstract_el.text if abstract_el is not None else ""
            year    = article.findtext(".//PubDate/Year", "")
            authors = [
                f"{a.findtext('LastName', '')} {a.findtext('ForeName', '')[:1]}"
                for a in article.findall(".//Author")[:5]
            ]
            papers.append({
                "pmid":      pmid,
                "title":     title[:120],
                "abstract":  (abstract or "")[:400],
                "year":      year,
                "authors":   authors,
                "url":       f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
            })

        return papers
    except Exception as e:
        logger.error(f"PubMed search failed: {e}")
        return []