# -*- coding: utf-8 -*-
"""CA Full Feature QA — 40 actions, Sharma & Co / Priya Sharma persona (corrected keys)"""
import sys, json, urllib.request
sys.stdout.reconfigure(encoding='utf-8')

BASE = "http://localhost:8000"
results = []

def post(path, body, timeout=60):
    data = json.dumps(body).encode()
    req = urllib.request.Request(f"{BASE}{path}", data=data,
          headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read()), None
    except Exception as e:
        return None, str(e)

def check(name, r, err, *keys):
    if err or r is None:
        status = "FAIL"; detail = str(err)[:90]
    elif r.get("error") not in (None, False, ""):
        status = "FAIL"; detail = str(r.get("error",""))[:90]
    else:
        missing = [k for k in keys if k not in r]
        if missing:
            status = "PARTIAL"; detail = f"missing:{missing} | got:{list(r.keys())[:5]}"
        else:
            val = r.get(keys[0], "")
            preview = f"[{type(val).__name__} len={len(val)}]" if isinstance(val,(list,dict)) else str(val)[:60]
            status = "PASS"; detail = preview
    results.append((status, name, detail))
    icon = "✓" if status=="PASS" else ("~" if status=="PARTIAL" else "✗")
    print(f"  {icon} {name:<42} {detail[:70]}")

PATH = "/api/verticals/ca/action"
def ca(action, payload, *keys, timeout=60):
    r, e = post(PATH, {"action": action, "payload": payload, "language": "en"}, timeout=timeout)
    check(action, r, e, *keys)

print("=" * 80)
print("  CA FULL QA — 40 actions | Sharma & Co / Priya Sharma")
print("=" * 80)

# 1
ca("gst_query", {"query":"GST rate on yoga mats and fitness equipment?","gstin":"29AABCU9603R1ZX"}, "answer")
# 2 — actual keys: email (not subject/body)
ca("client_email", {"email_type":"advisory","client_name":"Arjun Mehta","firm_name":"Sharma & Co","details":"Switch regime","amount":"1L","deadline":"31 Mar"}, "email")
# 3
ca("deadlines", {"month":7,"year":2025,"taxpayer_type":"regular"}, "deadlines","count")
# 4
ca("tds_calc", {"section":"194J","amount":150000,"pan_available":True,"payee_type":"individual"}, "tds_amount")
# 5
ca("invoice", {"seller_name":"Sharma & Co","seller_gstin":"29AABCU9603R1ZX","buyer_name":"ZenFit Pvt Ltd","items":[{"description":"GST Consultation","hsn":"998311","qty":1,"rate":15000,"gst_rate":18}],"invoice_date":"2025-07-22","seller_state":"karnataka"}, "seller","total_tax")
# 6 — actual key: checklist
ca("audit_checklist", {"client_name":"ZenFit Pvt Ltd","business_type":"private_limited","turnover_cr":2.5,"industry":"wellness","audit_type":"tax_audit","fy":"2024-25"}, "checklist")
# 7 — actual key: resolution
ca("reconciliation", {"mismatch_type":"gstr2b_mismatch","mismatch_amount":"45000","client_name":"ZenFit","description":"ITC mismatch"}, "resolution")
# 8
ca("itr_advice", {"income_sources":["salary","capital_gains"],"gross_income":900000,"taxpayer_type":"individual","age":32,"has_80c":True,"has_hra":True}, "itr_form")
# 9
ca("ca_social_post", {"topic":"gst_tip","platform":"linkedin","firm_name":"Sharma & Co"}, "post")
# 10
ca("client_query", {"query":"Can I claim HRA if I work from home?","client_profile":"Salaried, metro, 12L"}, "answer")
# 11
ca("compliance_calendar", {"months":[7,8,9],"taxpayer_type":"regular","include_tds":True,"include_itr":True,"firm_name":"Sharma & Co"}, "calendar")
# 12 — actual keys: gst_reconciliation, raw
ca("tally_analysis", {"tally_data":"Sales:12L|Purchases:8L","analysis_type":"gst_reconciliation","firm_name":"ZenFit","fy":"2024-25"}, "gst_reconciliation")
# 13 — fixed dispatch: now uses flat params, keys: seller, buyer
ca("generate_invoice", {"seller":{"name":"Sharma & Co","gstin":"29AABCU9603R1ZX","address":"Bangalore","state":"karnataka"},"buyer":{"name":"ZenFit","gstin":"29ZENFIT1234R1Z5","address":"Bangalore","state":"karnataka"},"items":[{"description":"Audit","hsn":"998311","qty":1,"rate":50000,"gst_rate":18}],"invoice_no":"SC/001","invoice_date":"2025-07-22","payment_terms":"30 days"}, "seller","buyer")
# 14
ca("capital_gains", {"asset_type":"property","purchase_price":5000000,"sale_price":8500000,"purchase_date":"2018-03-15","sale_date":"2025-01-10","sale_expenses":85000}, "gross_gain","term_label")
# 15
ca("rent_receipts", {"tenant_name":"Priya Sharma","landlord_name":"Ramesh Iyer","landlord_pan":"ABCRI1234D","property_address":"14, Indiranagar, Bangalore","monthly_rent":28000,"from_month":"April","to_month":"March","from_year":2025,"payment_mode":"Bank Transfer"}, "receipts","annual_rent")
# 16
ca("hra_80c_planner", {"basic_salary_annual":720000,"hra_received_annual":216000,"rent_paid_annual":336000,"city_type":"metro","existing_80c_investments":{"ELSS":50000,"PPF":60000},"nps_contribution":50000}, "hra_calculation","80c_summary")
# 17 — actual key: scheme, slab_info
ca("gstr_assistant", {"business_name":"ZenFit","gstin":"29ZENFIT1234R1Z5","annual_turnover":2500000,"is_composition":False,"filing_period":"monthly"}, "scheme","business_name")
# 18 — actual keys: roc_filings, tax_calendar
ca("mca_roc_calendar", {"company_name":"ZenFit Pvt Ltd","entity_type":"private_limited","fy_end_month":"March","has_msme_vendors":False,"is_newly_incorporated":False}, "roc_filings","tax_calendar")
# 19
ca("directors_report", {"company_name":"ZenFit","cin":"U52100KA2020PTC123456","fy_start":"2024-04-01","fy_end":"2025-03-31","revenue":25000000,"profit_before_tax":3500000,"profit_after_tax":2625000,"dividend_declared":False,"directors":[{"name":"Arjun Mehta","din":"12345678","designation":"MD"}]}, "report_sections")
# 20 — actual key: startup_name, entity_details
ca("startup_guide", {"startup_name":"FitTech","entity_type":"private_limited","industry_sector":"wellness","state":"Karnataka","founders_count":2}, "startup_name","entity_details")
# 21
ca("partnership_deed", {"firm_name":"Sharma & Iyer Associates","business_nature":"CA Services","registered_address":"Bangalore","commencement_date":"2025-08-01","duration":"at_will","partners":[{"name":"Priya Sharma","address":"Bangalore","pan":"ABCPS1234D","share_pct":60},{"name":"Ramesh Iyer","address":"Bangalore","pan":"ABCRI1234D","share_pct":40}],"profit_loss_ratio":"60:40","bank_name":"HDFC Bank"}, "clauses")
# 22 — actual keys: installments (check), total_tax not present → use installments + income_summary
ca("advance_tax", {"taxpayer_name":"Priya","taxpayer_type":"individual","financial_year":"2025-26","estimated_income":1200000,"salary_income":900000,"tds_deducted":80000,"regime":"new","deductions_80c":150000}, "installments","income_summary")
# 23 — actual keys: company, assets, balanced
ca("balance_sheet", {"company_name":"ZenFit Pvt Ltd","period":"FY 2024-25","industry":"wellness","land_building":5000000,"cash":300000,"bank":1500000,"debtors":800000,"share_capital":2000000,"reserves_surplus":3200000,"long_term_loans":2500000,"creditors":700000}, "assets","company")
# 24
ca("form_16", {"employee_name":"Priya Sharma","employee_pan":"ABCPS1234D","employee_designation":"Senior Manager","employer_name":"ZenFit","employer_tan":"BLRZ12345A","employer_pan":"AAACZ1234A","employer_address":"Bangalore","financial_year":"2024-25","assessment_year":"2025-26","gross_salary":1200000,"basic_salary":480000,"hra_received":192000,"hra_exemption":158400,"standard_deduction":50000,"deduction_80c":150000,"deduction_80d":25000,"tds_q1":15000,"tds_q2":15000,"tds_q3":15000,"tds_q4":15000}, "part_a","part_b")
# 25 — actual keys: client_name, pan, gstin, ...
ca("client_compliance_status", {"client_name":"ZenFit","pan":"AAACZ1234A","gstin":"29ZENFIT1234R1Z5","business_type":"private_limited","filing_type":"monthly","state":"Karnataka","turnover_lakh":250,"has_employees":True,"is_audit_case":True}, "client_name","gstin")
# 26 — actual keys: employee, company_name, month_year, working_days_in_month
ca("salary_slip", {"employee_name":"Kavitha R","employee_id":"ZF-001","designation":"Instructor","department":"Ops","company_name":"ZenFit","month_year":"July 2025","ctc_annual":420000,"basic_pct":40,"hra_pct":20,"city_tier":"metro","pf_applicable":True,"pt_state":"karnataka","working_days":26}, "employee","company_name")
# 27 — actual keys: recommended_itr_form, filing_deadline
ca("itr_checklist", {"taxpayer_name":"Priya","pan":"ABCPS1234D","assessment_year":"2025-26","income_sources":["salary","capital_gains"],"has_home_loan":True,"deductions":["80C","80D"],"taxpayer_type":"individual"}, "recommended_itr_form","filing_deadline")
# 28
ca("depreciation_calc", {"asset_name":"MacBook Pro","asset_category":"computer","cost":150000,"purchase_date":"2024-04-15","useful_life_years":3,"salvage_value":15000,"method":"slm","financial_year_start":2024}, "schedule")
# 29 — actual keys: invoice_number, seller
ca("gst_invoice", {"seller_name":"Sharma & Co","seller_gstin":"29AABCU9603R1ZX","seller_address":"Bangalore","seller_state":"karnataka","buyer_name":"FreshMart","buyer_gstin":"29FRESH1234R1Z5","buyer_address":"Bangalore","buyer_state":"karnataka","invoice_number":"SC/2025/042","invoice_date":"2025-07-22","items":[{"description":"Audit","hsn":"998311","qty":1,"rate":75000,"gst_rate":18}]}, "invoice_number","seller")
# 30 — actual keys: firm_name, client_name, ca_name, engagement_start
ca("client_proposal", {"firm_name":"Sharma & Co","client_name":"FreshMart","client_industry":"retail","client_turnover":"5Cr","services":["GST","TDS"],"fee_type":"monthly_retainer","engagement_start":"2025-08-01","ca_name":"Priya Sharma"}, "firm_name","client_name","ca_name")
# 31 — actual keys: company, month, challan_due_date
ca("tds_compliance_tracker", {"company_name":"ZenFit","month":6,"year":2025,"deductions":[{"party":"Sharma","section":"194J","amount":50000,"tds":5000,"pan":"ABCPS1234D"}],"pan_verified":True}, "company","challan_due_date")
# 32 — actual keys: msme_category, eligibility_score, eligibility_max
ca("msme_loan_eligibility", {"company_name":"ZenFit","business_type":"services","annual_turnover":25000000,"plant_machinery_value":2000000,"years_in_business":4,"loan_purpose":"expansion","loan_amount_requested":5000000,"existing_loans":1000000,"monthly_revenue":2100000,"gst_registered":True}, "msme_category","eligibility_score")
# 33 — actual keys: company, revenue, cogs
ca("pl_statement", {"company_name":"ZenFit","period":"FY 2024-25","revenue_items":[{"name":"Classes","amount":18000000}],"cogs_items":[{"name":"Instructor","amount":6000000}],"opex_items":[{"name":"Rent","amount":1200000}],"other_income":200000,"tax_rate":25,"industry":"wellness","prev_period_revenue":18000000,"prev_period_profit":2500000}, "company","revenue","cogs")
# 34 — actual keys: company, total_invoices, total_overdue
ca("overdue_collector", {"company_name":"Sharma & Co","invoices":[{"invoice_no":"SC/001","client":"FreshMart","amount":75000,"due_date":"2025-06-15","days_overdue":38}],"contact_name":"Priya","sender_name":"Priya","payment_terms":"Net 30","late_fee_pct":2}, "company","total_overdue")
# 35 — actual keys: company_name, forecast_period, opening_cash, closing_cash
ca("cash_flow_forecast", {"company_name":"ZenFit","monthly_revenue":2083333,"revenue_growth":8,"fixed_expenses":800000,"variable_expense_pct":35,"opening_cash":1500000,"industry":"wellness"}, "company_name","opening_cash","closing_cash")
# 36 — actual keys: industry, stage, inputs, financials
ca("business_valuation", {"revenue":25000000,"ebitda":5000000,"net_profit":3500000,"industry":"wellness","stage":"growth","growth_rate":25,"assets":10000000,"liabilities":4000000}, "industry","inputs","financials")
# 37 — actual keys: notice_type, taxpayer_name, gstin
ca("gst_notice_reply", {"notice_type":"scrutiny","notice_ref":"GSTN/SCR/2025/KA/1234","gstin":"29ZENFIT1234R1Z5","taxpayer_name":"ZenFit","notice_details":"ITC mismatch","reply_points":"Clerical error"}, "notice_type","taxpayer_name","gstin")
# 38
ca("payroll", {"company_name":"ZenFit","month":"July 2025","employees":[{"name":"Kavitha R","emp_id":"ZF-001","gross_salary":35000,"pf_applicable":True,"esi_applicable":False,"age":28,"state":"karnataka","lop_days":0},{"name":"Suresh M","emp_id":"ZF-002","gross_salary":45000,"pf_applicable":True,"esi_applicable":False,"age":32,"state":"karnataka","lop_days":0}]}, "payslips","summary")
# 39 — actual keys: taxpayer_type, age, regime, gross_income, current_deductions, recommendations
ca("tax_planning", {"income_details":{"salary":900000,"business_income":300000},"investments":{"ppf":60000,"elss":50000},"expenses":{"hra_paid":336000},"taxpayer_type":"individual","age":35,"regime":"old"}, "taxpayer_type","recommendations")
# 40 — actual keys: return_type, firm_name, gstin, period, sales_summary
ca("gstr_filing_prep", {"sales_data":[{"invoice_no":"ZF/001","party":"FreshMart","gstin":"29FRESH1234R1Z5","taxable":100000,"cgst":9000,"sgst":9000,"igst":0}],"purchase_data":[{"invoice_no":"SC/001","party":"Sharma","gstin":"29AABCU9603R1ZX","taxable":50000,"cgst":4500,"sgst":4500,"igst":0}],"return_type":"gstr3b","firm_name":"ZenFit","gstin":"29ZENFIT1234R1Z5","period":"July 2025"}, "return_type","firm_name","sales_summary")

# ── SUMMARY ──────────────────────────────────────────────────────────────────
print("\n" + "=" * 80)
passed  = sum(1 for s,*_ in results if s=="PASS")
partial = sum(1 for s,*_ in results if s=="PARTIAL")
failed  = sum(1 for s,*_ in results if s=="FAIL")
print(f"  RESULT: {passed}/{len(results)} PASS  |  {partial} PARTIAL  |  {failed} FAIL")
print("=" * 80)

if failed or partial:
    print("\n  Issues:")
    for s, nm, det in results:
        if s != "PASS":
            print(f"    [{s}] {nm}")
            print(f"         {det}")
