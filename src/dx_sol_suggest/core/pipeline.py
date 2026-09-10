from langgraph.checkpoint.memory import MemorySaver

from .graph import suggest_agent


def make_agent(checkpointer: MemorySaver | None = None):
    return suggest_agent(checkpointer=checkpointer)
