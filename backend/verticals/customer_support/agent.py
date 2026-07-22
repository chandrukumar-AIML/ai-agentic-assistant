"""Customer Support Agent — thin dispatcher. All business logic lives in tools/."""
from ._impl import cs_agent

__all__ = ["cs_agent"]
