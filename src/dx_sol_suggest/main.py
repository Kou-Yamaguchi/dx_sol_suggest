from dotenv import load_dotenv
import streamlit as st

from dx_sol_suggest.core.pipeline import make_agent

load_dotenv()

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
            last_message = result["messages"][-1]
            answer = result.get("summary") or str(
                getattr(last_message, "content", last_message)
            )
            st.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})
