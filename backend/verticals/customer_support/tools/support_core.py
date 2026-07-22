"""Core support tools — FAQ, complaint handling, ticket summary, KB answer, response templates."""
from .._impl import (
    faq_bot,
    handle_complaint,
    summarize_ticket,
    knowledge_base_answer,
    generate_response_template,
)

__all__ = [
    "faq_bot",
    "handle_complaint",
    "summarize_ticket",
    "knowledge_base_answer",
    "generate_response_template",
]
