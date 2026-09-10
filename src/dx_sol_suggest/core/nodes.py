import json

from langchain_core.messages import AIMessage, HumanMessage

from .catalogs import lookup_cost_range, lookup_solution_patterns, lookup_typical_issues
from .llm import get_llm
from .prompts import (
    ASSUME_ISSUE_PROMPT,
    COST_PROMPT,
    EFFECT_PROMPT,
    EXTRACT_CONSTRAINT_PROMPT,
    EXTRACT_ISSUE_PROMPT,
    PLAN_SOL_PROMPT,
    QUALITATIVE_CHECK_PROMPT,
    SUMMARIZE_PROMPT,
)
from .schemas import (
    AssumedIssues,
    ConstraintExtraction,
    CostPlan,
    EffectPlan,
    FinalSummary,
    IssueExtraction,
    QualitativeConstraintCheck,
    SolutionPlan,
)
from .state import (
    AgentState,
    BudgetInfo,
    Constraint,
    ConstraintViolation,
    CostItem,
    EffectEstimate,
    Issue,
    Solution,
)
from .tools.calc import (
    DEFAULT_HOURLY_WAGE_JPY,
    calc_labor_saving_impl,
    calc_roi_impl,
    compare_to_budget_impl,
    sum_cost_items_impl,
)
from .tools.check import check_solution_against_constraints_impl
from .tools.parse import (
    infer_constraint_flags,
    parse_budget_jpy_impl,
    parse_duration_months_impl,
    parse_workload_impl,
)


def _user_text(state: AgentState) -> str:
    for message in reversed(state.messages):
        if isinstance(message, HumanMessage):
            content = message.content
            return content if isinstance(content, str) else str(content)
        msg_type = getattr(message, "type", None)
        if msg_type in {"human", "user"}:
            content = getattr(message, "content", "")
            return content if isinstance(content, str) else str(content)
        if isinstance(message, dict) and message.get("role") in {"user", "human"}:
            return str(message.get("content", ""))
    return ""


def _structured(schema):
    return get_llm().with_structured_output(schema)


def _invoke_structured(schema, system_prompt: str, user_content: str):
    result = _structured(schema).invoke(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ]
    )
    if isinstance(result, dict):
        return schema.model_validate(result)
    return result


def _unique_extend(existing: list[str], extra: list[str]) -> list[str]:
    seen = set(existing)
    merged = list(existing)
    for item in extra:
        if item and item not in seen:
            merged.append(item)
            seen.add(item)
    return merged


def _dump(value) -> str:
    if hasattr(value, "model_dump"):
        return json.dumps(value.model_dump(), ensure_ascii=False, indent=2)
    return json.dumps(value, ensure_ascii=False, indent=2, default=str)


def extract_issue_node(state: AgentState):
    """課題を抽出するノード"""
    user_text = _user_text(state)
    extracted: IssueExtraction = _invoke_structured(
        IssueExtraction, EXTRACT_ISSUE_PROMPT, user_text
    )

    issues = [
        Issue(text=text, is_assumed=False, source="user")
        for text in extracted.issues
        if text.strip()
    ]
    missing = list(state.missing_fields)
    questions = list(state.questions)
    if not issues:
        missing = _unique_extend(missing, ["problems"])
    workload = None
    if extracted.has_workload or extracted.workload_raw:
        workload = parse_workload_impl(
            extracted.workload_people,
            extracted.workload_frequency,
            extracted.workload_time_per_task,
            extracted.workload_raw,
        )
    else:
        missing = _unique_extend(missing, ["workload"])
        questions = _unique_extend(
            questions,
            ["効果・ROIを試算するため、対象人数・頻度・1件あたり時間を教えてください。"],
        )

    return {
        "department": extracted.department,
        "situation": extracted.situation,
        "issues": issues,
        "workload": workload,
        "missing_fields": missing,
        "questions": questions,
    }


def extract_constraint_node(state: AgentState):
    """制約を抽出するノード"""
    extracted: ConstraintExtraction = _invoke_structured(
        ConstraintExtraction, EXTRACT_CONSTRAINT_PROMPT, _user_text(state)
    )

    constraints: list[Constraint] = []
    for raw in extracted.constraints:
        flags = _unique_extend(raw.flags, infer_constraint_flags(raw.text))
        budget_text = raw.budget_text or (raw.text if raw.category == "budget" else None)
        duration_text = raw.duration_text or (
            raw.text if raw.category == "timeline" else None
        )
        amount, kind = parse_budget_jpy_impl(budget_text)
        duration = parse_duration_months_impl(duration_text) or parse_duration_months_impl(
            raw.text
        )
        if amount is None:
            amount, kind = parse_budget_jpy_impl(raw.text)
        constraints.append(
            Constraint(
                text=raw.text,
                category=raw.category,
                source="user",
                budget_jpy=amount,
                budget_kind=kind,
                duration_months=duration,
                flags=flags,
            )
        )

    missing = list(state.missing_fields)
    questions = list(state.questions)
    assumptions = list(state.assumptions)
    if not constraints:
        missing = _unique_extend(missing, ["constraints"])
        questions = _unique_extend(
            questions,
            ["予算・期間・セキュリティ / 既存システム制約があれば教えてください。"],
        )
        assumptions = _unique_extend(
            assumptions,
            ["制約が未提示のため、追加投資を抑えたスモールスタートを仮定します。"],
        )

    initial_caps = [
        item.budget_jpy
        for item in constraints
        if item.budget_jpy is not None and item.budget_kind in {"initial", "none", None}
    ]
    annual_caps = [
        item.budget_jpy
        for item in constraints
        if item.budget_jpy is not None and item.budget_kind == "annual"
    ]
    budget = BudgetInfo(
        initial_cap_jpy=min(initial_caps) if initial_caps else None,
        annual_cap_jpy=min(annual_caps) if annual_caps else None,
        raw_text=" / ".join(item.text for item in constraints if item.category == "budget")
        or None,
        is_unknown=not initial_caps and not annual_caps,
    )

    return {
        "constraints": constraints,
        "missing_fields": missing,
        "questions": questions,
        "assumptions": assumptions,
        "budget": budget,
    }


def assume_issue_node(state: AgentState):
    """課題を推定するノード"""
    situation = state.situation or ""
    questions = list(state.questions)
    assumptions = list(state.assumptions)

    if not situation.strip() and not _user_text(state).strip():
        questions = _unique_extend(
            questions,
            ["現状の業務状況と、解決したい課題を具体的に教えてください。"],
        )
        return {
            "issues": [],
            "questions": questions,
            "should_propose": False,
        }

    typical = lookup_typical_issues(state.department, situation or _user_text(state))
    assumed: AssumedIssues = _invoke_structured(
        AssumedIssues,
        ASSUME_ISSUE_PROMPT,
        (
            f"部門: {state.department or '不明'}\n"
            f"状況: {situation or _user_text(state)}\n"
            f"典型課題候補: {typical}"
        ),
    )

    if not assumed.can_assume or not assumed.issues:
        questions = _unique_extend(
            questions,
            assumed.questions
            or ["解決したい課題（ボトルネック）を教えてください。"],
        )
        return {
            "issues": [],
            "questions": questions,
            "assumptions": _unique_extend(assumptions, assumed.assumptions),
            "should_propose": False,
        }

    issues = [
        Issue(text=text, is_assumed=True, source="assumed") for text in assumed.issues
    ]
    return {
        "issues": issues,
        "questions": _unique_extend(
            questions,
            assumed.questions
            or ["この課題認識で合っているか確認させてください。"],
        ),
        "assumptions": _unique_extend(assumptions, assumed.assumptions),
        "should_propose": True,
    }


def _constraint_flags(state: AgentState) -> list[str]:
    flags: list[str] = []
    for item in state.constraints:
        flags = _unique_extend(flags, item.flags)
    return flags


def _duration_months(state: AgentState) -> int | None:
    months = [item.duration_months for item in state.constraints if item.duration_months]
    return min(months) if months else None


def plan_sol_node(state: AgentState):
    """解決策を立案するノード"""
    issue_texts = [item.text for item in state.issues]
    flags = _constraint_flags(state)
    budget_jpy = state.budget.initial_cap_jpy if state.budget else None
    duration = _duration_months(state)
    patterns = lookup_solution_patterns(
        issue_texts,
        flags,
        budget_jpy=budget_jpy,
        duration_months=duration,
        scale_down=state.scale_down_requested,
    )
    feedback = [item.model_dump() for item in state.constraint_violations]
    plan: SolutionPlan = _invoke_structured(
        SolutionPlan,
        PLAN_SOL_PROMPT,
        (
            f"課題: {_dump(issue_texts)}\n"
            f"制約: {_dump([item.model_dump() for item in state.constraints])}\n"
            f"予算: {_dump(state.budget)}\n"
            f"候補パターン: {_dump(patterns)}\n"
            f"前回の違反: {_dump(feedback)}\n"
            f"縮小要求: {state.scale_down_requested}"
        ),
    )
    solution = Solution.model_validate(plan.model_dump())
    if "on_prem" in flags or "keep_existing" in flags:
        solution.replaces_existing_system = False
    if "confidential" in flags or "no_external_ai" in flags or "on_prem" in flags:
        solution.uses_public_cloud_llm = False
    return {"solution": solution}


def check_constraint_node(state: AgentState):
    """制約を遵守しているか確認するノード"""
    violations = check_solution_against_constraints_impl(state.solution, state.constraints)
    qualitative_targets = [
        item
        for item in state.constraints
        if item.category in {"accuracy", "other", "personnel"}
        or any(flag in item.flags for flag in ("fairness", "high_accuracy", "labor_law"))
    ]
    if qualitative_targets and state.solution is not None:
        qualitative: QualitativeConstraintCheck = _invoke_structured(
            QualitativeConstraintCheck,
            QUALITATIVE_CHECK_PROMPT,
            (
                f"提案: {_dump(state.solution)}\n"
                f"定性制約: {_dump([item.model_dump() for item in qualitative_targets])}"
            ),
        )
        for item in qualitative.violations:
            violations.append(
                ConstraintViolation(
                    constraint=item.constraint,
                    reason=item.reason,
                    fix_hint=item.fix_hint,
                )
            )

    retry_count = state.retry_count
    constraints_ok = not violations
    if violations and retry_count < state.max_retries:
        retry_count += 1
        constraints_ok = False
    elif violations and retry_count >= state.max_retries:
        constraints_ok = True

    return {
        "constraint_violations": violations,
        "retry_count": retry_count,
        "constraints_ok": constraints_ok,
    }


def calc_effect_node(state: AgentState):
    """効果を試算するノード"""
    plan: EffectPlan = _invoke_structured(
        EffectPlan,
        EFFECT_PROMPT,
        (
            f"課題: {_dump([item.text for item in state.issues])}\n"
            f"提案: {_dump(state.solution)}\n"
            f"業務量: {_dump(state.workload)}\n"
            f"業務量欠落: {'workload' in state.missing_fields}"
        ),
    )
    can_quantify = (
        state.workload is not None
        and state.workload.annual_hours is not None
        and plan.reduction_rate is not None
        and "workload" not in state.missing_fields
    )
    if not can_quantify:
        return {
            "effect": EffectEstimate(
                kpis=plan.kpis,
                qualitative_effects=plan.qualitative_effects,
                can_quantify=False,
                hourly_wage_jpy=DEFAULT_HOURLY_WAGE_JPY,
            )
        }

    rate = min(max(plan.reduction_rate or 0.3, 0.2), 0.6)
    assert state.workload is not None
    effect = calc_labor_saving_impl(
        state.workload.annual_hours,
        rate,
        DEFAULT_HOURLY_WAGE_JPY,
    )
    effect.kpis = plan.kpis
    effect.qualitative_effects = plan.qualitative_effects
    assumptions = _unique_extend(
        list(state.assumptions),
        [f"人件費単価は {DEFAULT_HOURLY_WAGE_JPY:,} 円/時間 と仮定しています。"],
    )
    return {"effect": effect, "assumptions": assumptions}


def calc_cost_node(state: AgentState):
    """コストを試算するノード"""
    pattern_ids = state.solution.pattern_ids if state.solution else []
    scale = "macro" if state.scale_down_requested else "poc"
    catalog_costs = {
        pattern_id: lookup_cost_range(pattern_id, scale) for pattern_id in pattern_ids
    }
    plan: CostPlan = _invoke_structured(
        CostPlan,
        COST_PROMPT,
        (
            f"提案: {_dump(state.solution)}\n"
            f"予算: {_dump(state.budget)}\n"
            f"カタログ概算: {_dump(catalog_costs)}\n"
            f"縮小要求: {state.scale_down_requested}"
        ),
    )
    items = [
        CostItem(
            name=item.name,
            amount_jpy=max(item.amount_jpy, 0),
            kind="annual" if item.kind == "annual" else "initial",
        )
        for item in plan.items
    ]
    if not items:
        for pattern_id, costs in catalog_costs.items():
            items.append(
                CostItem(
                    name=pattern_id,
                    amount_jpy=costs["initial_jpy"],
                    kind="initial",
                )
            )
            if costs["annual_jpy"]:
                items.append(
                    CostItem(
                        name=f"{pattern_id} 年額",
                        amount_jpy=costs["annual_jpy"],
                        kind="annual",
                    )
                )
    return {"cost": sum_cost_items_impl(items)}


def check_within_budget_node(state: AgentState):
    """予算内に収まっているか確認するノード"""
    assumptions = list(state.assumptions)
    if state.budget is None or state.budget.is_unknown or state.cost is None:
        assumptions = _unique_extend(
            assumptions,
            ["予算不明のため、追加投資を抑えたスモールスタートを前提にしています。"],
        )
        return {"budget_ok": True, "assumptions": assumptions, "scale_down_requested": False}

    ok, reason = compare_to_budget_impl(
        state.cost.initial_total_jpy,
        state.cost.annual_total_jpy,
        state.budget.initial_cap_jpy,
        state.budget.annual_cap_jpy,
    )
    budget_retry_count = state.budget_retry_count
    violations = list(state.constraint_violations)
    if ok:
        return {
            "budget_ok": True,
            "scale_down_requested": False,
            "assumptions": assumptions,
        }
    if budget_retry_count < state.max_retries:
        violations.append(
            ConstraintViolation(
                constraint="予算",
                reason=reason or "予算超過",
                fix_hint="対象範囲を縮小し、より安価な手段に切り替えてください",
            )
        )
        return {
            "budget_ok": False,
            "budget_retry_count": budget_retry_count + 1,
            "scale_down_requested": True,
            "constraint_violations": violations,
            "assumptions": assumptions,
        }
    violations.append(
        ConstraintViolation(
            constraint="予算",
            reason=reason or "予算超過の可能性",
            fix_hint="段階導入で初期費用を抑える前提を明示してください",
        )
    )
    return {
        "budget_ok": True,
        "scale_down_requested": False,
        "constraint_violations": violations,
        "assumptions": assumptions,
    }


def calc_roi_node(state: AgentState):
    """費用対効果を試算するノード"""
    questions = list(state.questions)
    effect = state.effect
    cost = state.cost
    if (
        effect is None
        or not effect.can_quantify
        or effect.annual_saving_jpy is None
        or cost is None
        or "workload" in state.missing_fields
    ):
        questions = _unique_extend(
            questions,
            ["ROIを算出するため、対象人数・頻度・1件あたり時間などの業務量を定量的に教えてください。"],
        )
        return {
            "roi": calc_roi_impl(None, None),
            "questions": questions,
        }
    return {
        "roi": calc_roi_impl(
            effect.annual_saving_jpy,
            cost.initial_total_jpy,
            cost.annual_total_jpy,
        )
    }


def summarize_node(state: AgentState):
    """最終出力を得るノード"""
    payload = {
        "should_propose": state.should_propose,
        "department": state.department,
        "situation": state.situation,
        "issues": [item.model_dump() for item in state.issues],
        "constraints": [item.model_dump() for item in state.constraints],
        "workload": state.workload.model_dump() if state.workload else None,
        "solution": state.solution.model_dump() if state.solution else None,
        "effect": state.effect.model_dump() if state.effect else None,
        "cost": state.cost.model_dump() if state.cost else None,
        "budget": state.budget.model_dump() if state.budget else None,
        "roi": state.roi.model_dump() if state.roi else None,
        "questions": state.questions,
        "assumptions": state.assumptions,
        "missing_fields": state.missing_fields,
        "violations": [item.model_dump() for item in state.constraint_violations],
    }
    result: FinalSummary = _invoke_structured(
        FinalSummary, SUMMARIZE_PROMPT, _dump(payload)
    )
    summary = result.markdown.strip()
    return {"summary": summary, "messages": [AIMessage(content=summary)]}
