import os
from datetime import datetime
from zoneinfo import ZoneInfo

from langchain.agents import create_agent
from langchain.tools import tool
from langchain_openai import ChatOpenAI


@tool
def current_time_in_tokyo() -> str:
    """日本時間の現在日時を返す。"""
    now = datetime.now(ZoneInfo("Asia/Tokyo"))
    return now.strftime("%Y-%m-%d %H:%M:%S JST")


def make_agent():
    model = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        temperature=0,
    )

    return create_agent(
        model=model,
        tools=[current_time_in_tokyo],
        system_prompt=(
            "あなたはDX提案を行うコンサルタントです。"
            "相談内容からボトルネックとなる課題を洗い出し、それを解決する方法を具体的に実行可能な状態で回答してください。"
            "実行可能にするために追加で情報が必要と思われる場合はその項目を列挙し質問を投げてください。"
        ),
    )
