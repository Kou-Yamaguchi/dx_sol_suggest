from langchain.tools import tool

from ..catalogs import lookup_cost_range, lookup_solution_patterns, lookup_typical_issues


@tool
def lookup_typical_issues_tool(department: str = "", situation: str = "") -> str:
    """部門と状況から典型課題の候補を返す。"""
    issues = lookup_typical_issues(department or None, situation or None)
    return "\n".join(issues)


@tool
def lookup_solution_patterns_tool(
    issues_text: str,
    constraint_flags: str = "",
    budget_jpy: int | None = None,
    duration_months: int | None = None,
    scale_down: bool = False,
) -> str:
    """課題と制約に合う解決パターンを返す。"""
    flags = [flag.strip() for flag in constraint_flags.split(",") if flag.strip()]
    patterns = lookup_solution_patterns(
        [issues_text],
        flags,
        budget_jpy=budget_jpy,
        duration_months=duration_months,
        scale_down=scale_down,
    )
    lines = []
    for pattern in patterns:
        lines.append(
            f"{pattern['id']}: {pattern['name']} / {pattern['summary']} "
            f"(初期{pattern['initial_cost_jpy'][0]:,}〜{pattern['initial_cost_jpy'][1]:,}円)"
        )
    return "\n".join(lines)


@tool
def lookup_cost_range_tool(solution_type: str, scale: str = "poc") -> str:
    """解決パターンの概算費用レンジを返す。"""
    costs = lookup_cost_range(solution_type, scale)
    return f"initial={costs['initial_jpy']},annual={costs['annual_jpy']}"
