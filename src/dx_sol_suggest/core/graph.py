from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from .nodes import (
    extract_issue_node,
    extract_constraint_node,
    assume_issue_node,
    plan_sol_node,
    check_constraint_node,
    calc_effect_node,
    calc_cost_node,
    check_within_budget_node,
    calc_roi_node,
    summarize_node,
)
from .state import AgentState


def _route_after_extract_issue(state: AgentState) -> str:
    if state.issue is None:
        return "assume_issue"
    return "extract_constraint"


# TODO: 適切な終了処理
def _route_after_assume_issue(state: AgentState) -> str:
    if state.issue is None:
        return "summarize"
    return "extract_constraint"


def suggest_agent():
    workflow = StateGraph(AgentState)

    # -- ノード登録 --
    workflow.add_node("extract_issue", extract_issue_node)
    workflow.add_node("extract_constraint", extract_constraint_node)
    workflow.add_node("assume_issue", assume_issue_node)
    workflow.add_node("plan_sol", plan_sol_node)
    workflow.add_node("check_constraint", check_constraint_node)
    workflow.add_node("calc_effect", calc_effect_node)
    workflow.add_node("calc_cost", calc_cost_node)
    workflow.add_node("check_within_budget", check_within_budget_node)
    workflow.add_node("calc_roi", calc_roi_node)
    workflow.add_node("summarize", summarize_node)

    # -- エッジ定義 --
    workflow.add_edge(START, "extract_issue")

    workflow.add_conditional_edges(
        "extract_issue",
        _route_after_extract_issue,
        {"assume_issue": "assume_issue", "extract_constraint": "extract_constraint"},
    )

    workflow.add_conditional_edges(
        "assume_issue",
        _route_after_assume_issue,
        {"extract_constraint": "extract_constraint", "summarize": "summarize"},
    )

    workflow.add_edge("extract_constraint", "plan_sol")

    # TODO: 制約チェックループ

    workflow.add_edge("plan_sol", "calc_effect")
    workflow.add_edge("plan_sol", "calc_cost")
    workflow.add_edge("calc_cost", "check_within_budget")

    # TODO: 予算チェックループ

    workflow.add_edge(["calc_effect", "check_within_budget"], "calc_roi")
    workflow.add_edge("calc_roi", "summarize")
    workflow.add_edge("summarize", END)
