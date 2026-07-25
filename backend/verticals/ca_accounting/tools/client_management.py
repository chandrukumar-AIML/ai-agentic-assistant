"""Client Management — emails, queries, proposals, overdue collection, Tally export."""
from .._impl import (
    analyze_tally_export,
    answer_client_query,
    draft_client_email,
    generate_client_proposal,
    generate_overdue_collection,
)

__all__ = [
    "draft_client_email","answer_client_query","generate_client_proposal",
    "generate_overdue_collection","analyze_tally_export",
]
