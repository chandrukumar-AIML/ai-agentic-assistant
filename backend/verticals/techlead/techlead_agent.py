"""
Tech Lead / Architect Vertical — AI-powered technical leadership assistant.

Actions:
  adr               — Generate Architecture Decision Records (ADR)
  tech_debt         — Analyze and prioritize technical debt
  api_design        — Design RESTful API with OpenAPI spec
  arch_review       — Review system architecture for scalability and reliability
  perf_analysis     — Analyze performance issues and suggest improvements
  tech_radar        — Generate team technology radar assessment
"""
from __future__ import annotations

import logging
import time

from backend.llm.router import llm_router

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a Principal Software Architect and Tech Lead with 15+ years of experience
building distributed systems at scale. You are expert in: system design, microservices, event-driven
architecture, API design (REST/GraphQL/gRPC), database selection, cloud architecture (AWS/GCP/Azure),
performance engineering, technical debt management, and engineering leadership.
You think in terms of: CAP theorem, reliability, scalability, maintainability, and team velocity.
Output is always structured, opinionated, and technically precise."""


async def _llm(messages: list[dict], max_tokens: int = 600) -> str:
    text, _ = await llm_router.complete(messages=messages, temperature=0.2, max_tokens=max_tokens)
    return text


async def generate_adr(
    decision_title: str,
    context: str,
    options_considered: list[str] = None,
    decision: str = "",
    language: str = "en",
) -> dict:
    """Generate a formal Architecture Decision Record (ADR)."""
    options_text = "\n".join(f"- {o}" for o in (options_considered or []))
    options_section = f"\nOptions considered:\n{options_text}" if options_text else ""
    decision_section = f"\nPreferred decision: {decision}" if decision else ""

    prompt = f"""Write a formal Architecture Decision Record (ADR) in Michael Nygard format.

DECISION TITLE: {decision_title}

CONTEXT:
{context}{options_section}{decision_section}

Format as complete ADR with these sections:
# ADR-XXX: {decision_title}

**Status:** Proposed
**Date:** [today]
**Deciders:** [Tech Lead, Team]

## Context
[Detailed technical and business context]

## Decision Drivers
[3-5 key factors driving this decision]

## Considered Options
[For each option: pros, cons, and technical assessment]

## Decision Outcome
[Chosen option with full justification]

## Positive Consequences
[Benefits of this decision]

## Negative Consequences
[Trade-offs and risks accepted]

## Compliance
[How to verify this decision is followed]

## Links
[Related ADRs, RFCs, or documentation]"""

    start = time.monotonic()
    result = await _llm([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": prompt},
    ], max_tokens=700)
    latency_ms = round((time.monotonic() - start) * 1000)

    return {"action": "adr", "adr": result, "title": decision_title, "latency_ms": latency_ms}


async def analyze_tech_debt(
    codebase_description: str,
    known_issues: list[str] = None,
    team_size: int = 5,
    language: str = "en",
) -> dict:
    """Analyze and prioritize technical debt."""
    issues_text = "\n".join(f"- {i}" for i in (known_issues or []))
    issues_section = f"\nKnown issues:\n{issues_text}" if issues_text else ""

    prompt = f"""Analyze technical debt for this codebase.

CODEBASE: {codebase_description}
TEAM SIZE: {team_size} engineers{issues_section}

Provide:
1. **Debt Categories** — architectural, code, test, documentation, infrastructure debt
2. **Debt Inventory** — ranked list of 10 debt items with:
   - Description of the debt
   - Business impact (velocity slowdown %)
   - Remediation effort (days)
   - Risk if unaddressed
   - Priority score (impact / effort)
3. **Hotspot Analysis** — which areas have highest debt concentration
4. **Quick Wins** — 3 items that can be fixed in <1 sprint with high ROI
5. **Technical Debt Roadmap** — quarterly plan to reduce debt
6. **Debt Budget Rule** — recommended % of sprint capacity for debt work
7. **Metrics to Track** — how to measure debt reduction over time
8. **Code Smell Patterns** — specific anti-patterns to refactor first"""

    start = time.monotonic()
    result = await _llm([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": prompt},
    ], max_tokens=700)
    latency_ms = round((time.monotonic() - start) * 1000)

    return {"action": "tech_debt", "analysis": result, "latency_ms": latency_ms}


async def design_api(
    api_name: str,
    resources: list[str],
    use_cases: str,
    auth_type: str = "JWT",
    language: str = "en",
) -> dict:
    """Design a RESTful API with OpenAPI spec."""
    resources_text = ", ".join(resources) if resources else "inferred from use cases"

    prompt = f"""Design a production-grade REST API.

API NAME: {api_name}
RESOURCES: {resources_text}
USE CASES: {use_cases}
AUTH: {auth_type}

Provide:
1. **Resource Design** — noun-based resources, URL structure, versioning strategy
2. **OpenAPI 3.0 Spec Skeleton** — YAML for all endpoints with request/response schemas
3. **HTTP Methods Mapping** — GET/POST/PUT/PATCH/DELETE decisions with justification
4. **Status Codes** — which codes to use and when
5. **Error Response Format** — RFC 7807 Problem Details structure
6. **Pagination** — cursor vs offset, response envelope
7. **Filtering & Sorting** — query parameter conventions
8. **Rate Limiting Headers** — X-RateLimit-* headers strategy
9. **Auth Flow** — {auth_type} implementation details
10. **Idempotency** — which endpoints need idempotency keys
11. **Versioning Strategy** — URL vs header vs content negotiation trade-offs"""

    start = time.monotonic()
    result = await _llm([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": prompt},
    ], max_tokens=700)
    latency_ms = round((time.monotonic() - start) * 1000)

    return {"action": "api_design", "design": result, "api_name": api_name, "latency_ms": latency_ms}


async def review_architecture(
    system_description: str,
    current_scale: str,
    target_scale: str,
    pain_points: list[str] = None,
    language: str = "en",
) -> dict:
    """Review system architecture for scalability and reliability."""
    pain_text = "\n".join(f"- {p}" for p in (pain_points or []))
    pain_section = f"\nPain points:\n{pain_text}" if pain_text else ""

    prompt = f"""Review this system architecture.

SYSTEM: {system_description}
CURRENT SCALE: {current_scale}
TARGET SCALE: {target_scale}{pain_section}

Using the AWS Well-Architected Framework (5 pillars) + production best practices:

1. **Architecture Diagram** — ASCII C4 Context diagram
2. **Scalability Assessment** — bottlenecks at {target_scale}
3. **Reliability Gaps** — single points of failure, no redundancy
4. **Security Gaps** — authentication, authorization, data at rest/transit
5. **Performance Issues** — latency, throughput, caching opportunities
6. **Cost Optimization** — over-provisioned or inefficient components
7. **Operational Excellence** — observability, deploy pipeline, runbooks
8. **Migration Path** — prioritized steps from current to target architecture
9. **Trade-off Analysis** — what you're giving up vs gaining
10. **Decision Framework** — 3 architectural principles for this system"""

    start = time.monotonic()
    result = await _llm([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": prompt},
    ], max_tokens=700)
    latency_ms = round((time.monotonic() - start) * 1000)

    return {"action": "arch_review", "review": result, "latency_ms": latency_ms}


async def analyze_performance(
    symptoms: str,
    system_info: str = "",
    metrics: dict = None,
    language: str = "en",
) -> dict:
    """Analyze performance issues and provide optimization strategy."""
    metrics_text = "\n".join(f"- {k}: {v}" for k, v in (metrics or {}).items())
    metrics_section = f"\nMetrics:\n{metrics_text}" if metrics_text else ""
    system_section = f"\nSystem: {system_info}" if system_info else ""

    prompt = f"""Analyze these performance issues and provide optimization strategy.

SYMPTOMS: {symptoms}{system_section}{metrics_section}

Provide:
1. **Bottleneck Identification** — USE Method (Utilization, Saturation, Errors) analysis
2. **Root Cause Hypotheses** — top 3, ordered by likelihood with evidence
3. **Profiling Plan** — exactly what to measure and which tools to use
4. **Quick Wins** — optimizations achievable in <1 day
5. **Architectural Fixes** — medium-term structural changes (1-2 sprints)
6. **Caching Strategy** — what to cache, where, TTL, invalidation
7. **Database Optimizations** — query, connection pool, read replicas
8. **Code-Level Optimizations** — async, batching, lazy loading
9. **Infrastructure Scaling** — horizontal vs vertical for each component
10. **SLO Recommendations** — p50/p95/p99 latency targets for each service"""

    start = time.monotonic()
    result = await _llm([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": prompt},
    ], max_tokens=700)
    latency_ms = round((time.monotonic() - start) * 1000)

    return {"action": "perf_analysis", "analysis": result, "latency_ms": latency_ms}


async def generate_tech_radar(
    team_context: str,
    current_stack: list[str] = None,
    language: str = "en",
) -> dict:
    """Generate a technology radar assessment for the team."""
    stack_text = ", ".join(current_stack) if current_stack else "not specified"

    prompt = f"""Generate a technology radar for this engineering team.

TEAM CONTEXT: {team_context}
CURRENT STACK: {stack_text}

Output a Thoughtworks-style tech radar with 4 quadrants and 4 rings:

**Quadrants:** Techniques, Tools, Platforms, Languages & Frameworks

**Rings:**
- ADOPT — proven, use in production
- TRIAL — worth pursuing, try on low-risk projects
- ASSESS — interesting, worth researching
- HOLD — be cautious, no new use, migrate away

For each technology, specify:
- Quadrant + Ring placement
- 1-sentence justification
- Action for the team

Then provide:
1. **Recommended Adoptions** — top 3 additions to the stack
2. **Technologies to Retire** — 2-3 to migrate away from
3. **Investment Areas** — where to build team skill
4. **Risk Assessment** — which bets might not pay off"""

    start = time.monotonic()
    result = await _llm([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": prompt},
    ], max_tokens=700)
    latency_ms = round((time.monotonic() - start) * 1000)

    return {"action": "tech_radar", "radar": result, "latency_ms": latency_ms}


async def techlead_agent(
    action: str,
    payload: dict,
    language: str = "en",
) -> dict:
    """Main Tech Lead agent dispatcher."""
    action = action.lower().strip()

    dispatch = {
        "adr":           lambda: generate_adr(
            decision_title=payload.get("decision_title", ""),
            context=payload.get("context", ""),
            options_considered=payload.get("options_considered", []),
            decision=payload.get("decision", ""),
            language=language,
        ),
        "tech_debt":     lambda: analyze_tech_debt(
            codebase_description=payload.get("codebase_description", ""),
            known_issues=payload.get("known_issues", []),
            team_size=int(payload.get("team_size", 5)),
            language=language,
        ),
        "api_design":    lambda: design_api(
            api_name=payload.get("api_name", "API"),
            resources=payload.get("resources", []),
            use_cases=payload.get("use_cases", ""),
            auth_type=payload.get("auth_type", "JWT"),
            language=language,
        ),
        "arch_review":   lambda: review_architecture(
            system_description=payload.get("system_description", ""),
            current_scale=payload.get("current_scale", ""),
            target_scale=payload.get("target_scale", ""),
            pain_points=payload.get("pain_points", []),
            language=language,
        ),
        "perf_analysis": lambda: analyze_performance(
            symptoms=payload.get("symptoms", ""),
            system_info=payload.get("system_info", ""),
            metrics=payload.get("metrics", {}),
            language=language,
        ),
        "tech_radar":    lambda: generate_tech_radar(
            team_context=payload.get("team_context", ""),
            current_stack=payload.get("current_stack", []),
            language=language,
        ),
    }

    handler = dispatch.get(action)
    if handler:
        return await handler()
    return {
        "error": f"Unknown action '{action}'. Valid: adr, tech_debt, api_design, arch_review, perf_analysis, tech_radar"
    }
