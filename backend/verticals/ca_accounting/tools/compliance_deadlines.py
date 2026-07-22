"""Compliance & Deadlines — GST/ITR/TDS calendar, advance tax, status, ITR checklist."""
from .._impl import (
    get_compliance_deadlines,
    get_compliance_calendar,
    generate_advance_tax,
    generate_client_compliance_status,
    generate_itr_checklist,
)
__all__ = [
    "get_compliance_deadlines","get_compliance_calendar","generate_advance_tax",
    "generate_client_compliance_status","generate_itr_checklist",
]
