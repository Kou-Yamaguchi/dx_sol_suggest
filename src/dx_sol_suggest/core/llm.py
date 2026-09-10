import os

from langchain_openai import ChatOpenAI


def get_llm(temperature: float = 0) -> ChatOpenAI:
    return ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        temperature=temperature,
    )
