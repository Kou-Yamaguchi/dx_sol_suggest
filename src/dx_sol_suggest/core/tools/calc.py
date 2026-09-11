from langchain.tools import tool

from ..state import CostEstimate, CostItem, EffectEstimate, RoiEstimate, Workload

DEFAULT_HOURLY_WAGE_JPY = 4000


def calc_annual_hours_impl(workload: Workload | None) -> float | None:
    if workload is None:
        return None
    return workload.annual_hours


def calc_labor_saving_impl(
    annual_hours: float | None,
    reduction_rate: float | None,
    hourly_wage_jpy: int = DEFAULT_HOURLY_WAGE_JPY,
) -> EffectEstimate:
    if annual_hours is None or reduction_rate is None:
        return EffectEstimate(can_quantify=False, hourly_wage_jpy=hourly_wage_jpy)
    hours_saved = annual_hours * reduction_rate
    return EffectEstimate(
        reduction_rate=reduction_rate,
        annual_hours_saved=hours_saved,
        hourly_wage_jpy=hourly_wage_jpy,
        annual_saving_jpy=int(hours_saved * hourly_wage_jpy),
        can_quantify=True,
    )


def sum_cost_items_impl(items: list[CostItem]) -> CostEstimate:
    initial = sum(item.amount_jpy for item in items if item.kind == "initial")
    annual = sum(item.amount_jpy for item in items if item.kind == "annual")
    return CostEstimate(items=items, initial_total_jpy=initial, annual_total_jpy=annual)


def compare_to_budget_impl(
    initial_cost: int,
    annual_cost: int,
    initial_cap: int | None,
    annual_cap: int | None,
) -> tuple[bool, str | None]:
    if initial_cap is None and annual_cap is None:
        return True, None
    if initial_cap is not None and initial_cost > initial_cap:
        return False, f"初期費用 {initial_cost:,}円 が予算上限 {initial_cap:,}円 を超過"
    if annual_cap is not None and annual_cost > annual_cap:
        return False, f"年額費用 {annual_cost:,}円 が年額予算 {annual_cap:,}円 を超過"
    return True, None


def calc_roi_impl(
    annual_saving_jpy: int | None,
    initial_cost_jpy: int | None,
    annual_cost_jpy: int = 0,
) -> RoiEstimate:
    if annual_saving_jpy is None or initial_cost_jpy is None:
        return RoiEstimate(
            can_calculate=False,
            reason_if_unavailable="業務量またはコストが不足しており、ROIを断定できません",
        )
    net_annual = annual_saving_jpy - annual_cost_jpy
    if initial_cost_jpy <= 0:
        return RoiEstimate(can_calculate=True, roi=None, payback_months=0)
    roi = (net_annual - initial_cost_jpy) / initial_cost_jpy
    payback = None
    if net_annual > 0:
        payback = (initial_cost_jpy / net_annual) * 12
    return RoiEstimate(can_calculate=True, roi=roi, payback_months=payback)


@tool
def calc_annual_hours(
    people: int | None = None,
    tasks_per_year: float | None = None,
    minutes_per_task: float | None = None,
) -> str:
    """年あたり業務時間を計算する。"""
    if tasks_per_year is None or minutes_per_task is None:
        return ""
    return str(tasks_per_year * minutes_per_task / 60)


@tool
def calc_labor_saving(
    annual_hours: float,
    reduction_rate: float,
    hourly_wage_jpy: int = DEFAULT_HOURLY_WAGE_JPY,
) -> str:
    """削減時間と人件費換算額を計算する。"""
    result = calc_labor_saving_impl(annual_hours, reduction_rate, hourly_wage_jpy)
    return result.model_dump_json()


@tool
def sum_cost_items(items_json: str) -> str:
    """費用内訳の合計を計算する。"""
    import json

    raw = json.loads(items_json)
    items = [CostItem.model_validate(item) for item in raw]
    return sum_cost_items_impl(items).model_dump_json()


@tool
def compare_to_budget(
    initial_cost: int,
    annual_cost: int,
    initial_cap: int | None = None,
    annual_cap: int | None = None,
) -> str:
    """コストが予算内かを判定する。"""
    ok, reason = compare_to_budget_impl(initial_cost, annual_cost, initial_cap, annual_cap)
    return "ok" if ok else (reason or "over_budget")


@tool
def calc_roi(
    annual_saving_jpy: int | None = None,
    initial_cost_jpy: int | None = None,
    annual_cost_jpy: int = 0,
) -> str:
    """ROIと回収月数を計算する。"""
    return calc_roi_impl(annual_saving_jpy, initial_cost_jpy, annual_cost_jpy).model_dump_json()


@tool
def calc_payback_months(initial_cost_jpy: int, net_annual_jpy: int) -> str:
    """投資回収月数を計算する。"""
    if net_annual_jpy <= 0:
        return ""
    return str((initial_cost_jpy / net_annual_jpy) * 12)
