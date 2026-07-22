"""TDS & Payroll tools — TDS calculator, payroll, Form 16, salary slips, tracker."""
from .._impl import (
    calculate_tds,
    calculate_payroll,
    generate_tds_compliance_tracker,
    generate_form16,
    generate_salary_slip,
)
__all__ = [
    "calculate_tds","calculate_payroll","generate_tds_compliance_tracker",
    "generate_form16","generate_salary_slip",
]
