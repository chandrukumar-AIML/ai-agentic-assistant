"""Base interface for domain vertical agents."""
import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class VerticalResult:
    vertical:    str
    content:     str
    sources:     list[str]      = field(default_factory=list)
    metadata:    dict[str, Any] = field(default_factory=dict)
    latency_ms:  float          = 0.0
    error:       str | None     = None
