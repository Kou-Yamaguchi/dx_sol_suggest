from datetime import datetime, timezone
from uuid import uuid4

from dotenv import load_dotenv
import streamlit as st

from dx_sol_suggest.core.pipeline import make_agent

TITLE_MAX_LEN = 15


def _ensure_session() -> None:
    if "conversations" not in st.session_state:
        st.session_state.conversations = {}
    if "current_id" not in st.session_state:
        st.session_state.current_id = None
    if "messages" not in st.session_state:
        st.session_state.messages = []


def _copy_messages(messages: list[dict]) -> list[dict]:
    return [dict(message) for message in messages]


def _conversation_title(messages: list[dict]) -> str:
    for message in messages:
        if message.get("role") == "user" and str(message.get("content", "")).strip():
            text = str(message["content"]).strip().replace("\n", " ")
            if len(text) > TITLE_MAX_LEN:
                return text[:TITLE_MAX_LEN] + "…"
            return text
    return "新しいチャット"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _format_timestamp(iso_text: str) -> str:
    try:
        moment = datetime.fromisoformat(iso_text)
    except ValueError:
        return iso_text
    if moment.tzinfo is not None:
        moment = moment.astimezone()
    return moment.strftime("%Y-%m-%d %H:%M")


def _start_new_chat() -> None:
    st.session_state.current_id = None
    st.session_state.messages = []


def _open_conversation(conversation_id: str) -> None:
    conversation = st.session_state.conversations.get(conversation_id)
    if conversation is None:
        return
    st.session_state.current_id = conversation_id
    st.session_state.messages = _copy_messages(conversation["messages"])


def _delete_conversation(conversation_id: str) -> None:
    st.session_state.conversations.pop(conversation_id, None)
    if st.session_state.current_id == conversation_id:
        _start_new_chat()


def _save_current_conversation() -> None:
    messages = st.session_state.messages
    if not messages:
        return

    conversation_id = st.session_state.current_id
    if conversation_id is None or conversation_id not in st.session_state.conversations:
        conversation_id = str(uuid4())
        st.session_state.current_id = conversation_id
        st.session_state.conversations[conversation_id] = {
            "title": _conversation_title(messages),
            "messages": _copy_messages(messages),
            "updated_at": _now_iso(),
        }
        return

    conversation = st.session_state.conversations[conversation_id]
    conversation["messages"] = _copy_messages(messages)
    conversation["updated_at"] = _now_iso()


def _sorted_conversations() -> list[tuple[str, dict]]:
    return sorted(
        st.session_state.conversations.items(),
        key=lambda item: item[1].get("updated_at", ""),
        reverse=True,
    )


def _render_sidebar() -> None:
    with st.sidebar:
        st.markdown("### チャット")
        st.button(
            "新しいチャット",
            use_container_width=True,
            on_click=_start_new_chat,
        )

        st.markdown("### 会話履歴")
        conversations = _sorted_conversations()
        if not conversations:
            st.caption("まだ会話がありません")
            return

        for conversation_id, conversation in conversations:
            is_current = conversation_id == st.session_state.current_id
            left, right = st.columns([4, 1], vertical_alignment="center")
            with left:
                st.button(
                    conversation["title"],
                    key=f"open_{conversation_id}",
                    use_container_width=True,
                    type="primary" if is_current else "secondary",
                    on_click=_open_conversation,
                    args=(conversation_id,),
                )
                st.caption(_format_timestamp(conversation.get("updated_at", "")))
            with right:
                st.button(
                    "削除",
                    key=f"delete_{conversation_id}",
                    use_container_width=True,
                    on_click=_delete_conversation,
                    args=(conversation_id,),
                )


load_dotenv()

st.set_page_config(page_title="AI Agent", page_icon="🤖")
_ensure_session()
_render_sidebar()

st.title("🤖 Streamlit AI Agent")

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
            last_message = result["messages"][-1]
            answer = result.get("summary") or str(
                getattr(last_message, "content", last_message)
            )
            st.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})
    _save_current_conversation()
    st.rerun()
