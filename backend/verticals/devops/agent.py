# backend/verticals/devops/agent.py
"""
DevOps Vertical Agent.
Combines GitHub, Jira, Docker, Prometheus into one workflow.
"""
import time
import logging
import re
from typing import Any

from backend.verticals.base               import BaseVerticalAgent, VerticalResult
from backend.verticals.devops.tools       import github_tool, docker_tool, prometheus_tool, jira_tool

logger = logging.getLogger(__name__)


class DevOpsAgent(BaseVerticalAgent):
    vertical_name = "devops"
    description   = (
        "Expert DevOps engineer. Debugs builds, analyses logs, "
        "fetches CI/CD status, creates Jira tickets, checks service health."
    )

    @property
    def system_prompt(self) -> str:
        return """You are a Senior DevOps Engineer AI assistant.

You have access to:
- GitHub: commits, PRs, workflow runs, issues
- Docker: container logs, stats, container list
- Prometheus: service metrics, error rates, latency, alerts
- Jira: create tickets, search sprint issues

Your workflow for debugging:
1. Identify the failing component from the query
2. Fetch recent commits (did something just change?)
3. Check CI/CD status (did a workflow fail?)
4. Pull container logs (what errors appear?)
5. Check Prometheus metrics (are error rates elevated?)
6. Correlate findings → root cause
7. Suggest fix + optionally create Jira ticket

Always provide:
- Specific error messages from logs
- Time correlation (when did it start failing?)
- Likely root cause
- Recommended next action"""

    async def run(
        self,
        query:          str,
        context:        dict[str, Any],
        memory_context: str = "",
    ) -> VerticalResult:
        start   = time.monotonic()
        q_lower = query.lower()

        # Extract repo and service hints from query
        repo_match    = re.search(r'(?:repo|repository|github\.com/)([\w-]+/[\w-]+)', query, re.I)
        repo          = repo_match.group(1) if repo_match else context.get("default_repo", "")

        service_match = re.search(r'(?:service|container|pod)\s+([\w-]+)', query, re.I)
        service       = service_match.group(1) if service_match else context.get("default_service", "")

        parts        = []
        sources      = []
        is_create_ticket = any(w in q_lower for w in ["create ticket", "create issue", "open ticket", "jira"])
        is_debug     = any(w in q_lower for w in ["debug", "error", "fail", "crash", "why", "issue"])
        is_pr_review = any(w in q_lower for w in ["pr", "pull request", "review", "pending"])
        is_ci        = any(w in q_lower for w in ["ci", "cd", "build", "pipeline", "workflow"])

        # ── GitHub data ────────────────────────────────────────────────────
        if repo and (is_debug or is_ci or is_pr_review):
            if is_ci or is_debug:
                runs = await github_tool.get_workflow_runs(repo, limit=5)
                if runs:
                    run_lines = [
                        f"  [{r['conclusion'] or r['status']}] {r['name']} "
                        f"on {r['branch']} (commit {r['commit']}) — {r['started']}"
                        for r in runs
                    ]
                    parts.append("**CI/CD Workflow Runs:**\n" + "\n".join(run_lines))
                    sources.append(f"https://github.com/{repo}/actions")

                commits = await github_tool.get_recent_commits(repo, limit=5)
                if commits:
                    commit_lines = [
                        f"  [{c['sha']}] {c['message'][:60]} — {c['author']} ({c['date'][:10]})"
                        for c in commits
                    ]
                    parts.append("**Recent Commits:**\n" + "\n".join(commit_lines))

            if is_pr_review:
                prs = await github_tool.get_pull_requests(repo, state="open")
                if prs:
                    pr_lines = [
                        f"  #{p['number']} {p['title'][:60]} by {p['author']} "
                        f"{'[DRAFT]' if p['draft'] else ''}"
                        for p in prs
                    ]
                    parts.append(f"**Open PRs ({len(prs)}):**\n" + "\n".join(pr_lines))

        # ── Docker logs ─────────────────────────────────────────────────────
        if service and is_debug:
            log_data = await docker_tool.get_container_logs(service, tail=100)
            if log_data.get("errors"):
                err_lines = "\n".join(log_data["errors"][:10])
                parts.append(f"**Container Errors ({service}):**\n```\n{err_lines}\n```")
            if log_data.get("recent_logs"):
                parts.append(
                    f"**Recent Logs ({service}, last 20 lines):**\n"
                    f"```\n{chr(10).join(log_data['recent_logs'].splitlines()[-20:])}\n```"
                )

            stats = await docker_tool.get_container_stats(service)
            if not stats.get("error"):
                parts.append(
                    f"**Container Stats ({service}):** "
                    f"CPU: {stats.get('cpu_pct','?')} | "
                    f"Memory: {stats.get('memory','?')}"
                )

        # ── Prometheus metrics ──────────────────────────────────────────────
        if service and is_debug:
            health = await prometheus_tool.get_service_health(service)
            m      = health.get("metrics", {})
            parts.append(
                f"**Service Health ({service}):** {health['health'].upper()}\n"
                f"  Error rate: {m.get('error_rate') or 'N/A'} | "
                f"p95 latency: {m.get('p95_latency') or 'N/A'}s | "
                f"Availability: {m.get('availability') or 'N/A'}"
            )

            alerts = await prometheus_tool.get_recent_alerts()
            if alerts:
                alert_lines = [
                    f"  🔴 [{a['severity']}] {a['name']}: {a['summary']}"
                    for a in alerts[:5]
                ]
                parts.append("**Active Alerts:**\n" + "\n".join(alert_lines))

        # ── Jira ticket creation ────────────────────────────────────────────
        jira_result = None
        if is_create_ticket and context.get("jira_project"):
            jira_result = await jira_tool.create_issue(
                project_key=context["jira_project"],
                summary=query[:100],
                description="\n".join(parts) if parts else query,
                issue_type="Bug" if is_debug else "Task",
            )

        # ── Synthesise with LLM ─────────────────────────────────────────────
        raw_data = "\n\n".join(parts) if parts else "No relevant DevOps data fetched."
        system   = self.system_prompt + (f"\n{memory_context}" if memory_context else "")
        synthesis = await self._call_llm(
            user_content=(
                f"DevOps query: {query}\n\n"
                f"Data collected:\n{raw_data}\n\n"
                f"Provide root cause analysis and recommended fix."
            ),
            system_content=system,
            temperature=0.1,
        )

        if jira_result and jira_result.get("created"):
            synthesis += f"\n\n✅ Jira ticket created: [{jira_result['issue_key']}]({jira_result['url']})"

        return VerticalResult(
            vertical="devops",
            content=synthesis,
            sources=sources,
            metadata={
                "repo":    repo,
                "service": service,
                "jira":    jira_result,
            },
            latency_ms=(time.monotonic() - start) * 1000,
        )