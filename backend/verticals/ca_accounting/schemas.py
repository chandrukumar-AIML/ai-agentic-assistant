"""Pydantic request/response schemas for the CA Accounting agent."""
from __future__ import annotations

from typing import Any, Dict, List

from pydantic import BaseModel


class GstQueryRequest(BaseModel):
    query: str
    business_type: str = ""
    state: str = ""
    language: str = "en"

class TdsRequest(BaseModel):
    section: str
    amount: float
    pan_available: bool = True
    language: str = "en"

class InvoiceRequest(BaseModel):
    seller_name: str
    seller_gstin: str = ""
    buyer_name: str
    buyer_gstin: str = ""
    items: List[Dict[str, Any]] = []
    supply_type: str = "intra"
    language: str = "en"

class ItrRequest(BaseModel):
    income_sources: List[str] = []
    total_income: float = 0
    has_business_income: bool = False
    has_capital_gains: bool = False
    has_foreign_assets: bool = False
    language: str = "en"

class CapitalGainsRequest(BaseModel):
    asset_type: str
    purchase_price: float
    sale_price: float
    purchase_date: str
    sale_date: str
    sale_expenses: float = 0
    improvement_cost: float = 0
    applicable_exemption: str = ""
    exemption_investment: float = 0
    language: str = "en"

class RentReceiptRequest(BaseModel):
    tenant_name: str
    landlord_name: str
    landlord_pan: str = ""
    property_address: str = ""
    monthly_rent: float
    from_month: str
    to_month: str
    from_year: int
    payment_mode: str = "Bank Transfer"
    language: str = "en"

class Hra80cRequest(BaseModel):
    employee_name: str
    basic_salary_annual: float
    hra_received_annual: float = 0
    rent_paid_annual: float = 0
    city_type: str = "metro"
    existing_80c_investments: Dict[str, float] = {}
    health_insurance_self: float = 0
    health_insurance_parents: float = 0
    home_loan_interest: float = 0
    home_loan_principal: float = 0
    education_loan_interest: float = 0
    nps_contribution: float = 0
    language: str = "en"

class AgentResponse(BaseModel):
    action: str
    status: str = "success"
    data: Dict[str, Any] = {}
