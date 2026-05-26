# backend/verticals/devops/tools/github_tool.py
"""
GitHub API tool for DevOps agent.
Fetches: repo info, recent commits, PRs, CI/CD status, issues.
"""
import logging
from typing import Any
import httpx
from backend.config import get_settings

logger   = logging.getLogger(__name__)
settings = get_settings()

_client = httpx.AsyncClient(
    base_url="https://api.github.com",
    headers={
        "Authorization": f"token {getattr(settings, 'github_token', '')}",
        "Accept":        "application/vnd.github.v3+json",
        "X-GitHub-Api-Version": "2022-11-28",
    },
    timeout=15.0,
)


async def get_recent_commits(repo: str, branch: str = "main", limit: int = 10) -> list[dict]:
    """Fetch recent commits for a repo."""
    try:
        r = await _client.get(f"/repos/{repo}/commits",
                              params={"sha": branch, "per_page": limit})
        r.raise_for_status()
        commits = r.json()
        return [
            {
                "sha":     c["sha"][:7],
                "message": c["commit"]["message"].split("\n")[0][:80],
                "author":  c["commit"]["author"]["name"],
                "date":    c["commit"]["author"]["date"],
                "url":     c["html_url"],
            }
            for c in commits
        ]
    except Exception as e:
        logger.error(f"GitHub commits failed: {e}")
        return []


async def get_pull_requests(
    repo:   str,
    state:  str = "open",
    limit:  int = 10,
) -> list[dict]:
    """Fetch pull requests."""
    try:
        r = await _client.get(f"/repos/{repo}/pulls",
                              params={"state": state, "per_page": limit})
        r.raise_for_status()
        prs = r.json()
        return [
            {
                "number":   pr["number"],
                "title":    pr["title"][:80],
                "author":   pr["user"]["login"],
                "state":    pr["state"],
                "created":  pr["created_at"],
                "url":      pr["html_url"],
                "draft":    pr.get("draft", False),
                "reviews":  pr.get("requested_reviewers", []),
            }
            for pr in prs
        ]
    except Exception as e:
        logger.error(f"GitHub PRs failed: {e}")
        return []


async def get_workflow_runs(repo: str, limit: int = 5) -> list[dict]:
    """Get recent GitHub Actions workflow runs (CI/CD status)."""
    try:
        r = await _client.get(f"/repos/{repo}/actions/runs",
                              params={"per_page": limit})
        r.raise_for_status()
        runs = r.json().get("workflow_runs", [])
        return [
            {
                "id":         run["id"],
                "name":       run["name"],
                "status":     run["status"],
                "conclusion": run.get("conclusion"),
                "branch":     run["head_branch"],
                "started":    run["created_at"],
                "url":        run["html_url"],
                "commit":     run["head_sha"][:7],
            }
            for run in runs
        ]
    except Exception as e:
        logger.error(f"GitHub workflow runs failed: {e}")
        return []


async def get_repo_issues(
    repo:   str,
    state:  str = "open",
    labels: str = "",
    limit:  int = 10,
) -> list[dict]:
    """Fetch repository issues."""
    try:
        params = {"state": state, "per_page": limit}
        if labels:
            params["labels"] = labels
        r = await _client.get(f"/repos/{repo}/issues", params=params)
        r.raise_for_status()
        issues = r.json()
        return [
            {
                "number":  i["number"],
                "title":   i["title"][:80],
                "author":  i["user"]["login"],
                "state":   i["state"],
                "labels":  [l["name"] for l in i.get("labels", [])],
                "created": i["created_at"],
                "url":     i["html_url"],
            }
            for i in issues
            if "pull_request" not in i   # exclude PRs from issues list
        ]
    except Exception as e:
        logger.error(f"GitHub issues failed: {e}")
        return []