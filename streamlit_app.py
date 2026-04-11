import os
import streamlit as st
import requests
import uuid

st.set_page_config(
    page_title="RAG Chatbot",
    page_icon="📄",
    layout="wide"
)

API_URL = os.getenv("API_URL", "http://localhost:8000/api/v1")
REQUEST_TIMEOUT = 60

if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.header("Upload Document")

    uploaded_files = st.file_uploader(
        "Choose documents",
        type=["pdf", "txt", "md"],
        accept_multiple_files=True
    )

    if st.button("Process Documents", type="primary"):
        if uploaded_files:
            with st.spinner(f"Processing {len(uploaded_files)} file(s)..."):
                files = [
                    ("files", (f.name, f, f.type))
                    for f in uploaded_files
                ]
                try:
                    response = requests.post(
                        f"{API_URL}/upload/documents/",
                        files=files,
                        params={"user_id": str(st.session_state.user_id)} if st.session_state.user_id else {},
                        timeout=REQUEST_TIMEOUT
                    )
                    if response.status_code == 200:
                        data = response.json()
                        st.session_state.user_id = str(data["user_id"])
                        st.success(f"✅ Uploaded {data['uploaded']}/{len(uploaded_files)} files")
                        for f in data["files"]:
                            st.caption(f"📄 {f['filename']} — {f['chunks_created']} chunks")
                        for err in data.get("errors", []):
                            st.warning(f"⚠️ {err['filename']}: {err['error']}")
                    else:
                        st.error(f"Upload failed: {response.status_code}")
                except requests.exceptions.Timeout:
                    st.error("⏳ Server is waking up, please try again in 30 seconds.")
                except requests.exceptions.ConnectionError:
                    st.error("❌ Cannot reach server.")
        else:
            st.warning("Please select at least one file.")

    st.divider()

    if st.button("Clear Conversation"):
        try:
            response = requests.delete(
                f"{API_URL}/chat/{str(st.session_state.session_id)}",
                timeout=REQUEST_TIMEOUT
            )
            if response.status_code == 200:
                st.session_state.messages = []
                st.success("Conversation cleared")
            else:
                st.error(f"Failed to clear: {response.status_code}")
        except Exception as e:
            st.error(f"Failed to clear: {str(e)}")

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
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        try:
            response = requests.post(
                f"{API_URL}/chat/",
                json={
                    "query":   str(prompt),                         
                    "user_id":    str(st.session_state.user_id),       
                    "session_id": str(st.session_state.session_id),     
                    "k":          3
                },
                timeout=REQUEST_TIMEOUT                                 
            )
            if response.status_code == 200:
                data = response.json()
                assistant_message = {
                    "role":    "assistant",
                    "content": data["answer"],
                    "sources": data.get("sources", [])
                }
                st.session_state.messages.append(assistant_message)
                with st.chat_message("assistant"):
                    st.markdown(data["answer"])
                    if data.get("sources"):
                        st.caption(f"📄 Sources: {', '.join(data['sources'])}")
            else:
                st.error(f"Chat failed: {response.status_code} — {response.text}")

        except requests.exceptions.Timeout:
            st.error("⏳ Server is waking up, please try again in 30 seconds.")
        except requests.exceptions.ConnectionError:
            st.error("❌ Cannot reach server.")
        except Exception as e:
            st.error(f"Chat failed: {str(e)}")