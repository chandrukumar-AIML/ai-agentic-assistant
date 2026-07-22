"""Customer Support tools — public API. Import from here, not from _impl directly."""
from .support_core import (
    faq_bot, handle_complaint, summarize_ticket,
    knowledge_base_answer, generate_response_template,
)
from .leads_whatsapp import qualify_lead, draft_whatsapp
from .analytics_reporting import (
    analyze_sentiment, weekly_report, generate_voc_report,
    generate_support_analytics, generate_customer_360,
)
from .policies_docs import (
    generate_sla_policy, generate_returns_policy, generate_review_response_kit,
    generate_agent_training_manual, generate_chatbot_script,
)
from .advanced import (
    score_ticket_priority, _churn_risk_analyzer, _ticket_categorizer,
    _escalation_manager, _agent_performance_scorecard, _nps_campaign_builder,
    _customer_health_score,
)

__all__ = [
    "faq_bot", "handle_complaint", "summarize_ticket",
    "knowledge_base_answer", "generate_response_template",
    "qualify_lead", "draft_whatsapp",
    "analyze_sentiment", "weekly_report", "generate_voc_report",
    "generate_support_analytics", "generate_customer_360",
    "generate_sla_policy", "generate_returns_policy", "generate_review_response_kit",
    "generate_agent_training_manual", "generate_chatbot_script",
    "score_ticket_priority",
]
