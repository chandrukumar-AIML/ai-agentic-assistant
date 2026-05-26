# backend/verticals/research/agent.py
"""
Research Vertical Agent.
Multi-source academic research with structured report output.
"""
import time
import logging
from typing import Any

from backend.verticals.base                             import BaseVerticalAgent, VerticalResult
from backend.verticals.research.tools                   import arxiv_tool, semantic_scholar_tool, pubmed_tool
from backend.agent.tools.web_search_tool                import _tavily_search
from backend.utils.text                                  import deduplicate_ordered

logger = logging.getLogger(__name__)


class ResearchVerticalAgent(BaseVerticalAgent):
    vertical_name = "research"
    description   = (
        "Expert research analyst. Searches ArXiv, PubMed, Semantic Scholar, "
        "and web for academic papers. Generates structured literature reviews."
    )

    @property
    def system_prompt(self) -> str:
        return """You are an Expert Research Analyst AI assistant.

Your capabilities:
- Search ArXiv for AI/ML/CS papers
- Search PubMed for biomedical literature
- Search Semantic Scholar for citation data
- Synthesise findings into structured research reports

Research report structure:
1. **Executive Summary** (2-3 sentences)
2. **Key Papers** (top 3-5, with brief description and significance)
3. **Main Findings** (what the papers collectively show)
4. **Research Gaps** (what questions remain open)
5. **Recommended Reading** (most important papers to read first)

Always:
- Sort papers by relevance and citation count
- Note publication dates (AI field moves fast — prefer recent)
- Distinguish empirical results from theoretical claims
- Flag if findings conflict across papers"""

    async def run(
        self,
        query:          str,
        context:        dict[str, Any],
        memory_context: str = "",
    ) -> VerticalResult:
        start   = time.monotonic()
        sources = []

        # Determine which databases to search
        q_lower  = query.lower()
        use_bio  = any(w in q_lower for w in ["medical", "clinical", "drug", "disease", "bio"])
        use_web  = any(w in q_lower for w in ["news", "recent", "latest", "2024", "2025"])

        # ── ArXiv search ───────────────────────────────────────────────────
        arxiv_papers = await arxiv_tool.search_papers(query, max_results=8, sort_by="relevance")
        recent_papers = await arxiv_tool.search_papers(query, max_results=3, sort_by="submittedDate")

        # ── Semantic Scholar — get citation counts ─────────────────────────
        ss_papers = await semantic_scholar_tool.search_papers(query, limit=5)

        # ── PubMed (if biomedical) ─────────────────────────────────────────
        pubmed_papers = []
        if use_bio:
            pubmed_papers = await pubmed_tool.search_pubmed(query, max_results=5)
            sources.append(f"https://pubmed.ncbi.nlm.nih.gov/?term={query[:50]}")

        # ── Web search for news/blog posts ─────────────────────────────────
        web_results = []
        if use_web:
            web_results = await _tavily_search(query + " research 2024 2025", max_results=3)

        # ── Compile all papers ─────────────────────────────────────────────
        all_papers = []
        seen_titles = set()

        for p in arxiv_papers + recent_papers:
            title = p.get("title", "")
            if title not in seen_titles:
                seen_titles.add(title)
                all_papers.append({**p, "source": "arxiv"})
                sources.append(p.get("url", ""))

        # Merge Semantic Scholar citation data
        ss_by_title = {p["title"][:50]: p for p in ss_papers}
        for p in all_papers:
            ss_match = ss_by_title.get(p["title"][:50], {})
            p["citations"] = ss_match.get("citations", 0)

        for p in pubmed_papers:
            title = p.get("title", "")
            if title not in seen_titles:
                seen_titles.add(title)
                all_papers.append({**p, "source": "pubmed", "citations": 0})

        # Sort by citations then recency
        all_papers.sort(
            key=lambda p: (p.get("citations", 0), p.get("published", p.get("year", ""))),
            reverse=True,
        )
        top_papers = all_papers[:10]

        # ── Format papers for LLM ──────────────────────────────────────────
        paper_text = ""
        for i, p in enumerate(top_papers, 1):
            paper_text += (
                f"\n[{i}] {p.get('title','')}\n"
                f"    Authors: {', '.join(p.get('authors', [])[:3])}\n"
                f"    Year: {p.get('published', p.get('year', 'N/A'))[:4]}\n"
                f"    Citations: {p.get('citations', 'N/A')}\n"
                f"    Abstract: {p.get('abstract', '')[:300]}...\n"
                f"    URL: {p.get('url', '')}\n"
            )

        web_text = ""
        if web_results:
            web_text = "\n\nWEB/BLOG SOURCES:\n" + "\n".join(
                f"- {r.get('url', '')}: {r.get('content', '')[:200]}"
                for r in web_results
            )

        # ── LLM synthesis → structured report ─────────────────────────────
        system  = self.system_prompt + (f"\n{memory_context}" if memory_context else "")
        report  = await self._call_llm(
            user_content=(
                f"Research query: {query}\n\n"
                f"Papers found ({len(top_papers)}):\n{paper_text}"
                f"{web_text}\n\n"
                f"Generate a structured research report following your format."
            ),
            system_content=system,
            temperature=0.2,
            max_tokens=2000,
        )

        return VerticalResult(
            vertical="research",
            content=report,
            sources=deduplicate_ordered(s for s in sources if s),
            metadata={
                "papers_found":  len(all_papers),
                "arxiv_papers":  len(arxiv_papers),
                "pubmed_papers": len(pubmed_papers),
                "ss_papers":     len(ss_papers),
            },
            latency_ms=(time.monotonic() - start) * 1000,
        )