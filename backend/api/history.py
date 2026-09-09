"""History API — view and delete saved AI outputs."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from backend.api.auth import verify_token
from backend.db import history as hist_db

router = APIRouter(prefix="/history", tags=["history"])


class DeleteResponse(BaseModel):
    deleted: bool
    id: int


@router.get("", summary="Get content history for the logged-in user")
async def get_history(
    vertical: str | None = Query(None, description="Filter by vertical: social | ca | cs"),
    limit:    int        = Query(20, ge=1, le=100),
    token:    dict       = Depends(verify_token),
):
    user_id = token.get("sub", "")
    items = hist_db.get_history(user_id=user_id, vertical=vertical, limit=limit)
    return {"user_id": user_id, "count": len(items), "items": items}


@router.delete("/{item_id}", response_model=DeleteResponse, summary="Delete a history item")
async def delete_history_item(
    item_id: int,
    token:   dict = Depends(verify_token),
):
    user_id = token.get("sub", "")
    deleted = hist_db.delete_item(user_id=user_id, item_id=item_id)
    return DeleteResponse(deleted=deleted, id=item_id)
