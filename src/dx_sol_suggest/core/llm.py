import os

from langchain_openai import ChatOpenAI


def get_llm(temperature: float = 0) -> ChatOpenAI:
    """
    LLMクライアントを取得する。

    Args:
        temperature (float, optional): The temperature to use for the LLM. Defaults to 0.

    Returns:
        ChatOpenAI: The LLM object.
    """

    return ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        temperature=temperature,
    )
