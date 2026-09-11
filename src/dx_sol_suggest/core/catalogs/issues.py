TYPICAL_ISSUES: list[dict] = [
    {
        "keywords": ["日報", "自由記述", "訪問記録"],
        "issues": [
            "記述フォーマットが統一されておらず定量的なデータ抽出が困難",
            "管理職の確認作業に膨大な時間がかかっている",
            "重要なシグナルが見落とされがち",
        ],
    },
    {
        "keywords": ["コピペ", "転記", "資料請求", "CRM"],
        "issues": [
            "単純な転記作業に時間がかかっている",
            "コピペ時の入力ミスが発生している",
        ],
    },
    {
        "keywords": ["見積", "ファイルサーバー", "類似案件"],
        "issues": [
            "過去案件の検索に時間がかかる",
            "検索スキルの差により見積り精度が属人化している",
        ],
    },
    {
        "keywords": ["履歴書", "エントリーシート", "一次選考"],
        "issues": [
            "書類選考に膨大な時間がかかっている",
            "担当者によって評価がブレる",
        ],
    },
    {
        "keywords": ["シフト", "LINE", "労働基準"],
        "issues": [
            "シフト作成とルールチェックに時間がかかる",
            "特定担当者への属人化",
        ],
    },
    {
        "keywords": ["就業規則", "福利厚生", "Slack", "問い合わせ"],
        "issues": [
            "繰り返しの問い合わせ対応で人事の時間が奪われる",
            "回答待ちが発生している",
        ],
    },
    {
        "keywords": ["交通費", "経費", "目視", "承認"],
        "issues": [
            "ルールの目視チェックで見落としが起きる",
            "確認作業が特定時期に集中する",
        ],
    },
]


def lookup_typical_issues(department: str | None, situation: str | None) -> list[str]:
    """
    部門・状況から典型的な課題を抽出する。
    入力テキスト内容からkeywordベースで登録単語を検索
    ヒットしたkeywordが最も多い課題を出力

    Args:
        department (str | None): 部門
        situation (str | None): 状況

    Returns:
        list[str]: 典型的な課題リスト
    """
    text = f"{department or ''} {situation or ''}"
    if not text.strip():
        return []
    scored: list[tuple[int, list[str]]] = []
    for entry in TYPICAL_ISSUES:
        hits = sum(1 for keyword in entry["keywords"] if keyword in text)
        if hits:
            scored.append((hits, entry["issues"]))
    scored.sort(key=lambda item: item[0], reverse=True)
    if not scored:
        return []
    return list(scored[0][1])
