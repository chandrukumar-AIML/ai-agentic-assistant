# backend/api/output_routes.py
"""
Multi-modal Output API (Feature 7).

Endpoints:
  POST /outputs/generate   — generate PDF / PPTX / Excel / Image / Audio
  GET  /outputs/formats    — list supported formats + their payload schema
"""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from pydantic import BaseModel, Field

from backend.api.auth          import verify_token
from backend.outputs.output_generator import generate_output

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/outputs", tags=["outputs"])

VALID_FORMATS = {"pdf", "pptx", "excel", "image", "audio"}


class GenerateRequest(BaseModel):
    format:  str       = Field(..., description="pdf | pptx | excel | image | audio")
    payload: dict[str, Any] = Field(default_factory=dict)


@router.get(
    "/formats",
    summary="List supported output formats",
    response_model=dict,
)
async def list_formats(_token: dict = Depends(verify_token)):
    return {
        "formats": [
            {
                "id":          "pdf",
                "name":        "PDF Report",
                "content_type": "application/pdf",
                "payload":     {"title": "str", "content": "str", "sections": "[{heading, body}]"},
            },
            {
                "id":          "pptx",
                "name":        "PowerPoint Presentation",
                "content_type": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
                "payload":     {"title": "str", "slides": "[{title, bullets:[str], notes}]"},
            },
            {
                "id":          "excel",
                "name":        "Excel Spreadsheet",
                "content_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "payload":     {"title": "str", "sheets": "[{name, headers:[str], rows:[[values]]}]"},
            },
            {
                "id":          "image",
                "name":        "DALL-E 3 Image",
                "content_type": "image/png",
                "payload":     {"prompt": "str", "size": "1024x1024|1792x1024|1024x1792",
                               "quality": "standard|hd", "style": "natural|vivid"},
            },
            {
                "id":          "audio",
                "name":        "Text-to-Speech Audio",
                "content_type": "audio/wav",
                "payload":     {"text": "str", "language": "en|hi|ta", "speaker": "optional"},
            },
        ]
    }


@router.post(
    "/generate",
    summary="Generate multi-modal output",
    status_code=status.HTTP_200_OK,
)
async def generate_output_file(
    req:   GenerateRequest,
    token: dict = Depends(verify_token),
):
    """
    Generate a file in the requested format and return it as a binary download.
    Billing tier check: image generation requires PRO or ENTERPRISE plan.
    """
    fmt = req.format.lower()
    if fmt not in VALID_FORMATS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unsupported format: {fmt!r}. Valid: {sorted(VALID_FORMATS)}",
        )

    # Tier gating: DALL-E image & Audio require PRO+
    plan = token.get("plan_tier", "free")
    if fmt in ("image", "audio") and plan == "free":
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"'{fmt}' output requires PRO or ENTERPRISE plan. Upgrade at /billing.",
        )

    try:
        file_bytes, content_type, filename = await generate_output(fmt, req.payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    except Exception as e:
        logger.error("Output generation failed: %s", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Output generation service temporarily unavailable.")

    return Response(
        content=file_bytes,
        media_type=content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length":      str(len(file_bytes)),
            "X-Generated-By":      "AI-Agentic-Assistant-V2",
        },
    )
