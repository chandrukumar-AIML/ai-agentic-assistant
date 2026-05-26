# backend/verticals/devops/tools/jira_tool.py
"""
Jira integration for DevOps agent.
Creates tickets, fetches sprint status, updates issues.
"""
import logging
import httpx
from backend.config import get_settings

logger   = logging.getLogger(__name__)
settings = get_settings()

_client = httpx.AsyncClient(
    base_url=getattr(settings, "jira_url", "https://your-org.atlassian.net"),
    auth=(
        getattr(settings, "jira_email", ""),
        getattr(settings, "jira_api_token", ""),
    ),
    headers={"Content-Type": "application/json"},
    timeout=15.0,
)


async def create_issue(
    project_key:  str,
    summary:      str,
    description:  str,
    issue_type:   str = "Bug",
    priority:     str = "Medium",
    labels:       list[str] | None = None,
) -> dict:
    """Create a Jira issue."""
    payload = {
        "fields": {
            "project":   {"key": project_key},
            "summary":   summary[:255],
            "description": {
                "type":    "doc",
                "version": 1,
                "content": [{"type": "paragraph", "content": [{"type": "text", "text": description[:5000]}]}],
            },
            "issuetype": {"name": issue_type},
            "priority":  {"name": priority},
            "labels":    labels or [],
        }
    }
    try:
        r = await _client.post("/rest/api/3/issue", json=payload)
        r.raise_for_status()
        data = r.json()
        jira_base = getattr(settings, "jira_url", "https://your-org.atlassian.net")  # FIXED: AttributeError if jira_url missing
        return {
            "created":   True,
            "issue_key": data["key"],
            "url":       f"{jira_base}/browse/{data['key']}",
            "id":        data["id"],
        }
    except Exception as e:
        logger.error(f"Jira create issue failed: {e}")
        return {"created": False, "error": str(e)}


async def search_issues(
    jql:   str,
    limit: int = 10,
) -> list[dict]:
    """Search Jira issues with JQL."""
    try:
        r = await _client.post(
            "/rest/api/3/issue/search",
            json={"jql": jql, "maxResults": limit, "fields": ["summary", "status", "assignee", "priority", "created"]},
        )
        r.raise_for_status()
        issues = r.json().get("issues", [])
        return [
            {
                "key":      i["key"],
                "summary":  i["fields"]["summary"][:80],
                "status":   i["fields"]["status"]["name"],
                "assignee": (i["fields"].get("assignee") or {}).get("displayName", "Unassigned"),
                "priority": i["fields"]["priority"]["name"],
                "created":  i["fields"]["created"],
                "url":      f"{getattr(settings, 'jira_url', 'https://your-org.atlassian.net')}/browse/{i['key']}",  # FIXED: AttributeError if jira_url missing
            }
            for i in issues
        ]
    except Exception as e:
        logger.error(f"Jira search failed: {e}")
        return []


async def get_sprint_issues(project_key: str) -> dict:
    """Get all issues in the current active sprint."""
    jql    = f"project = {project_key} AND sprint in openSprints()"
    issues = await search_issues(jql, limit=50)

    # Summarise by status
    status_count: dict[str, int] = {}
    for i in issues:
        status = i["status"]
        status_count[status] = status_count.get(status, 0) + 1

    return {
        "project":      project_key,
        "total":        len(issues),
        "by_status":    status_count,
        "issues":       issues,
    }