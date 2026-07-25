"""CA Accounting tools — public API. Import from here, not from _impl directly."""
from .client_management import (
    analyze_tally_export,
    answer_client_query,
    draft_client_email,
    generate_client_proposal,
    generate_overdue_collection,
)
from .compliance_deadlines import (
    generate_advance_tax,
    generate_client_compliance_status,
    generate_itr_checklist,
    get_compliance_calendar,
    get_compliance_deadlines,
)
from .documents import (
    generate_directors_report,
    generate_mca_roc_calendar,
    generate_partnership_deed,
    generate_startup_registration_guide,
)
from .financial_reports import (
    calculate_business_valuation,
    calculate_cash_flow_forecast,
    generate_balance_sheet,
    generate_depreciation_calc,
    generate_pl_statement,
)
from .gst import (
    advise_gst_reconciliation,
    answer_gst_query,
    draft_gst_notice_reply,
    generate_gst_invoice,
    generate_gstr_assistant,
    prepare_gstr_filing,
)
from .invoicing import draft_invoice
from .itr_tax_planning import (
    advise_itr,
    generate_capital_gains_calculator,
    generate_hra_80c_planner,
    optimize_tax_planning,
)
from .misc import (
    calculate_msme_loan_eligibility,
    generate_audit_checklist,
    generate_ca_social_post,
    generate_rent_receipts,
)
from .tds_payroll import (
    calculate_payroll,
    calculate_tds,
    generate_form16,
    generate_salary_slip,
    generate_tds_compliance_tracker,
)

__all__ = [
    "answer_gst_query", "advise_gst_reconciliation", "prepare_gstr_filing",
    "generate_gst_invoice", "generate_gstr_assistant", "draft_gst_notice_reply",
    "calculate_tds", "calculate_payroll", "generate_tds_compliance_tracker",
    "generate_form16", "generate_salary_slip",
    "draft_invoice",
    "get_compliance_deadlines", "get_compliance_calendar", "generate_advance_tax",
    "generate_client_compliance_status", "generate_itr_checklist",
    "advise_itr", "optimize_tax_planning", "generate_capital_gains_calculator",
    "generate_hra_80c_planner",
    "generate_balance_sheet", "calculate_cash_flow_forecast", "generate_pl_statement",
    "calculate_business_valuation", "generate_depreciation_calc",
    "draft_client_email", "answer_client_query", "generate_client_proposal",
    "generate_overdue_collection", "analyze_tally_export",
    "generate_partnership_deed", "generate_startup_registration_guide",
    "generate_directors_report", "generate_mca_roc_calendar",
    "generate_audit_checklist", "generate_rent_receipts",
    "calculate_msme_loan_eligibility", "generate_ca_social_post",
]
