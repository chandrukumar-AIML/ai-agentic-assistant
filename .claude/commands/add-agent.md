# /add-agent — Add New Agent Vertical

Act as **Engineering Manager + Backend Engineer + Frontend Engineer** from AGENTS.md.

Add a complete new agent vertical following the SM/CS/CA pattern.

## Inputs needed

Ask the user for:
1. Agent name (e.g. "HR", "Legal", "Sales")
2. Short description (one line)
3. Target persona from PERSONAS.md (which Indian SMB user?)
4. List of 10–15 initial features/actions

## Step 1 — Product Lead check

Before building, verify:
- Which PERSONAS.md user needs this?
- Does it fit ROADMAP.md Q3/Q4 2026?
- Minimum 10 features that would be used weekly?

## Step 2 — Backend (5 files)

```
backend/verticals/{name}/
  __init__.py      ← empty
  router.py        ← POST /api/{name}/action
  _impl.py         ← dispatch() + all handlers + DEMO_RESPONSES
  prompts.py       ← all prompt templates
  models.py        ← ActionRequest, ActionResponse
```

Template `router.py`:
```python
from fastapi import APIRouter, Depends
from .._impl import dispatch
from ..models import ActionRequest
from ...auth import get_current_user

router = APIRouter()

@router.post("/action")
async def action(req: ActionRequest, user=Depends(get_current_user)):
    return await dispatch(req.action, req.payload, req.language, user)
```

Template `_impl.py` dispatch:
```python
async def dispatch(action: str, payload: dict, language: str, user=None) -> dict:
    handlers = {
        "feature_one": feature_one,
        "feature_two": feature_two,
        # ... all actions
    }
    if os.getenv("DEMO_MODE") == "true":
        return DEMO_RESPONSES.get(action, {"result": "Demo output"})
    fn = handlers.get(action)
    if not fn: raise HTTPException(404, f"Unknown action: {action}")
    return await fn(payload, language)
```

Register in `backend/main.py`:
```python
from verticals.{name}.router import router as {name}_router
app.include_router({name}_router, prefix="/api/{name}", tags=["{Name}"])
```

## Step 3 — Frontend (1 file)

`frontend/src/pages/{Name}Page.tsx`:
- Import: `PageShell, Card, Btn, Input, Select, ResultBox, Tabs, TwoCol, useApi, SectionHead` from `ui.tsx`
- Import: `WorkspaceSetup, WorkspaceBar` from components
- Import: `getWorkspace, saveWorkspace, clearWorkspace` from `lib/workspace.ts`
- Add workspace type to `lib/workspace.ts`
- Add tabs with groups (max 6-8 per group)
- Agent accent color (pick from palette)

Update these files:
- `src/App.tsx` → add to `PageId` type + `makePAGE_MAP`
- `src/components/Sidebar.tsx` → add to `NAV`, `ICONS`, `AGENT_ACCENT`
- `src/pages/DashboardPage.tsx` → add to `AGENTS` array

## Step 4 — QA

Create `qa/qa_{name}_full.py` — test every action.

## Step 5 — Docs

- Add to `CHANGELOG.md`
- Add to `ROADMAP.md` as shipped
- Update `README.md` feature count
