import os
import streamlit as st
import requests
import uuid

API_URL = os.getenv("API_URL", "http://localhost:8000/api/v1")

if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []

st.set_page_config(
    page_title="RAG Chatbot",
    page_icon="📄",
    layout="wide"
)

with st.sidebar:
    st.header("Upload Document")

    uploaded_file = st.file_uploader(
        "Choose a document",
        type=["pdf", "txt", "md"],
        help="Upload a PDF, text, or markdown file"
    )

    if st.button("Process Document", type="primary"):
        if uploaded_file is not None:
            files = {"file": (uploaded_file.name, uploaded_file, uploaded_file.type)}
            try:
                response = requests.post(f"{API_URL}/upload/document/", files=files)
                if response.status_code == 200:
                    data = response.json()
                    st.session_state.user_id = data["user_id"]
                    st.success(f"Document processed successfully! Created {data['chunks_created']} chunks.")
                    st.info(f"User ID: {data['user_id']}")
                else:
                    st.error(f"Upload failed with status code: {response.status_code}")
            except Exception as e:
                st.error(f"Upload failed: {str(e)}")
        else:
            st.error("Please select a file first")

    st.divider()

    if st.button("Clear Conversation"):
        try:
            response = requests.delete(f"{API_URL}/chat/{st.session_state.session_id}")
            if response.status_code == 200:
                st.session_state.messages = []
                st.success("Conversation cleared")
            else:
                st.error(f"Failed to clear conversation: {response.status_code}")
        except Exception as e:
            st.error(f"Failed to clear conversation: {str(e)}")

st.markdown("# 📄 RAG Chatbot")

if st.session_state.user_id is None:
    st.info("Please upload a document in the sidebar to start chatting")
else:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "sources" in message and message["sources"]:
                st.caption(f"Sources: {', '.join(message['sources'])}")

    if prompt := st.chat_input("Ask about your document..."):
        if st.session_state.user_id is None:
            st.error("Please upload a document first")
        else:
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            try:
                response = requests.post(
                    f"{API_URL}/chat/",
                    json={
                        "query": prompt,
                        "user_id": st.session_state.user_id,
                        "session_id": st.session_state.session_id,
                        "k": 3
                    }
                )

                if response.status_code == 200:
                    data = response.json()
                    assistant_message = {
                        "role": "assistant",
                        "content": data["answer"],
                        "sources": data.get("sources", [])
                    }
                    st.session_state.messages.append(assistant_message)

                    with st.chat_message("assistant"):
                        st.markdown(data["answer"])
                        if data.get("sources"):
                            st.caption(f"Sources: {', '.join(data['sources'])}")
                else:
                    st.error(f"Chat request failed with status code: {response.status_code}")

            except Exception as e:
                st.error(f"Chat request failed: {str(e)}")