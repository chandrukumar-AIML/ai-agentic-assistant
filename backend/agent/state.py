from __future__ import annotations
from typing import Annotated, Any, Optional
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages


class ToolResult(TypedDict):
    tool_name:  str
    content:    str
    source:     str
    confidence: float
    metadata:   dict[str, Any]


def _replace_list(old: list, new: list) -> list:
    """Reducer: replaces list on retry (evaluator clears tool_results)."""
    return new


def _merge_dicts(a: dict, b: dict) -> dict:
    """Reducer: merges latency_ms dicts, later node wins on conflict."""
    return {**a, **b}


def _append_list(old: list, new: list) -> list:
    """Reducer: appends to reflection history."""
    return old + new


# FIXED: Single canonical AgentState — all phases consolidated here
class AgentState(TypedDict):
    # Conversation
    messages:       Annotated[list, add_messages]

    # Current turn
    user_query:     str
    image_data:     Optional[str]
    session_id:     str

    # Phase A: Identity + Memory
    user_id:        str
    memory_context: str

    # Planning
    intent:         str
    plan:           list[str]
    selected_tools: list[str]

    # Execution — replace reducer so evaluator can clear on retry
    tool_results:   Annotated[list[ToolResult], _replace_list]
    retry_count:    int
    max_retries:    int

    # Output
    final_answer:   Optional[str]
    sources:        list[str]

    # Phase B: Reflection loop
    reflection_score:    float
    reflection_verdict:  str
    reflection_critique: str
    reflection_missing:  list[str]
    reflection_attempts: int
    reflection_history:  Annotated[list[dict], _append_list]

    # Phase C: Multi-agent supervisor
    supervisor_workers:     list[dict]
    supervisor_parallel:    bool
    supervisor_aggregation: str
    supervisor_decision:    str
    worker_results:         list[dict]

    # Phase G: Prompt A/B
    ab_log_entry_id: Optional[int]

    # Phase I: Browser
    browser_screenshots: list[str]
    browser_actions_log: list[dict]
    browser_final_url:   Optional[str]

    # Phase N: Guardian Agent compliance
    guard_input_flag:      Optional[str]  # APPROVE | WARN | REJECT | ESCALATE_TO_HUMAN
    guard_output_flag:     Optional[str]  # APPROVE | WARN | REJECT
    pii_masked:            bool           # True if PII was masked in input
    phi_detected:          bool           # True if HIPAA PHI found
    compliance_verdict:    Optional[str]  # full ComplianceStatus value
    compliance_violations: list[dict]     # list of ComplianceViolation dicts

    # Phase O: Human-in-the-Loop (HITL)
    hitl_approval_id:    Optional[str]   # UUID of pending approval request
    hitl_decision:       Optional[str]   # "approved" | "rejected" | None (pending)
    hitl_action_type:    Optional[str]   # action label e.g. "email_send"
    hitl_action_payload: Optional[dict]  # payload for the action
    hitl_context_summary: Optional[str] # human-readable description for reviewer
    hitl_next_node:      Optional[str]   # node to route to after approval
    hitl_reviewer_note:  Optional[str]   # reviewer's rejection note

    # Observability
    trace_id:   str
    latency_ms: Annotated[dict[str, float], _merge_dicts]
    model_used: str
    error:      Optional[str]
