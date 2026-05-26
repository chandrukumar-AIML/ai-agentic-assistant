# backend/agents/code_agent.py
"""
Code Agent: generation, execution, review, unit test writing.
Best for: write code, debug, explain code, generate tests.
"""
import time
import asyncio
import logging
import re
from typing import Any

from backend.agent.base_agent import BaseWorkerAgent, WorkerResult
from backend.agent.tools.code_runner_tool import _run_sandboxed, EXEC_TIMEOUT_SECONDS

logger = logging.getLogger(__name__)


class CodeAgent(BaseWorkerAgent):
    name        = "code_agent"
    description = (
        "Expert Python developer. Writes code, debugs errors, "
        "reviews code quality, generates unit tests. "
        "Best for: write/fix/explain/test code tasks."
    )

    @property
    def system_prompt(self) -> str:
        return """You are a Senior Python Developer Agent specialised in writing production-quality code.

Your responses for code tasks:
1. Write clean, typed, documented Python
2. Always include error handling (try/except)
3. Add type hints to all functions
4. Write docstrings for public functions
5. Prefer async/await for I/O operations
6. When fixing bugs: explain the root cause first
7. When writing tests: cover happy path + edge cases + error cases
8. Format all code in fenced ```python blocks

Do NOT include placeholder comments like "# TODO" or "# implement this".
Write complete, runnable code every time."""

    async def _generate_code(
        self, query: str, memory_context: str = ""
    ) -> tuple[str, str]:
        """Generate code and extract the code block from LLM response."""
        system  = self.system_prompt + (f"\n{memory_context}" if memory_context else "")
        raw     = await self._call_llm(
            user_content=query,
            system_content=system,
            temperature=0.1,
            max_tokens=2000,
        )
        # Extract code block
        match   = re.search(r"```python\n?(.*?)```", raw, re.DOTALL)
        code    = match.group(1).strip() if match else ""
        return raw, code

    async def _review_code(self, code: str) -> str:
        """Review code quality and suggest improvements."""
        review_prompt = f"""Review this Python code for:
1. Correctness — will it run without errors?
2. Security — any unsafe operations?
3. Style — PEP8 compliance, naming conventions
4. Performance — any obvious inefficiencies?
5. Missing error handling

Code:
```python
{code}
```

Be specific. List each issue with line number if possible.
If code is good, say "Code quality: PASS" and explain why."""

        return await self._call_llm(
            user_content=review_prompt,
            system_content="You are a code reviewer. Be specific and constructive.",
            temperature=0,
            max_tokens=800,
        )

    async def run(
        self,
        query:          str,
        context:        dict[str, Any],
        memory_context: str = "",
    ) -> WorkerResult:
        start = time.monotonic()

        # ── Determine task type ────────────────────────────────────────────
        q_lower = query.lower()
        is_test_gen  = any(w in q_lower for w in ["test", "unittest", "pytest"])
        is_review    = any(w in q_lower for w in ["review", "audit", "check"])
        is_debug     = any(w in q_lower for w in ["debug", "fix", "error", "bug"])
        is_explain   = any(w in q_lower for w in ["explain", "what does", "how does"])

        # ── Generate code / explanation ────────────────────────────────────
        full_response, code = await self._generate_code(query, memory_context)

        execution_result = None
        review_result    = None

        # ── Execute if code was generated ──────────────────────────────────
        if code and not is_review and not is_explain:
            try:
                output, error = await asyncio.wait_for(
                    asyncio.to_thread(_run_sandboxed, code),
                    timeout=EXEC_TIMEOUT_SECONDS,
                )
                if error:
                    execution_result = f"⚠️ Execution error:\n{error}"
                    # Self-fix: ask LLM to fix the error
                    fix_prompt = (
                        f"This code produced an error:\n```python\n{code}\n```\n"
                        f"Error:\n{error}\n\nFix the code."
                    )
                    fixed_response, fixed_code = await self._generate_code(fix_prompt)
                    if fixed_code:
                        output2, error2 = await asyncio.wait_for(
                            asyncio.to_thread(_run_sandboxed, fixed_code),
                            timeout=EXEC_TIMEOUT_SECONDS,
                        )
                        if not error2:
                            full_response    = fixed_response
                            code             = fixed_code
                            execution_result = f"✅ Fixed and executed:\n{output2}"
                        else:
                            execution_result += f"\n\nAttempted fix also failed:\n{error2}"
                elif output:
                    execution_result = f"✅ Execution output:\n{output}"
                else:
                    execution_result = "✅ Code executed successfully (no output)"
            except asyncio.TimeoutError:
                execution_result = f"⏱️ Execution timed out after {EXEC_TIMEOUT_SECONDS}s"

        # ── Code review if requested or always for complex code ─────────────
        if code and (is_review or len(code) > 200):
            review_result = await self._review_code(code)

        # ── Assemble final content ─────────────────────────────────────────
        content_parts = [full_response]
        if execution_result:
            content_parts.append(f"\n---\n**Execution Result:**\n{execution_result}")
        if review_result:
            content_parts.append(f"\n---\n**Code Review:**\n{review_result}")

        final_content = "\n".join(content_parts)

        return WorkerResult(
            worker_name="code_agent",
            content=final_content,
            confidence=0.90,
            metadata={
                "had_execution": execution_result is not None,
                "had_review":    review_result is not None,
                "code_length":   len(code),
                "task_type":     (
                    "test_gen"  if is_test_gen else
                    "review"    if is_review   else
                    "debug"     if is_debug    else
                    "explain"   if is_explain  else
                    "generate"
                ),
            },
            latency_ms=(time.monotonic() - start) * 1000,
        )