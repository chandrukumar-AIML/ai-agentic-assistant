"""
QA Engineer Vertical — AI-powered quality assurance assistant.

Actions:
  generate_tests    — Generate test cases (unit/integration/e2e) from feature description
  analyze_bug       — Structured bug report analysis with reproduction steps
  test_plan         — Create full test plan with coverage matrix
  review_quality    — Code quality review focused on testability and edge cases
  acceptance_criteria — Generate Gherkin Given/When/Then acceptance criteria
"""
from __future__ import annotations

import logging
import time
from typing import Optional

from backend.llm.router import llm_router

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a senior QA Engineer and Test Architect with 10+ years of experience.
You write precise, executable test cases following industry standards (IEEE 829, ISO 29119).
You think in terms of: boundary values, equivalence partitioning, negative paths, race conditions,
and security edge cases. Output is always structured, professional, and actionable."""


async def _llm(messages: list[dict], max_tokens: int = 600) -> str:
    text, _ = await llm_router.complete(messages=messages, temperature=0.2, max_tokens=max_tokens)
    return text


async def generate_tests(
    feature_description: str,
    test_type: str = "unit",
    framework: str = "pytest",
    language: str = "en",
) -> dict:
    """Generate test cases from a feature/requirement description."""
    prompt = f"""Generate {test_type} test cases for the following feature.
Framework: {framework}

FEATURE DESCRIPTION:
{feature_description}

Output format:
1. List 5-8 test cases with:
   - Test ID (TC-001 etc.)
   - Test Name
   - Preconditions
   - Test Steps (numbered)
   - Expected Result
   - Priority (P0/P1/P2)
   - Test Type (positive/negative/boundary/performance)

Then provide {framework} code stubs for the top 3 test cases."""

    start = time.monotonic()
    result = await _llm([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": prompt},
    ], max_tokens=700)
    latency_ms = round((time.monotonic() - start) * 1000)

    return {
        "action":      "generate_tests",
        "test_type":   test_type,
        "framework":   framework,
        "test_cases":  result,
        "latency_ms":  latency_ms,
    }


async def analyze_bug(
    bug_description: str,
    logs: str = "",
    environment: str = "",
    language: str = "en",
) -> dict:
    """Analyze a bug report — root cause, severity, reproduction steps, fix hints."""
    env_section = f"\nEnvironment: {environment}" if environment else ""
    log_section = f"\n\nLOGS/STACK TRACE:\n{logs[:2000]}" if logs else ""

    prompt = f"""Analyze this bug report and provide a structured QA assessment.

BUG DESCRIPTION:
{bug_description}{env_section}{log_section}

Provide:
1. **Severity** (Critical/Major/Minor/Trivial) with justification
2. **Root Cause Analysis** — likely cause based on description
3. **Reproduction Steps** — minimal numbered steps to reproduce
4. **Impact Assessment** — what features/users are affected
5. **Fix Recommendations** — top 3 suggested fixes
6. **Regression Risk** — areas to test after fix
7. **Test Cases to Add** — 2-3 test cases that would catch this bug"""

    start = time.monotonic()
    result = await _llm([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": prompt},
    ], max_tokens=600)
    latency_ms = round((time.monotonic() - start) * 1000)

    return {
        "action":     "analyze_bug",
        "analysis":   result,
        "latency_ms": latency_ms,
    }


async def create_test_plan(
    project_name: str,
    scope: str,
    modules: list[str] = None,
    timeline_days: int = 14,
    language: str = "en",
) -> dict:
    """Create a comprehensive test plan with coverage matrix."""
    modules_text = ", ".join(modules) if modules else "all modules"
    prompt = f"""Create a professional test plan for:

Project: {project_name}
Scope: {scope}
Modules in scope: {modules_text}
Timeline: {timeline_days} days

Include:
1. **Test Objectives** — what we're validating
2. **Test Scope** — in-scope and out-of-scope
3. **Test Strategy** — unit / integration / system / UAT breakdown with % effort
4. **Test Environment Requirements** — hardware, software, data
5. **Coverage Matrix** — Feature × Test Type grid (✓/✗)
6. **Risk & Mitigation** — top 3 testing risks
7. **Entry / Exit Criteria** — when to start and stop testing
8. **Milestone Schedule** — {timeline_days}-day plan with weekly targets
9. **Defect Management** — severity classification and SLA"""

    start = time.monotonic()
    result = await _llm([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": prompt},
    ], max_tokens=700)
    latency_ms = round((time.monotonic() - start) * 1000)

    return {
        "action":      "test_plan",
        "project":     project_name,
        "test_plan":   result,
        "latency_ms":  latency_ms,
    }


async def review_quality(
    code: str,
    language_name: str = "Python",
    lang: str = "en",
) -> dict:
    """Review code for quality, testability, and edge cases."""
    prompt = f"""Perform a QA-focused code review of this {language_name} code.

```{language_name.lower()}
{code[:3000]}
```

Provide:
1. **Testability Score** (1-10) with reasoning
2. **Edge Cases Missing** — list untested paths
3. **Error Handling Gaps** — missing exception handling
4. **Code Smells** — what makes this hard to test
5. **Suggested Refactoring** — to improve testability
6. **Test Coverage Gaps** — specific scenarios missing from test suite
7. **Security Test Cases** — input validation, injection points to test"""

    start = time.monotonic()
    result = await _llm([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": prompt},
    ], max_tokens=600)
    latency_ms = round((time.monotonic() - start) * 1000)

    return {
        "action":     "review_quality",
        "review":     result,
        "latency_ms": latency_ms,
    }


async def generate_acceptance_criteria(
    user_story: str,
    language: str = "en",
) -> dict:
    """Generate Gherkin Given/When/Then acceptance criteria from a user story."""
    prompt = f"""Generate professional acceptance criteria in Gherkin format for this user story.

USER STORY:
{user_story}

Provide:
1. **3-5 Scenarios** in Gherkin (Feature / Scenario / Given / When / Then / And)
   - Happy path
   - Error/negative paths
   - Boundary conditions
2. **Definition of Done** checklist (8-10 items)
3. **Non-functional Requirements** to validate (performance, security, accessibility)"""

    start = time.monotonic()
    result = await _llm([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": prompt},
    ], max_tokens=500)
    latency_ms = round((time.monotonic() - start) * 1000)

    return {
        "action":               "acceptance_criteria",
        "user_story":           user_story,
        "acceptance_criteria":  result,
        "latency_ms":           latency_ms,
    }


async def qa_agent(
    action: str,
    payload: dict,
    language: str = "en",
) -> dict:
    """Main QA agent dispatcher."""
    action = action.lower().strip()

    if action == "generate_tests":
        return await generate_tests(
            feature_description=payload.get("feature_description", ""),
            test_type=payload.get("test_type", "unit"),
            framework=payload.get("framework", "pytest"),
            language=language,
        )
    elif action == "analyze_bug":
        return await analyze_bug(
            bug_description=payload.get("bug_description", ""),
            logs=payload.get("logs", ""),
            environment=payload.get("environment", ""),
            language=language,
        )
    elif action == "test_plan":
        return await create_test_plan(
            project_name=payload.get("project_name", "Project"),
            scope=payload.get("scope", ""),
            modules=payload.get("modules", []),
            timeline_days=int(payload.get("timeline_days", 14)),
            language=language,
        )
    elif action == "review_quality":
        return await review_quality(
            code=payload.get("code", ""),
            language_name=payload.get("language_name", "Python"),
            lang=language,
        )
    elif action == "acceptance_criteria":
        return await generate_acceptance_criteria(
            user_story=payload.get("user_story", ""),
            language=language,
        )
    else:
        return {
            "error": f"Unknown action '{action}'. Valid: generate_tests, analyze_bug, test_plan, review_quality, acceptance_criteria"
        }
