"""CA Accounting constants — TDS sections, GST rates, CII table, deadline data."""
from __future__ import annotations

# ── TDS Sections (Finance Act 2025) ──────────────────────────────────────────
TDS_SECTIONS: dict[str, dict] = {
    "192":   {"description": "Salary",                        "rate_general": "slab", "threshold": 250000},
    "194":   {"description": "Dividend",                      "rate_general": 10.0,   "threshold": 5000},
    "194A":  {"description": "Interest (Bank FD)",            "rate_general": 10.0,   "threshold": 50000},
    "194B":  {"description": "Lottery/Crossword winnings",    "rate_general": 30.0,   "threshold": 10000},
    "194C":  {"description": "Contractor payments",           "rate_general": 1.0,    "threshold": 30000},
    "194D":  {"description": "Insurance commission",          "rate_general": 5.0,    "threshold": 15000},
    "194H":  {"description": "Commission / brokerage",        "rate_general": 5.0,    "threshold": 15000},
    "194I":  {"description": "Rent",                          "rate_general": 10.0,   "threshold": 240000},
    "194J":  {"description": "Professional / technical fees", "rate_general": 10.0,   "threshold": 30000},
    "194LA": {"description": "Compulsory acquisition",        "rate_general": 10.0,   "threshold": 250000},
    "194Q":  {"description": "Purchase of goods",             "rate_general": 0.1,    "threshold": 5000000},
    "206C":  {"description": "TCS on sale of goods",          "rate_general": 0.1,    "threshold": 5000000},
}

# ── GST Rates ─────────────────────────────────────────────────────────────────
GST_RATES = [0, 0.1, 0.25, 1, 1.5, 3, 5, 6, 7.5, 12, 18, 28]

# ── Cost Inflation Index ──────────────────────────────────────────────────────
CII_TABLE: dict[int, int] = {
    2001: 100, 2002: 105, 2003: 109, 2004: 113, 2005: 117,
    2006: 122, 2007: 129, 2008: 137, 2009: 148, 2010: 167,
    2011: 184, 2012: 200, 2013: 220, 2014: 240, 2015: 259,
    2016: 264, 2017: 272, 2018: 280, 2019: 289, 2020: 301,
    2021: 317, 2022: 331, 2023: 348, 2024: 363, 2025: 376,
}

# ── GSTR Filing Deadlines ────────────────────────────────────────────────────
GSTR_DEADLINES: dict[str, dict] = {
    "GSTR-1":  {"frequency": "monthly",   "due": "11th of next month", "penalty_per_day": 50},
    "GSTR-3B": {"frequency": "monthly",   "due": "20th of next month", "penalty_per_day": 50},
    "GSTR-9":  {"frequency": "annual",    "due": "31 Dec",             "penalty_per_day": 200},
    "GSTR-9C": {"frequency": "annual",    "due": "31 Dec",             "penalty_per_day": 200},
    "CMP-08":  {"frequency": "quarterly", "due": "18th of next month", "penalty_per_day": 50},
    "GSTR-4":  {"frequency": "annual",    "due": "30 Apr",             "penalty_per_day": 50},
}

# ── ITR Forms ─────────────────────────────────────────────────────────────────
ITR_FORMS: dict[str, dict] = {
    "ITR-1 (Sahaj)":  {"for": "Salaried, one house, other income < 5000",         "limit": "Income <= 50 lakh"},
    "ITR-2":          {"for": "Capital gains, multiple properties, foreign assets", "limit": "No limit"},
    "ITR-3":          {"for": "Business or profession income",                      "limit": "No limit"},
    "ITR-4 (Sugam)":  {"for": "Presumptive taxation 44AD/44ADA/44AE",              "limit": "Turnover <= 2 crore"},
    "ITR-5":          {"for": "Partnership firms, LLPs, AOPs",                     "limit": "No limit"},
    "ITR-6":          {"for": "Companies",                                          "limit": "No limit"},
    "ITR-7":          {"for": "Trusts, political parties (Sec 139 4A-4F)",          "limit": "No limit"},
}

# ── 80C Instruments ───────────────────────────────────────────────────────────
INSTRUMENTS_80C: dict[str, dict] = {
    "ELSS":          {"lock_in": "3 years",   "return": "12-15%",          "risk": "High"},
    "PPF":           {"lock_in": "15 years",  "return": "7.1%",            "risk": "Nil"},
    "EPF":           {"lock_in": "retirement","return": "8.25%",           "risk": "Nil"},
    "NPS_80CCD1B":   {"lock_in": "retirement","return": "8-10%",           "risk": "Medium", "extra_limit": 50000},
    "NSC":           {"lock_in": "5 years",   "return": "7.7%",            "risk": "Nil"},
    "LIC_premium":   {"lock_in": "policy",    "return": "4-6%",            "risk": "Low"},
    "Home_principal":{"lock_in": "5 years",   "return": "n/a",             "risk": "n/a"},
    "FD_5yr":        {"lock_in": "5 years",   "return": "6.5-7.5%",        "risk": "Nil"},
}

# ── State GST Codes ───────────────────────────────────────────────────────────
STATE_GST_CODES: dict[str, str] = {
    "07": "Delhi", "27": "Maharashtra", "29": "Karnataka",
    "33": "Tamil Nadu", "32": "Kerala", "36": "Telangana",
    "37": "Andhra Pradesh", "24": "Gujarat", "09": "Uttar Pradesh",
    "19": "West Bengal", "06": "Haryana", "03": "Punjab",
}

# ── Supported languages ───────────────────────────────────────────────────────
SUPPORTED_LANGUAGES = {"en": "English", "ta": "Tamil", "hi": "Hindi"}
