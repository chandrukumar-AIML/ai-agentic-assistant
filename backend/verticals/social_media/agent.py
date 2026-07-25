"""Social Media Agent — thin dispatcher. All business logic lives in tools/."""
from ._impl import social_agent  # dispatcher lives in _impl until fully migrated

__all__ = ["social_agent"]
