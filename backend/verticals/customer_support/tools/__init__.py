"""Customer Support tools — public API. Import from here, not from _impl directly."""
from .advanced import (
    _agent_performance_scorecard,
    _churn_risk_analyzer,
    _customer_health_score,
    _escalation_manager,
    _nps_campaign_builder,
    _ticket_categorizer,
    score_ticket_priority,
)
from .analytics_reporting import (
    analyze_sentiment,
    generate_customer_360,
    generate_support_analytics,
    generate_voc_report,
    weekly_report,
)
from .leads_whatsapp import draft_whatsapp, qualify_lead
from .policies_docs import (
    generate_agent_training_manual,
    generate_chatbot_script,
    generate_returns_policy,
    generate_review_response_kit,
    generate_sla_policy,
)
from .support_core import (
    faq_bot,
    generate_response_template,
    handle_complaint,
    knowledge_base_answer,
    summarize_ticket,
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
    "_agent_performance_scorecard", "_churn_risk_analyzer", "_customer_health_score",
    "_escalation_manager", "_nps_campaign_builder", "_ticket_categorizer",
]
