"""Client Management — emails, queries, proposals, overdue collection, Tally export."""
from .._impl import (
    draft_client_email,
    answer_client_query,
    generate_client_proposal,
    generate_overdue_collection,
    analyze_tally_export,
)
__all__ = [
    "draft_client_email","answer_client_query","generate_client_proposal",
    "generate_overdue_collection","analyze_tally_export",
]
