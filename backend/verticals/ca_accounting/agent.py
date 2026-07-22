"""CA Accounting Agent - thin dispatcher. All business logic lives in tools/."""
from ._impl import ca_agent

__all__ = ["ca_agent"]
