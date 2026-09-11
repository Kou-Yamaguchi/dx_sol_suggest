from typing import Any

SOLUTION_PATTERNS: list[dict[str, Any]] = [
    {
        "id": "template_standardization",
        "name": "入力テンプレート標準化",
        "summary": "日報や申請の入力項目をテンプレート化し、後工程の集計を可能にする。",
        "keywords": ["フォーマット", "自由記述", "日報", "属人"],
        "complexity": "rules",
        "uses_generative_ai": False,
        "uses_public_cloud_llm": False,
        "replaces_existing_system": False,
        "avoid_when": [],
        "initial_cost_jpy": (0, 300_000),
        "annual_cost_jpy": (0, 0),
        "typical_duration_months": 1,
    },
    {
        "id": "ipaas_rpa",
        "name": "iPaaS / RPA による転記自動化",
        "summary": "Zapier、Power Automate、RPA などで定型データの転記を自動化する。",
        "keywords": ["転記", "コピペ", "CRM", "メール", "手作業"],
        "complexity": "rpa",
        "uses_generative_ai": False,
        "uses_public_cloud_llm": False,
        "replaces_existing_system": False,
        "avoid_when": ["no_external_saas"],
        "initial_cost_jpy": (50_000, 500_000),
        "annual_cost_jpy": (60_000, 240_000),
        "typical_duration_months": 1,
    },
    {
        "id": "regex_script",
        "name": "正規表現 / 固定スクリプト抽出",
        "summary": "フォーマットが安定したメールや帳票からルールベースで項目を抽出する。",
        "keywords": ["転記", "メール", "定型", "入力ミス"],
        "complexity": "rules",
        "uses_generative_ai": False,
        "uses_public_cloud_llm": False,
        "replaces_existing_system": False,
        "avoid_when": [],
        "initial_cost_jpy": (0, 300_000),
        "annual_cost_jpy": (0, 0),
        "typical_duration_months": 1,
    },
    {
        "id": "workflow_rules",
        "name": "既存ワークフロー / マクロの条件分岐",
        "summary": "既存の経費精算やExcelマクロに IF 条件を追加し、目視チェックを置き換える。",
        "keywords": ["目視", "承認", "経費", "ルール", "条件"],
        "complexity": "rules",
        "uses_generative_ai": False,
        "uses_public_cloud_llm": False,
        "replaces_existing_system": False,
        "avoid_when": [],
        "initial_cost_jpy": (0, 200_000),
        "annual_cost_jpy": (0, 0),
        "typical_duration_months": 1,
    },
    {
        "id": "nlp_closed",
        "name": "閉域NLPによる非構造テキスト構造化",
        "summary": "オンプレまたは閉域LLMで自由記述から定量項目・シグナルを抽出する。",
        "keywords": ["自由記述", "日報", "非構造", "シグナル", "テキスト"],
        "complexity": "ml",
        "uses_generative_ai": True,
        "uses_public_cloud_llm": False,
        "replaces_existing_system": False,
        "avoid_when": ["tiny_budget", "simple_copy"],
        "initial_cost_jpy": (1_500_000, 5_000_000),
        "annual_cost_jpy": (300_000, 1_200_000),
        "typical_duration_months": 4,
    },
    {
        "id": "rag_closed",
        "name": "社内閉域RAG / ベクトル検索",
        "summary": "社内文書や過去案件を閉域で検索し、属人的な探索を減らす。",
        "keywords": ["検索", "過去案件", "見積", "文書", "問い合わせ", "FAQ"],
        "complexity": "ml",
        "uses_generative_ai": True,
        "uses_public_cloud_llm": False,
        "replaces_existing_system": False,
        "avoid_when": ["tiny_budget", "simple_copy"],
        "initial_cost_jpy": (1_000_000, 4_000_000),
        "annual_cost_jpy": (240_000, 1_200_000),
        "typical_duration_months": 3,
    },
    {
        "id": "faq_bot",
        "name": "FAQチャットボット（RAG）",
        "summary": "社内規程をソースにしたFAQボットをSlack等へ連携する。",
        "keywords": ["問い合わせ", "Slack", "FAQ", "就業規則", "福利厚生"],
        "complexity": "saas",
        "uses_generative_ai": True,
        "uses_public_cloud_llm": False,
        "replaces_existing_system": False,
        "avoid_when": ["tiny_budget"],
        "initial_cost_jpy": (800_000, 2_000_000),
        "annual_cost_jpy": (120_000, 600_000),
        "typical_duration_months": 3,
    },
    {
        "id": "shift_optimizer",
        "name": "数理最適化 / シフト管理SaaS",
        "summary": "労働時間上限や必要人数を制約にしたソルバーまたは専用SaaSでシフトを組む。",
        "keywords": ["シフト", "配置", "労働基準", "希望"],
        "complexity": "saas",
        "uses_generative_ai": False,
        "uses_public_cloud_llm": False,
        "replaces_existing_system": False,
        "avoid_when": [],
        "initial_cost_jpy": (200_000, 800_000),
        "annual_cost_jpy": (120_000, 360_000),
        "typical_duration_months": 2,
    },
    {
        "id": "bi_dashboard",
        "name": "管理職向けダッシュボード",
        "summary": "抽出済みデータをBIで可視化し、確認作業を一覧化する。",
        "keywords": ["管理職", "確認", "可視化", "KPI", "案件"],
        "complexity": "saas",
        "uses_generative_ai": False,
        "uses_public_cloud_llm": False,
        "replaces_existing_system": False,
        "avoid_when": ["tiny_budget"],
        "initial_cost_jpy": (300_000, 1_500_000),
        "annual_cost_jpy": (120_000, 480_000),
        "typical_duration_months": 2,
    },
    {
        "id": "onprem_integration",
        "name": "既存オンプレシステム連携（API / RPA）",
        "summary": "既存システムを残し、APIまたはRPAでデータを受け渡す。全面リプレイスはしない。",
        "keywords": ["既存", "オンプレ", "連携", "日報システム"],
        "complexity": "custom",
        "uses_generative_ai": False,
        "uses_public_cloud_llm": False,
        "replaces_existing_system": False,
        "avoid_when": [],
        "initial_cost_jpy": (300_000, 2_000_000),
        "annual_cost_jpy": (0, 300_000),
        "typical_duration_months": 3,
    },
    {
        "id": "hitl_screening",
        "name": "AI補助 + 人間最終判断",
        "summary": "一次スクリーニングをAIが補助し、不合格や最終判断は人が行う。",
        "keywords": ["選考", "履歴書", "公平", "評価", "審査"],
        "complexity": "ml",
        "uses_generative_ai": True,
        "uses_public_cloud_llm": False,
        "replaces_existing_system": False,
        "avoid_when": ["tiny_budget"],
        "initial_cost_jpy": (1_000_000, 8_000_000),
        "annual_cost_jpy": (300_000, 1_500_000),
        "typical_duration_months": 4,
    },
]


def _mid(range_pair: tuple[int, int]) -> int:
    return (range_pair[0] + range_pair[1]) // 2


def lookup_solution_patterns(
    issues: list[str],
    constraint_flags: list[str],
    budget_jpy: int | None = None,
    duration_months: int | None = None,
    scale_down: bool = False,
) -> list[dict[str, Any]]:
    """
    SOLUTION_PATTERNS に定義されたソリューションパターンを、
    与えられた問題や制約条件に基づいてスコアリングし、
    上位5件を選択する。

    Args:
        issues (list[str]): 問題や制約条件を表すテキスト
        constraint_flags (list[str]): 制約条件を表すフラグ
        budget_jpy (int | None, optional): 予算 (円)
        duration_months (int | None, optional): 所要期間 (月)
        scale_down (bool, optional): スケールダウンフラグ

    Returns:
        list[dict[str, Any]]: スコアリングされたソリューションパターンのリスト
    """
    issue_text = " ".join(issues)
    flags = set(constraint_flags)

    # NOTE: (仮)予算が50万円以下の場合は "tiny_budget" フラグを追加
    tiny_budget = budget_jpy is not None and budget_jpy <= 500_000
    if tiny_budget:
        flags.add("tiny_budget")

    # NOTE: 低予算で転記やコピペが多い場合は "simple_copy" フラグを追加
    if any(token in issue_text for token in ("転記", "コピペ")) and tiny_budget:
        flags.add("simple_copy")

    scored: list[tuple[float, dict[str, Any]]] = []
    for pattern in SOLUTION_PATTERNS:

        # NOTE: 制約条件に基づいてソリューションパターンをフィルタリング
        if any(flag in pattern["avoid_when"] for flag in flags):
            continue
        if scale_down and pattern["complexity"] in {"ml", "custom"}:
            continue
        if tiny_budget and pattern["uses_generative_ai"]:
            continue
        if duration_months is not None and duration_months <= 1:
            if pattern["typical_duration_months"] > 2:
                continue

        # NOTE: キーワードに基づいてスコアを計算
        hits = sum(1 for keyword in pattern["keywords"] if keyword in issue_text)
        score = float(hits)
        if "confidential" in flags and pattern["uses_public_cloud_llm"]:
            continue
        if "on_prem" in flags and pattern["id"] == "onprem_integration":
            score += 2
        if hits == 0 and pattern["id"] not in {
            "onprem_integration",
            "template_standardization",
        }:
            continue
        scored.append((score, pattern))

    # NOTE: スコアに基づいてソリューションパターンをソート
    scored.sort(key=lambda item: item[0], reverse=True)
    selected = [item[1] for item in scored[:5]]
    if not selected:
        fallback_ids = ["template_standardization", "regex_script", "workflow_rules"]
        selected = [p for p in SOLUTION_PATTERNS if p["id"] in fallback_ids]
    return selected


def lookup_cost_range(solution_type: str, scale: str = "poc") -> dict[str, int]:
    """
    ソリューションパターンの初期コストと年間コストを返す。

    Args:
        solution_type (str): ソリューションパターンのID
        scale (str, optional): スケール (poc: POC, macro: マクロ, large: 大規模)

    Returns:
        dict[str, int]: 初期コストと年間コストの辞書
    """
    pattern = next((p for p in SOLUTION_PATTERNS if p["id"] == solution_type), None)

    # NOTE: ソリューションパターンが見つからない場合はデフォルト値を返す。(仮)初期コスト30万円, 年間コスト0円に設定
    if pattern is None:
        return {"initial_jpy": 300_000, "annual_jpy": 0}

    # NOTE: 初期コストと年間コストの中央値を計算
    initial = _mid(pattern["initial_cost_jpy"])
    annual = _mid(pattern["annual_cost_jpy"])

    # NOTE: スケールに応じて初期コストと年間コストを調整
    if scale == "macro":
        initial = min(initial, 200_000)
        annual = min(annual, 0)
    elif scale == "large":
        initial = pattern["initial_cost_jpy"][1]
        annual = pattern["annual_cost_jpy"][1]
    return {"initial_jpy": initial, "annual_jpy": annual}
