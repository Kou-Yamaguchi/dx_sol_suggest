from langchain.tools import tool

from ..state import Constraint, ConstraintViolation, Solution


def check_solution_against_constraints_impl(
    solution: Solution | None,
    constraints: list[Constraint],
) -> list[ConstraintViolation]:
    if solution is None:
        return [
            ConstraintViolation(
                constraint="solution",
                reason="提案が未作成です",
                fix_hint="制約内のスモールスタート案を作成してください",
            )
        ]

    flags = {flag for item in constraints for flag in item.flags}
    texts = " ".join(item.text for item in constraints)
    violations: list[ConstraintViolation] = []

    if solution.uses_public_cloud_llm and (
        "confidential" in flags
        or "no_external_ai" in flags
        or "personal_info" in flags
        or "オンプレ" in texts
    ):
        violations.append(
            ConstraintViolation(
                constraint="セキュリティ / 機密情報",
                reason="パブリッククラウドLLMは機密・個人情報・オンプレ制約に抵触します",
                fix_hint="閉域またはオンプレのモデル連携に切り替えてください",
            )
        )

    if solution.replaces_existing_system and (
        "keep_existing" in flags or "既存" in texts or "オンプレ" in texts
    ):
        violations.append(
            ConstraintViolation(
                constraint="既存システム維持",
                reason="既存システムの全面リプレイスは制約違反です",
                fix_hint="既存システム連携（API/RPA）を前提にした追加機能にしてください",
            )
        )

    tiny_budget = any(
        item.budget_jpy is not None
        and item.budget_jpy <= 500_000
        and item.budget_kind in {"initial", "none", None}
        for item in constraints
    )
    short_timeline = any(
        item.duration_months is not None and item.duration_months <= 1 for item in constraints
    )
    simple_task = solution.complexity in {"ml", "custom"} and (
        tiny_budget or short_timeline
    )
    if simple_task and solution.uses_generative_ai:
        violations.append(
            ConstraintViolation(
                constraint="予算・期間に対する過剰なAI",
                reason="少額・短期間の単純作業に高額な生成AIは不適合です",
                fix_hint="iPaaS、RPA、マクロ、ルールベースに縮小してください",
            )
        )

    if "labor_law" in flags and solution.uses_generative_ai and "shift" in " ".join(
        solution.pattern_ids
    ):
        violations.append(
            ConstraintViolation(
                constraint="労働時間ルール",
                reason="シフトの厳密なルール適用に生成AIは不向きです",
                fix_hint="数理最適化またはシフト管理SaaSを使ってください",
            )
        )

    if (
        ("high_accuracy" in flags or "fairness" in flags)
        and solution.uses_generative_ai
        and not solution.human_in_the_loop
    ):
        violations.append(
            ConstraintViolation(
                constraint="正確性 / 公平性",
                reason="生成AIの自動確定はハルシネーションやバイアスのリスクがあります",
                fix_hint="ヒューマンインザループを必須にしてください",
            )
        )

    return violations


@tool
def check_solution_against_constraints(
    uses_public_cloud_llm: bool,
    uses_generative_ai: bool,
    replaces_existing_system: bool,
    human_in_the_loop: bool,
    complexity: str,
    pattern_ids: str,
    constraint_flags: str,
    constraint_texts: str,
) -> str:
    """提案が定量・ルール制約に抵触していないか判定する。"""
    solution = Solution(
        title="candidate",
        pattern_ids=[item for item in pattern_ids.split(",") if item],
        uses_public_cloud_llm=uses_public_cloud_llm,
        uses_generative_ai=uses_generative_ai,
        replaces_existing_system=replaces_existing_system,
        human_in_the_loop=human_in_the_loop,
        complexity=complexity,  # type: ignore[arg-type]
    )
    constraints = [
        Constraint(
            text=constraint_texts,
            flags=[flag.strip() for flag in constraint_flags.split(",") if flag.strip()],
        )
    ]
    violations = check_solution_against_constraints_impl(solution, constraints)
    if not violations:
        return "ok"
    return "\n".join(f"{item.reason} -> {item.fix_hint}" for item in violations)
