import re

from langchain.tools import tool

from ..state import BudgetKind, Workload

WORKING_DAYS_PER_YEAR = 240


def _to_int(value: str) -> int:
    return int(value.replace(",", "").replace("，", ""))


def parse_minutes(text: str | None) -> float | None:
    if not text:
        return None
    hour = re.search(r"([\d.]+)\s*時間", text)
    if hour:
        return float(hour.group(1)) * 60
    minute = re.search(r"([\d.]+)\s*分", text)
    if minute:
        return float(minute.group(1))
    return None


def parse_workload_impl(
    people: int | None,
    frequency: str | None,
    time_per_task: str | None,
    raw_text: str | None = None,
) -> Workload:
    minutes = parse_minutes(time_per_task)
    tasks_per_year = None
    freq = frequency or ""

    annual = re.search(r"年間\s*([\d,]+)\s*件", freq)
    monthly = re.search(r"月\s*([\d.]+)\s*回", freq)
    per_person_day = re.search(r"1人あたり1日\s*([\d.]+)\s*件", freq)
    day_total = re.search(r"1日合計\s*([\d.]+)\s*件", freq)
    per_day = re.search(r"1日\s*([\d.]+)\s*件", freq)

    if annual:
        tasks_per_year = float(_to_int(annual.group(1)))
    elif monthly:
        tasks_per_year = float(monthly.group(1)) * 12 * (people or 1)
    elif per_person_day:
        tasks_per_year = float(per_person_day.group(1)) * WORKING_DAYS_PER_YEAR * (people or 1)
    elif day_total:
        tasks_per_year = float(day_total.group(1)) * WORKING_DAYS_PER_YEAR
    elif per_day:
        tasks_per_year = float(per_day.group(1)) * WORKING_DAYS_PER_YEAR * (people or 1)

    annual_hours = None
    if tasks_per_year is not None and minutes is not None:
        annual_hours = tasks_per_year * minutes / 60

    return Workload(
        people=people,
        frequency_text=frequency,
        time_per_task_text=time_per_task,
        tasks_per_year=tasks_per_year,
        minutes_per_task=minutes,
        annual_hours=annual_hours,
        raw_text=raw_text,
    )


def parse_budget_jpy_impl(text: str | None) -> tuple[int | None, BudgetKind | None]:
    if not text:
        return None, None
    if re.search(r"ほぼゼロ|予算ゼロ|投資はできない", text):
        return 0, "none"
    amount = None
    man_yen = re.search(r"([\d,]+)\s*万円", text)
    if man_yen:
        amount = _to_int(man_yen.group(1)) * 10_000
    yen = re.search(r"([\d,]+)\s*円", text)
    if amount is None and yen:
        amount = _to_int(yen.group(1))
    if amount is None:
        return None, None
    if "月額" in text:
        return amount * 12, "annual"
    if "年間" in text or "年額" in text:
        return amount, "annual"
    return amount, "initial"


def parse_duration_months_impl(text: str | None) -> int | None:
    if not text:
        return None
    if re.search(r"半年", text):
        return 6
    if re.search(r"早急|すぐ|即効", text):
        return 1
    month = re.search(r"([\d.]+)\s*ヶ月|([\d.]+)\s*カ月|([\d.]+)\s*か月", text)
    if month:
        value = next(g for g in month.groups() if g)
        return int(float(value))
    year = re.search(r"([\d.]+)\s*年", text)
    if year:
        return int(float(year.group(1)) * 12)
    return None


def infer_constraint_flags(text: str) -> list[str]:
    flags: list[str] = []
    if re.search(r"オンプレ|既存.+連携|リプレイス", text):
        flags.append("on_prem")
        flags.append("keep_existing")
    if re.search(r"外部AI|学習され|パブリック|社外秘|機密|セキュア", text):
        flags.append("confidential")
        flags.append("no_external_ai")
    if re.search(r"個人情報", text):
        flags.append("personal_info")
    if re.search(r"公平|透明性|バイアス", text):
        flags.append("fairness")
    if re.search(r"ハルシネーション|正確性|100%|不正確|嘘", text):
        flags.append("high_accuracy")
    if re.search(r"労働基準|労働時間", text):
        flags.append("labor_law")
    return flags


@tool
def parse_workload(
    people: int | None = None,
    frequency: str | None = None,
    time_per_task: str | None = None,
) -> str:
    """人数・頻度・1件あたり時間を年換算可能な業務量に正規化する。"""
    return parse_workload_impl(people, frequency, time_per_task).model_dump_json()


@tool
def parse_budget_jpy(text: str) -> str:
    """『500万円以下』『月額10万円』などを円と予算種別へ分解する。"""
    amount, kind = parse_budget_jpy_impl(text)
    return f"{amount},{kind}"


@tool
def parse_duration_months(text: str) -> str:
    """期間表現を月数に正規化する。"""
    months = parse_duration_months_impl(text)
    return "" if months is None else str(months)
