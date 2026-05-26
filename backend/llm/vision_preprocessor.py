import base64
import io
import logging
from enum import Enum
from typing import Optional
from PIL import Image

logger = logging.getLogger(__name__)

MAX_IMAGE_BYTES   = 20 * 1024 * 1024
MAX_DIMENSION     = 2048
SUPPORTED_FORMATS = {"JPEG", "PNG", "GIF", "WEBP"}


class VisionDetail(str, Enum):
    LOW  = "low"
    HIGH = "high"
    AUTO = "auto"


class ImageProcessingError(ValueError):
    pass


def _detect_detail_level(query: str) -> VisionDetail:
    high_keywords = {
        "text", "read", "ocr", "extract", "table", "chart",
        "graph", "code", "screenshot", "diagram", "label",
        "number", "value", "data", "write", "word", "letter",
    }
    if set(query.lower().split()) & high_keywords:
        return VisionDetail.HIGH
    return VisionDetail.LOW


def validate_and_encode(
    image_bytes: bytes,
    query: str = "",
    force_detail: Optional[VisionDetail] = None,
) -> dict:
    if len(image_bytes) > MAX_IMAGE_BYTES:
        raise ImageProcessingError(
            f"Image too large: {len(image_bytes)//1024//1024}MB "
            f"(max {MAX_IMAGE_BYTES//1024//1024}MB)"
        )

    # Open once to capture format BEFORE verify() invalidates the object
    try:
        img = Image.open(io.BytesIO(image_bytes))
        detected_format = img.format  # capture here — verify() clears it
    except Exception as e:
        raise ImageProcessingError(f"Cannot open image: {e}")

    # Verify integrity
    try:
        img.verify()
    except Exception as e:
        raise ImageProcessingError(f"Corrupt or invalid image: {e}")

    if detected_format not in SUPPORTED_FORMATS:
        raise ImageProcessingError(
            f"Unsupported format: {detected_format}. "
            f"Use one of: {', '.join(SUPPORTED_FORMATS)}"
        )

    # Re-open after verify (verify() invalidates the object)
    img = Image.open(io.BytesIO(image_bytes))

    orig_width, orig_height = img.size

    if max(img.size) > MAX_DIMENSION:
        img.thumbnail((MAX_DIMENSION, MAX_DIMENSION), Image.LANCZOS)
        logger.info(f"Resized image: {orig_width}×{orig_height} → {img.size}")

    # FIXED: Convert RGBA/LA/P to RGB — handle all alpha modes correctly
    if img.mode in ("RGBA", "LA", "P"):
        if img.mode == "P":
            img = img.convert("RGBA")
        elif img.mode == "LA":
            img = img.convert("RGBA")
        background = Image.new("RGB", img.size, (255, 255, 255))
        background.paste(img, mask=img.split()[3])  # index 3 = alpha for RGBA
        img = background

    buffer = io.BytesIO()
    fmt = detected_format if detected_format in ("JPEG", "PNG", "GIF", "WEBP") else "JPEG"
    img.save(buffer, format=fmt, quality=92)
    processed_bytes = buffer.getvalue()

    b64_data = base64.b64encode(processed_bytes).decode("utf-8")
    media_type = f"image/{fmt.lower()}"
    detail = force_detail or _detect_detail_level(query)

    return {
        "base64_data": b64_data,
        "media_type":  media_type,
        "detail":      detail.value,
        "width":       img.size[0],
        "height":      img.size[1],
        "size_bytes":  len(processed_bytes),
    }


def encode_from_base64(
    b64_string: str,
    query: str = "",
    force_detail: Optional[VisionDetail] = None,
) -> dict:
    try:
        image_bytes = base64.b64decode(b64_string)
    except Exception as e:
        raise ImageProcessingError(f"Invalid base64 data: {e}")
    return validate_and_encode(image_bytes, query, force_detail)