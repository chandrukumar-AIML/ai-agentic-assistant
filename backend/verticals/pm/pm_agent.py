"""
Project Manager / Scrum Vertical — AI-powered agile project management assistant.

Actions:
  user_story        — Generate user stories from feature idea
  sprint_plan       — Create sprint backlog with priorities and estimates
  acceptance_criteria — Generate DoD and acceptance criteria
  retrospective     — Facilitate sprint retrospective analysis
  roadmap           — Generate quarterly product roadmap
  estimation        — Story point estimation with PERT/Planning Poker
"""
from __future__ import annotations

import logging
import time

from backend.llm.router import llm_router

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a seasoned Agile Project Manager and Scrum Master with 12+ years of experience
in software product delivery. You excel at writing INVEST-compliant user stories, facilitating ceremonies,
managing backlogs, and driving product roadmaps. Output is always structured, professional, and actionable.
You follow the Scrum Guide, SAFe, and standard agile frameworks."""


async def _llm(messages: list[dict], max_tokens: int = 600) -> str:
    text, _ = await llm_router.complete(messages=messages, temperature=0.3, max_tokens=max_tokens)
    return text


async def generate_user_stories(
    feature_idea: str,
    persona: str = "user",
    priority: str = "medium",
    language: str = "en",
) -> dict:
    """Generate INVEST-compliant user stories with acceptance criteria."""
    prompt = f"""Generate professional user stories for the following feature idea.
Persona: {persona}
Priority: {priority}

FEATURE IDEA:
{feature_idea}

Output:
1. **Epic** — high-level epic title and description
2. **3-5 User Stories** in format: "As a [persona], I want [goal] so that [benefit]"
   For each story:
   - Story ID (US-001 etc.)
   - Story Points estimate (Fibonacci: 1,2,3,5,8,13)
   - Priority (Must Have / Should Have / Could Have / Won't Have — MoSCoW)
   - Acceptance Criteria (3-5 bullet points)
   - Dependencies
3. **INVEST Checklist** — verify each story is Independent, Negotiable, Valuable, Estimable, Small, Testable"""

    start = time.monotonic()
    result = await _llm([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": prompt},
    ], max_tokens=700)
    latency_ms = round((time.monotonic() - start) * 1000)

    return {
        "action":       "user_story",
        "feature":      feature_idea[:100],
        "user_stories": result,
        "latency_ms":   latency_ms,
    }


async def create_sprint_plan(
    team_size: int,
    sprint_duration_weeks: int,
    backlog_items: list[str],
    velocity: int = 0,
    language: str = "en",
) -> dict:
    """Create a sprint plan from backlog items."""
    items_text = "\n".join(f"- {item}" for item in backlog_items[:15])
    est_velocity = velocity or (team_size * sprint_duration_weeks * 8)

    prompt = f"""Create a sprint plan for:
- Team size: {team_size} engineers
- Sprint duration: {sprint_duration_weeks} weeks
- Estimated velocity: {est_velocity} story points

BACKLOG ITEMS:
{items_text}

Provide:
1. **Sprint Goal** — one clear sentence
2. **Sprint Backlog** — prioritized list with story point assignments that fit the velocity
3. **Capacity Planning** — days per engineer, buffer for ceremonies (20%)
4. **Daily Standup Template** — 3 questions format
5. **Definition of Done** — team-level checklist
6. **Sprint Risk Register** — top 3 risks with mitigation
7. **Ceremony Schedule** — planning, daily, review, retro timings"""

    start = time.monotonic()
    result = await _llm([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": prompt},
    ], max_tokens=700)
    latency_ms = round((time.monotonic() - start) * 1000)

    return {
        "action":       "sprint_plan",
        "sprint_plan":  result,
        "velocity":     est_velocity,
        "latency_ms":   latency_ms,
    }


async def run_retrospective(
    went_well: list[str],
    improvements: list[str],
    action_items: list[str],
    sprint_number: int = 1,
    language: str = "en",
) -> dict:
    """Analyze sprint retrospective inputs and generate structured output."""
    well_text    = "\n".join(f"- {x}" for x in went_well)
    improve_text = "\n".join(f"- {x}" for x in improvements)
    action_text  = "\n".join(f"- {x}" for x in action_items)

    prompt = f"""Facilitate a sprint {sprint_number} retrospective analysis.

WHAT WENT WELL:
{well_text}

WHAT NEEDS IMPROVEMENT:
{improve_text}

ACTION ITEMS PROPOSED:
{action_text}

Provide:
1. **Key Themes** — group inputs into 2-3 themes
2. **Root Cause Analysis** — for top improvement areas (5-Why technique)
3. **SMART Action Items** — refine proposed actions to be Specific, Measurable, Achievable, Relevant, Time-bound
4. **Process Improvements** — specific workflow changes to implement
5. **Team Health Score** (1-10) with reasoning
6. **Next Sprint Focus** — top 3 priorities based on retro findings"""

    start = time.monotonic()
    result = await _llm([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": prompt},
    ], max_tokens=600)
    latency_ms = round((time.monotonic() - start) * 1000)

    return {
        "action":       "retrospective",
        "analysis":     result,
        "latency_ms":   latency_ms,
    }


async def generate_roadmap(
    product_name: str,
    vision: str,
    themes: list[str],
    quarters: int = 4,
    language: str = "en",
) -> dict:
    """Generate a quarterly product roadmap."""
    themes_text = "\n".join(f"- {t}" for t in themes)
    prompt = f"""Create a {quarters}-quarter product roadmap for:

Product: {product_name}
Vision: {vision}

Strategic Themes:
{themes_text}

Provide:
1. **Now / Next / Later** roadmap overview
2. **Quarterly Breakdown** (Q1-Q{quarters}):
   - Theme focus
   - Key epics and features
   - Success metrics / OKRs
   - Dependencies and risks
3. **Milestone Timeline** — key releases and checkpoints
4. **Stakeholder Communication** — what to share with leadership vs engineering
5. **Assumption Log** — key assumptions behind this roadmap"""

    start = time.monotonic()
    result = await _llm([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": prompt},
    ], max_tokens=700)
    latency_ms = round((time.monotonic() - start) * 1000)

    return {
        "action":     "roadmap",
        "product":    product_name,
        "roadmap":    result,
        "latency_ms": latency_ms,
    }


async def estimate_stories(
    stories: list[str],
    technique: str = "planning_poker",
    language: str = "en",
) -> dict:
    """Estimate user stories using Planning Poker or PERT."""
    stories_text = "\n".join(f"{i+1}. {s}" for i, s in enumerate(stories[:10]))
    prompt = f"""Estimate these user stories using {technique}.

USER STORIES:
{stories_text}

For each story provide:
- Story Points (Fibonacci: 1, 2, 3, 5, 8, 13, 21)
- Complexity factors (technical, business, unknowns)
- Estimation rationale (1-2 sentences)
- Comparison to reference story if applicable

Then provide:
- **Team Velocity Recommendation** — suggested velocity for a 5-person team
- **Estimation Confidence** (High/Medium/Low) per story
- **Risk-Adjusted Total** — points with 20% buffer"""

    start = time.monotonic()
    result = await _llm([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": prompt},
    ], max_tokens=500)
    latency_ms = round((time.monotonic() - start) * 1000)

    return {
        "action":     "estimation",
        "estimates":  result,
        "latency_ms": latency_ms,
    }


async def pm_agent(
    action: str,
    payload: dict,
    language: str = "en",
) -> dict:
    """Main PM agent dispatcher."""
    action = action.lower().strip()

    if action == "user_story":
        return await generate_user_stories(
            feature_idea=payload.get("feature_idea", ""),
            persona=payload.get("persona", "user"),
            priority=payload.get("priority", "medium"),
            language=language,
        )
    elif action == "sprint_plan":
        return await create_sprint_plan(
            team_size=int(payload.get("team_size", 5)),
            sprint_duration_weeks=int(payload.get("sprint_duration_weeks", 2)),
            backlog_items=payload.get("backlog_items", []),
            velocity=int(payload.get("velocity", 0)),
            language=language,
        )
    elif action == "retrospective":
        return await run_retrospective(
            went_well=payload.get("went_well", []),
            improvements=payload.get("improvements", []),
            action_items=payload.get("action_items", []),
            sprint_number=int(payload.get("sprint_number", 1)),
            language=language,
        )
    elif action == "roadmap":
        return await generate_roadmap(
            product_name=payload.get("product_name", "Product"),
            vision=payload.get("vision", ""),
            themes=payload.get("themes", []),
            quarters=int(payload.get("quarters", 4)),
            language=language,
        )
    elif action == "estimation":
        return await estimate_stories(
            stories=payload.get("stories", []),
            technique=payload.get("technique", "planning_poker"),
            language=language,
        )
    else:
        return {
            "error": f"Unknown action '{action}'. Valid: user_story, sprint_plan, retrospective, roadmap, estimation"
        }
