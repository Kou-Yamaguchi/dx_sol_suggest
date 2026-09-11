from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from .nodes import (
    assume_issue_node,
    calc_cost_node,
    calc_effect_node,
    calc_roi_node,
    check_constraint_node,
    check_within_budget_node,
    extract_constraint_node,
    extract_issue_node,
    plan_sol_node,
    summarize_node,
)
from .state import AgentState


def _route_after_extract_issue(state: AgentState) -> str:
    """
    課題抽出を試みた後の遷移先を決定する。
        課題を抽出できない場合は仮説立案ノードへ遷移する。
        課題を抽出できた場合は、制約抽出ノードへ遷移する。
    """

    if not state.issues:
        return "assume_issue"
    return "extract_constraint"


def _route_after_assume_issue(state: AgentState) -> str:
    """
    仮説立案を試みた後の遷移先を決定する。
        仮説を立案できない場合は、要約ノードへ遷移する。
        仮説を立案できた場合は、制約抽出ノードへ遷移する。
    """

    if not state.issues:
        return "summarize"
    return "extract_constraint"


def _route_after_check_constraint(state: AgentState) -> str:
    """
    制約チェックを試みた後の遷移先を決定する。
        制約をチェックできない場合は、計画ノードへ遷移する。
        制約をチェックできた場合は、計算ノードへ遷移する。
    """

    if not state.constraints_ok:
        return "plan_sol"
    return "dispatch_calcs"


def _route_after_budget(state: AgentState) -> str:
    """
    予算チェックを試みた後の遷移先を決定する。
        予算をチェックできない場合は、計画ノードへ遷移する。
        予算をチェックできた場合は、ROI計算ノードへ遷移する。
    """

    if not state.budget_ok:
        return "plan_sol"
    return "calc_roi"


def _dispatch_calcs_node(_state: AgentState) -> dict:
    return {}


def suggest_agent(checkpointer: MemorySaver | None = None):
    """
    与えられた問題に対して、エージェントを提案する。
    Args:
        checkpointer (MemorySaver | None, optional): The checkpointer to use for the workflow. Defaults to None.

    Returns:
        Workflow: The workflow object.
    """

    workflow = StateGraph(AgentState)

    workflow.add_node("extract_issue", extract_issue_node)
    workflow.add_node("extract_constraint", extract_constraint_node)
    workflow.add_node("assume_issue", assume_issue_node)
    workflow.add_node("plan_sol", plan_sol_node)
    workflow.add_node("check_constraint", check_constraint_node)
    workflow.add_node("dispatch_calcs", _dispatch_calcs_node)
    workflow.add_node("calc_effect", calc_effect_node)
    workflow.add_node("calc_cost", calc_cost_node)
    workflow.add_node("check_within_budget", check_within_budget_node)
    workflow.add_node("calc_roi", calc_roi_node)
    workflow.add_node("summarize", summarize_node)

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
    workflow.add_edge("plan_sol", "check_constraint")
    workflow.add_conditional_edges(
        "check_constraint",
        _route_after_check_constraint,
        {"plan_sol": "plan_sol", "dispatch_calcs": "dispatch_calcs"},
    )
    workflow.add_edge("dispatch_calcs", "calc_effect")
    workflow.add_edge("dispatch_calcs", "calc_cost")
    workflow.add_edge(["calc_effect", "calc_cost"], "check_within_budget")
    workflow.add_conditional_edges(
        "check_within_budget",
        _route_after_budget,
        {"plan_sol": "plan_sol", "calc_roi": "calc_roi"},
    )
    workflow.add_edge("calc_roi", "summarize")
    workflow.add_edge("summarize", END)

    compile_kwargs = {}
    if checkpointer is not None:
        compile_kwargs["checkpointer"] = checkpointer
    return workflow.compile(**compile_kwargs)
