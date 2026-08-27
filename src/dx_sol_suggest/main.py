import os
from datetime import datetime
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
import streamlit as st
from langchain.agents import create_agent
from langchain.tools import tool
from langchain_openai import ChatOpenAI

load_dotenv()


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


st.set_page_config(page_title="AI Agent", page_icon="🤖")
st.title("🤖 Streamlit AI Agent")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("メッセージを入力してください"):
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("考え中…"):
            agent = make_agent()
            result = agent.invoke(
                {
                    "messages": [
                        {"role": item["role"], "content": item["content"]}
                        for item in st.session_state.messages
                    ]
                }
            )
            answer = str(result["messages"][-1].content)
            st.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})
