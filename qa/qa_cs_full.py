# -*- coding: utf-8 -*-
"""CS Full Feature QA — 38 actions, ShopEasy / Rajesh Kumar persona"""
import sys, json, urllib.request
sys.stdout.reconfigure(encoding='utf-8')

BASE = "http://localhost:8000"
results = []

def post(path, body, timeout=90):
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

PATH = "/api/verticals/cs/action"
def cs(action, payload, *keys, timeout=90):
    r, e = post(PATH, {"action": action, "payload": payload, "language": "en"}, timeout=timeout)
    check(action, r, e, *keys)

print("=" * 80)
print("  CS FULL QA — 38 actions | ShopEasy / Rajesh Kumar")
print("=" * 80)

# 1
cs("faq_bot", {"query":"My order hasn't arrived after 5 days","business_name":"ShopEasy","business_type":"ecommerce","faq_context":"Orders typically deliver in 3-5 business days. For delays contact support@shopeasy.in"}, "answer","confidence")
# 2
cs("qualify_lead", {"customer_name":"Anita Reddy","business_type":"ecommerce","responses":{"budget":"2L/month","authority":"Yes, I'm the owner","need":"WhatsApp ordering system","timeline":"3 months"}}, "quality","buying_signals")
# 3
cs("draft_whatsapp", {"message_type":"apology","customer_name":"Rajesh Kumar","business_name":"ShopEasy","context":"Order SHE-4521 delivered wrong address, re-dispatching in 24hrs with 10% coupon"}, "message","message_type")
# 4
cs("analyze_sentiment", {"text":"Ordered 3 days ago, no update! Support useless, want refund immediately!","customer_name":"Rajesh Kumar"}, "sentiment","urgency","score")
# 5
cs("handle_complaint", {"complaint":"Paid for express delivery, got standard. This is fraud!","customer_name":"Rajesh Kumar","order_id":"SHE-4521","business_name":"ShopEasy","category":"billing"}, "acknowledgment","resolution_steps")
# 6
cs("summarize_ticket", {"conversation":"Customer: My order SHE-4521 not delivered. Agent: Let me check. Agent: It was sent to wrong address. Customer: Unacceptable! Agent: We'll re-dispatch in 24hrs with 10% coupon.","customer_name":"Rajesh Kumar"}, "issue_summary","customer_mood")
# 7
cs("response_template", {"scenario":"delayed_delivery","business_type":"ecommerce","tone":"empathetic"}, "templates")
# 8
cs("weekly_report", {"ticket_data":"247 tickets, 198 resolved, 12 escalated, avg 6.2hrs, CSAT 4.1, top: delivery delay, wrong item, refund","period":"July 14-20, 2025","business_name":"ShopEasy"}, "executive_summary","top_issues")
# 9
cs("kb_answer", {"question":"How do I track my order?","kb_content":"ShopEasy order tracking: Go to My Orders > Enter order ID > View live status. SMS sent at each stage.","business_name":"ShopEasy"}, "answer")
# 10
cs("suggest_canned_response", {"incoming_message":"Where is my order? It's been 5 days!","business_name":"ShopEasy","existing_templates":[{"category":"delivery","text":"Your order is on the way! Track here: shopeasy.in/track"}]}, "suggested_text","category")
# 11
cs("analyze_sla", {"tickets":[{"id":"TKT-001","subject":"Order not delivered","priority":"high","created_at":"2025-07-21T09:00:00Z","first_response_at":"2025-07-21T12:30:00Z","resolved_at":None,"assignee":"Priya"},{"id":"TKT-002","subject":"Wrong item","priority":"medium","created_at":"2025-07-21T10:00:00Z","first_response_at":"2025-07-21T11:00:00Z","resolved_at":"2025-07-21T18:00:00Z","assignee":"Suresh"}],"sla_rules":{},"business_name":"ShopEasy"}, "stats","breaches")
# 12
cs("ticket_triage", {"ticket_text":"My gold jewellery order worth ₹45,000 has been missing for 7 days! Delivery person said delivered but nothing received.","customer_name":"Rajesh Kumar","channel":"whatsapp","customer_tier":"gold","is_repeat_contact":True}, "priority","category")
# 13
cs("voc_report", {"company_name":"ShopEasy","period":"Q1 FY 2025-26","total_responses":1240,"nps_score":42.0,"csat_score":4.1,"top_positive_themes":["fast delivery","easy returns","good packaging"],"top_negative_themes":["delayed support","wrong items","refund delays"],"data_sources":["csat_survey","reviews","support_tickets"],"verbatim_samples":["Great app but support is slow","Delivered on time, very happy","Wrong item received, no response for 3 days"]}, "executive_summary","company_name")
# 14
cs("review_response", {"business_name":"ShopEasy","product_name":"Wireless Earbuds","platform":"google","review_text":"Earbuds stopped working after 2 weeks. Very disappointed. No response from support.","star_rating":2,"reviewer_name":"Rahul M","support_email":"support@shopeasy.in"}, "sentiment","business_name")
# 15
cs("sla_policy", {"company_name":"ShopEasy","plan_tiers":["basic","standard","premium","enterprise"],"support_channels":["whatsapp","email","chat","phone"],"business_hours":"Mon-Sat 9am-9pm IST"}, "priority_tiers","company_name")
# 16
cs("agent_training", {"company_name":"ShopEasy","industry":"ecommerce","support_channels":["whatsapp","email","chat"],"tone":"empathetic"}, "modules")
# 17
cs("chatbot_script", {"business_name":"ShopEasy","industry":"ecommerce","bot_name":"ShopBot","top_faqs":["track order","return policy","payment failed","cancel order"],"escalation_trigger":"agent please","tone":"friendly","platform":"whatsapp"}, "bot_name","faq_count")
# 18
cs("returns_policy", {"business_name":"ShopEasy","industry":"ecommerce","return_days":7,"refund_days":5,"refund_modes":["original_payment","store_credit"],"contact_email":"returns@shopeasy.in","contact_phone":"1800-123-4567"}, "policy_sections","policy_title")
# 19
cs("support_analytics", {"business_name":"ShopEasy","industry":"ecommerce","week_label":"July 14-20 2025","total_tickets":247,"resolved_tickets":198,"avg_frt_hrs":2.3,"avg_resolution_hrs":6.2,"csat_score":4.1,"ticket_categories":{"delivery_delay":89,"wrong_item":54,"refund":42,"other":62},"agent_data":[{"name":"Priya","tickets":82,"csat":4.3,"avg_resolution_hrs":5.1},{"name":"Suresh","tickets":75,"csat":4.0,"avg_resolution_hrs":7.2}],"channel_data":{"whatsapp":140,"email":67,"chat":40},"prev_week_tickets":228,"prev_week_csat":3.9}, "summary","week")
# 20
cs("customer_360", {"customer_name":"Rajesh Kumar","customer_email":"rajesh@gmail.com","customer_since_months":18,"total_orders":23,"total_revenue":87500,"last_order_days_ago":12,"open_tickets":1,"total_tickets":5,"avg_resolution_hrs":8.2,"avg_csat":4.0,"plan_type":"Gold","has_referred":True,"payment_status":"current"}, "customer_name","customer_email")
# 21
cs("csat_survey", {"business_name":"ShopEasy","product_name":"ShopEasy App","survey_goal":"post_purchase","customer_segment":"repeat_buyers","industry":"ecommerce","max_questions":6,"include_nps":True}, "survey_focus","business_name")
# 22
cs("winback_campaign", {"business_name":"ShopEasy","product_name":"ShopEasy Premium","customer_name":"Rajesh Kumar","churn_reason":"bad_experience","inactive_days":45,"industry":"ecommerce","offer_type":"discount","offer_value":"20%","cs_rep_name":"Priya"}, "customer_name","churn_reason")
# 23
cs("escalation_email", {"business_name":"ShopEasy","customer_name":"Rajesh Kumar","ticket_id":"TKT-001","issue_summary":"Order SHE-4521 delivered to wrong address, customer paid express shipping","sla_breached":"48 hours","priority":"high","escalation_type":"internal","escalate_to":"Suresh (Senior Manager)","cs_rep_name":"Priya","current_status":"Re-dispatch arranged","customer_tier":"gold"}, "ticket_id","customer_name")
# 24
cs("kb_article", {"business_name":"ShopEasy","product_name":"ShopEasy App","article_topic":"How to track your order","article_type":"how_to","industry":"ecommerce","audience":"end_user","tone":"friendly"}, "article_topic","article_type")
# 25
cs("onboarding_sequence", {"business_name":"ShopEasy","product_name":"ShopEasy Pro","industry":"ecommerce","customer_type":"smb","key_features":["bulk ordering","inventory sync","WhatsApp alerts"],"success_metric":"first order placed within 7 days","cs_rep_name":"Priya"}, "customer_type","business_name")
# 26
cs("nps_campaign_builder", {"business_name":"ShopEasy","product_name":"ShopEasy App","industry":"ecommerce","responses":[{"score":9,"comment":"Love the fast delivery"},{"score":6,"comment":"Support response is slow"},{"score":3,"comment":"Wrong item twice, very frustrated"},{"score":10,"comment":"Best shopping app"}],"survey_channel":"whatsapp"}, "promoters","detractors","passives")
# 27
cs("agent_performance_scorecard", {"agents":[{"name":"Priya","tickets_resolved":82,"avg_csat":4.3,"avg_frt_hrs":2.1,"escalations":3,"first_contact_resolution":0.78},{"name":"Suresh","tickets_resolved":75,"avg_csat":4.0,"avg_frt_hrs":3.5,"escalations":6,"first_contact_resolution":0.71}],"business_name":"ShopEasy","period":"July 14-20 2025","team_targets":{"csat":4.2,"frt_hrs":3.0,"fcr":0.75}}, "total_agents","team_avg_score")
# 28
cs("winback_sequence", {"business_name":"ShopEasy","product_name":"ShopEasy Premium","churned_customers":[{"name":"Rajesh Kumar","email":"rajesh@gmail.com","churn_date":"2025-05-15","ltv":87500},{"name":"Anita Reddy","email":"anita@gmail.com","churn_date":"2025-06-01","ltv":45000}],"churn_reason":"bad_experience","offer_type":"discount","offer_value":"25%","industry":"ecommerce"}, "churn_reason","offer_type")
# 29
cs("customer_health_score", {"customers":[{"name":"Rajesh Kumar","login_frequency_days":3,"feature_adoption_pct":0.75,"support_tickets_30d":1,"nps_score":8,"payment_status":"current","contract_months_remaining":6},{"name":"Anita Reddy","login_frequency_days":15,"feature_adoption_pct":0.30,"support_tickets_30d":4,"nps_score":4,"payment_status":"current","contract_months_remaining":2}],"business_name":"ShopEasy","product_name":"ShopEasy Pro","industry":"ecommerce"}, "total_customers","avg_health_score")
# 30
cs("escalation_rule_builder", {"business_name":"ShopEasy","industry":"ecommerce","team_structure":[{"level":1,"title":"Support Agent","count":8},{"level":2,"title":"Senior Agent","count":3},{"level":3,"title":"Manager","count":1}],"products":["ShopEasy App","ShopEasy Pro"],"sla_tier":"standard"}, "escalation_matrix","sla_tier")
# 31
cs("ticket_categorizer", {"tickets":[{"id":"TKT-001","subject":"My order hasn't arrived after 7 days"},{"id":"TKT-002","subject":"I received wrong item, need exchange"},{"id":"TKT-003","subject":"Payment deducted but order not placed"},{"id":"TKT-004","subject":"How do I apply coupon code?"}],"business_name":"ShopEasy","custom_categories":[]}, "tickets","business_name")
# 32
cs("onboarding_planner", {"customer_name":"FreshMart Pvt Ltd","product_name":"ShopEasy Pro","industry":"retail","tier":"premium","goals":["reduce order errors","speed up fulfilment","WhatsApp notifications"],"team_size":15}, "customer_name","product_name")
# 33
cs("churn_risk", {"customers":[{"name":"Rajesh Kumar","days_since_last_login":3,"support_tickets_30d":1,"nps":8,"ltv":87500,"contract_end_days":180},{"name":"Anita Reddy","days_since_last_login":18,"support_tickets_30d":5,"nps":4,"ltv":45000,"contract_end_days":45},{"name":"FreshMart","days_since_last_login":7,"support_tickets_30d":2,"nps":7,"ltv":250000,"contract_end_days":90}],"business_name":"ShopEasy","industry":"ecommerce"}, "total_analyzed","high_count")
# 34
cs("escalation_manager", {"tickets":[{"id":"TKT-001","subject":"Gold customer order missing ₹45K","priority":"critical","customer_tier":"gold","created_at":"2025-07-20T09:00:00Z","sla_breach":True},{"id":"TKT-002","subject":"Payment deducted no order","priority":"high","customer_tier":"standard","created_at":"2025-07-21T14:00:00Z","sla_breach":False}],"rules":{"critical":{"escalate_after_hrs":2,"escalate_to":"manager@shopeasy.in"},"high":{"escalate_after_hrs":8,"escalate_to":"senior@shopeasy.in"}},"business_name":"ShopEasy","escalation_email":"escalations@shopeasy.in"}, "escalated","stats")
# 35
cs("build_csat_survey", {"business_name":"ShopEasy","business_type":"ecommerce","touchpoints":["post_delivery","post_support","post_return"]}, "survey_title","business_name")
# 36
cs("analyze_csat", {"responses":[{"rating":5,"comment":"Fast delivery, great packaging","touchpoint":"post_delivery"},{"rating":2,"comment":"Support took 3 days to reply","touchpoint":"post_support"},{"rating":4,"comment":"Easy return process","touchpoint":"post_return"},{"rating":1,"comment":"Wrong item twice! No compensation","touchpoint":"post_delivery"},{"rating":5,"comment":"Loved the WhatsApp updates","touchpoint":"post_delivery"}],"business_name":"ShopEasy"}, "csat_score","avg_rating")
# 37 — send_whatsapp skipped (needs Twilio creds)
# cs("send_whatsapp", ...) — skip
# 38 — ticket_triage with tickets list (old format from round2)
cs("ticket_triage", {"tickets":[{"id":"TKT-001","subject":"Order not delivered 5 days","channel":"whatsapp","customer_tier":"gold"},{"id":"TKT-002","subject":"Wrong item received","channel":"email","customer_tier":"regular"}],"ticket_text":"","customer_name":"","channel":"whatsapp","customer_tier":"standard"}, "priority","category")

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
