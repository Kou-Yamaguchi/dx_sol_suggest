from .state import AgentState


def extract_issue_node(state: AgentState):
    """課題を抽出するノード"""
    pass


def assume_issue_node(state: AgentState):
    """課題を推定するノード"""
    pass


def plan_sol_node(state: AgentState):
    """解決策を立案するノード"""
    pass


def calc_effect_node(state: AgentState):
    """効果を試算するノード"""
    pass


def calc_cost_node(state: AgentState):
    """コストを試算するノード"""
    pass


def check_within_budget_node(state: AgentState):
    """予算内に収まっているか確認するノード"""
    pass


def calc_roi_node(state: AgentState):
    """費用対効果を試算するノード"""
    pass


def summarize_node(state: AgentState):
    """最終出力を得るノード"""
    pass
