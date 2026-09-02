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
        model=os.getenv("OPENAI_MODEL", "gpt-5.4"),
        temperature=0,
    )

    return create_agent(
        model=model,
        tools=[current_time_in_tokyo],
        system_prompt=(
            "あなたは役立つ日本語アシスタントです。"
            "現在時刻を尋ねられたときは、必ず current_time_in_tokyo ツールを使ってください。"
        ),
    )
