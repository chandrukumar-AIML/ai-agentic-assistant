# backend/agents/planning_agent.py
"""
Planning Agent: decomposes complex tasks, creates execution plans,
monitors subtask completion, adapts on failure.
Best for: multi-step tasks, project planning, workflow design.
"""
import time
import json
import logging
from typing import Any

from backend.agent.base_agent import BaseWorkerAgent, WorkerResult
from backend.utils.text        import strip_code_fence

logger = logging.getLogger(__name__)

PLAN_PROMPT = """You are a Task Planning Agent. Break down complex tasks into clear, executable steps.

For the given task, create a structured plan:
{{
  "task_summary": "one-line summary of the overall task",
  "complexity": "simple|medium|complex",
  "estimated_steps": <number>,
  "plan": [
    {{
      "step": 1,
      "title": "short title",
      "description": "what to do",
      "worker": "research_agent|code_agent|vision_agent|memory_agent|self",
      "depends_on": [],
      "success_criteria": "how to know this step is done"
    }}
  ],
  "risks": ["potential failure point 1", "potential failure point 2"],
  "fallback": "what to do if the plan fails"
}}

Task: {task}
Context: {context}

Return ONLY valid JSON."""


class PlanningAgent(BaseWorkerAgent):
    name        = "planning_agent"
    description = (
        "Expert at breaking complex tasks into steps. Creates execution plans, "
        "assigns subtasks to right workers, monitors progress. "
        "Best for: multi-step projects, workflow design, complex orchestration."
    )

    @property
    def system_prompt(self) -> str:
        return """You are a Strategic Planning Agent specialised in task decomposition.

You break complex goals into concrete, ordered, executable steps.
Each step must:
- Have a clear success criterion
- Be assigned to the right specialist (research/code/vision/memory)
- Have explicit dependencies noted
- Be achievable in a single agent turn

You do NOT execute — you only plan. Other agents execute."""

    async def run(
        self,
        query:          str,
        context:        dict[str, Any],
        memory_context: str = "",
    ) -> WorkerResult:
        start = time.monotonic()

        context_str = json.dumps({k: str(v)[:200] for k, v in context.items()}, indent=2)

        raw = await self._call_llm(
            user_content=PLAN_PROMPT.format(task=query, context=context_str),
            system_content=self.system_prompt + (f"\n{memory_context}" if memory_context else ""),
            temperature=0.1,
            max_tokens=1000,
        )

        # Parse the plan
        try:
            plan_data = json.loads(strip_code_fence(raw))
        except json.JSONDecodeError:
            plan_data = {"task_summary": query, "plan": [], "error": "Failed to parse plan"}

        # Format for human reading
        formatted_parts = []
        if plan_data.get("task_summary"):
            formatted_parts.append(f"**Task:** {plan_data['task_summary']}")

        if plan_data.get("complexity"):
            formatted_parts.append(f"**Complexity:** {plan_data['complexity'].title()}")

        steps = plan_data.get("plan", [])
        if steps:
            formatted_parts.append("\n**Execution Plan:**")
            for step in steps:
                worker     = step.get("worker", "self")
                title      = step.get("title", "")
                desc       = step.get("description", "")
                criteria   = step.get("success_criteria", "")
                dep        = step.get("depends_on", [])
                dep_str    = f" (after step {dep})" if dep else ""

                formatted_parts.append(
                    f"\n**Step {step.get('step', '?')}: {title}**{dep_str}\n"
                    f"Agent: `{worker}`\n"
                    f"{desc}\n"
                    f"✓ Done when: {criteria}"
                )

        if plan_data.get("risks"):
            formatted_parts.append("\n**Risks:**")
            for risk in plan_data["risks"]:
                formatted_parts.append(f"⚠️ {risk}")

        if plan_data.get("fallback"):
            formatted_parts.append(f"\n**Fallback:** {plan_data['fallback']}")

        content = "\n".join(formatted_parts) or raw

        return WorkerResult(
            worker_name="planning_agent",
            content=content,
            confidence=0.85,
            metadata={
                "plan_data":  plan_data,
                "step_count": len(steps),
                "complexity": plan_data.get("complexity", "unknown"),
            },
            latency_ms=(time.monotonic() - start) * 1000,
        )