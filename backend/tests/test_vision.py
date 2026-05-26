"""
Tests for backend.llm.vision_preprocessor:
  - Valid JPEG bytes encode successfully
  - Image > 20MB raises ImageProcessingError
  - Corrupt bytes raise ImageProcessingError
  - RGBA image is converted to RGB
  - Query containing "text" keyword returns HIGH detail level
  - Oversized image (> 2048px) gets resized to <= 2048px
"""
import io
import pytest
from unittest.mock import patch, MagicMock
from PIL import Image


# ---------------------------------------------------------------------------
# Fixtures — real in-memory images (no disk I/O, no network)
# ---------------------------------------------------------------------------

def _make_jpeg_bytes(width: int = 100, height: int = 100) -> bytes:
    """Create a minimal valid JPEG image in memory."""
    buf = io.BytesIO()
    img = Image.new("RGB", (width, height), color=(128, 64, 32))
    img.save(buf, format="JPEG")
    return buf.getvalue()


def _make_png_bytes(width: int = 100, height: int = 100, mode: str = "RGB") -> bytes:
    """Create a minimal valid PNG image in memory."""
    buf = io.BytesIO()
    img = Image.new(mode, (width, height), color=(200, 100, 50) if mode == "RGB" else (200, 100, 50, 200))
    img.save(buf, format="PNG")
    return buf.getvalue()


def _make_rgba_png_bytes(width: int = 50, height: int = 50) -> bytes:
    """Create a valid RGBA PNG image."""
    buf = io.BytesIO()
    img = Image.new("RGBA", (width, height), color=(128, 64, 32, 180))
    img.save(buf, format="PNG")
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestValidateAndEncode:
    """Tests for backend.llm.vision_preprocessor.validate_and_encode()"""

    def test_valid_jpeg_encodes_successfully(self):
        """A valid JPEG must be encoded without raising."""
        from backend.llm.vision_preprocessor import validate_and_encode
        jpeg_bytes = _make_jpeg_bytes()
        result = validate_and_encode(jpeg_bytes, query="what is this?")

        assert "base64_data" in result
        assert "media_type" in result
        assert result["media_type"] == "image/jpeg"
        assert len(result["base64_data"]) > 0

    def test_valid_jpeg_result_has_required_keys(self):
        """validate_and_encode() result dict must contain all expected keys."""
        from backend.llm.vision_preprocessor import validate_and_encode
        result = validate_and_encode(_make_jpeg_bytes())
        for key in ("base64_data", "media_type", "detail", "width", "height", "size_bytes"):
            assert key in result, f"Missing key: {key}"

    def test_image_over_20mb_raises_error(self):
        """Image larger than 20MB must raise ImageProcessingError immediately."""
        from backend.llm.vision_preprocessor import validate_and_encode, ImageProcessingError
        oversized = b"\x00" * (21 * 1024 * 1024)
        with pytest.raises(ImageProcessingError, match="too large"):
            validate_and_encode(oversized)

    def test_corrupt_bytes_raise_error(self):
        """Non-image bytes must raise ImageProcessingError."""
        from backend.llm.vision_preprocessor import validate_and_encode, ImageProcessingError
        corrupt = b"this is definitely not an image" * 10
        with pytest.raises(ImageProcessingError):
            validate_and_encode(corrupt)

    def test_rgba_image_converted_to_rgb(self):
        """An RGBA PNG must be composited onto white and saved as a non-RGBA image."""
        from backend.llm.vision_preprocessor import validate_and_encode
        rgba_bytes = _make_rgba_png_bytes()
        result = validate_and_encode(rgba_bytes, query="show me this")

        # Decode the result and verify mode is RGB (no alpha channel)
        import base64
        decoded = base64.b64decode(result["base64_data"])
        img = Image.open(io.BytesIO(decoded))
        assert img.mode == "RGB", f"Expected RGB mode after RGBA conversion, got {img.mode}"

    def test_text_keyword_in_query_returns_high_detail(self):
        """
        A query containing 'text' must trigger HIGH detail level because
        OCR / text reading requires high resolution.
        """
        from backend.llm.vision_preprocessor import validate_and_encode, VisionDetail
        result = validate_and_encode(_make_jpeg_bytes(), query="please read the text in this image")
        assert result["detail"] == VisionDetail.HIGH.value

    def test_non_text_query_returns_low_detail(self):
        """A generic query without detail keywords must default to LOW detail."""
        from backend.llm.vision_preprocessor import validate_and_encode, VisionDetail
        result = validate_and_encode(_make_jpeg_bytes(), query="what is in this picture?")
        assert result["detail"] == VisionDetail.LOW.value

    def test_oversized_image_resized_to_max_dimension(self):
        """An image larger than 2048px must be resized so max(w,h) <= 2048."""
        from backend.llm.vision_preprocessor import validate_and_encode, MAX_DIMENSION

        # Create a 3000x3000 PNG — above the 2048px limit
        buf = io.BytesIO()
        img = Image.new("RGB", (3000, 3000), color=(100, 150, 200))
        img.save(buf, format="PNG")
        large_bytes = buf.getvalue()

        result = validate_and_encode(large_bytes)
        assert result["width"]  <= MAX_DIMENSION, f"Width {result['width']} > {MAX_DIMENSION}"
        assert result["height"] <= MAX_DIMENSION, f"Height {result['height']} > {MAX_DIMENSION}"

    def test_force_detail_overrides_query_detection(self):
        """force_detail parameter must override the auto-detected detail level."""
        from backend.llm.vision_preprocessor import validate_and_encode, VisionDetail
        # The query contains 'text' which would normally give HIGH, but we force LOW
        result = validate_and_encode(
            _make_jpeg_bytes(),
            query="read the text in this",
            force_detail=VisionDetail.LOW,
        )
        assert result["detail"] == VisionDetail.LOW.value

    def test_valid_png_encodes_successfully(self):
        """A valid PNG must also encode without raising."""
        from backend.llm.vision_preprocessor import validate_and_encode
        png_bytes = _make_png_bytes()
        result = validate_and_encode(png_bytes)
        assert result["media_type"] == "image/png"
        assert result["size_bytes"] > 0
