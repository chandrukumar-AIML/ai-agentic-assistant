"""Policy & documentation tools — SLA policy, returns policy, review responses, training manual, chatbot script."""
from .._impl import (
    generate_sla_policy,
    generate_returns_policy,
    generate_review_response_kit,
    generate_agent_training_manual,
    generate_chatbot_script,
)

__all__ = [
    "generate_sla_policy",
    "generate_returns_policy",
    "generate_review_response_kit",
    "generate_agent_training_manual",
    "generate_chatbot_script",
]
