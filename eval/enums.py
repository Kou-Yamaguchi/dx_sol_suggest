from enum import StrEnum
from typing import Any


class InputMode(StrEnum):
    STRUCTURED = "structured"
    NATURAL_LANGUAGE = "natural_language"


class ExpectedBehavior(StrEnum):
    SUGGEST = "suggest"
    ASK = "ask"
    ASK_OR_ASSUME = "ask_or_assume"
    REFUSE_OVERCONFIDENT_ROI = "refuse_overconfident_roi"


INPUT_MODE_SPECS: dict[InputMode, str] = {
    InputMode.STRUCTURED: "項目ラベル付きの構造化入力",
    InputMode.NATURAL_LANGUAGE: "自然文の入力",
}

EXPECTED_BEHAVIOR_SPECS: dict[ExpectedBehavior, str] = {
    ExpectedBehavior.SUGGEST: "情報が十分なので、確認待ちにせずDX提案を返す",
    ExpectedBehavior.ASK: "情報が足りないので、提案せず確認質問を返す",
    ExpectedBehavior.ASK_OR_ASSUME: "提案してよいが、欠けている情報は仮定として明示する",
    ExpectedBehavior.REFUSE_OVERCONFIDENT_ROI: "業務量が無い状態でROIや削減効果を断定しない",
}


def _parse_enum[T: StrEnum](enum_cls: type[T], value: str, field: str) -> T:
    try:
        return enum_cls(value)
    except ValueError as exc:
        allowed = ", ".join(repr(item.value) for item in enum_cls)
        raise ValueError(f"{field} の値 {value!r} は不正です。使える値: {allowed}") from exc


def parse_case_enums(case: dict[str, Any]) -> dict[str, Any]:
    """JSONの文字列をenumに変換する。不正値は読み込み時点で失敗させる。"""
    case_id = case.get("case_id", "<unknown>")
    try:
        case["input_mode"] = _parse_enum(InputMode, case["input_mode"], "input_mode")
        case["expected_behavior"] = _parse_enum(
            ExpectedBehavior, case["expected_behavior"], "expected_behavior"
        )
    except (KeyError, ValueError) as exc:
        raise ValueError(f"case_id={case_id}: {exc}") from exc
    return case
