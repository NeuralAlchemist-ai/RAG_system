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
if "access_token" not in st.session_state:
    st.session_state.access_token = None
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []

def auth_headers() -> dict:
    if st.session_state.access_token:
        return {"Authorization": f"Bearer {st.session_state.access_token}"}
    return {}

if st.session_state.access_token is None:
    st.markdown("# RAG Chatbot")
    
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    
    with tab1:
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        if st.button("Login"):
            try:
                response = requests.post(
                    f"{API_URL}/auth/login/",
                    json={"email": email, "password": password},
                    timeout=REQUEST_TIMEOUT
                )
                if response.status_code == 200:
                    data = response.json()
                    st.session_state.access_token = data["access_token"]
                    st.session_state.user_id = data["user_id"]
                    st.rerun()
                else:
                    st.error(f"Login failed: {response.json().get('detail', 'Unknown error')}")
            except Exception as e:
                st.error(f"Login failed: {str(e)}")
    
    with tab2:
        email = st.text_input("Email", key="signup_email")
        password = st.text_input("Password", type="password", key="signup_password")
        if st.button("Create Account"):
            try:
                response = requests.post(
                    f"{API_URL}/auth/signup/",
                    json={"email": email, "password": password},
                    timeout=REQUEST_TIMEOUT
                )
                if response.status_code == 200:
                    st.success("Account created! Please login.")
                else:
                    st.error(f"Sign up failed: {response.json().get('detail', 'Unknown error')}")
            except Exception as e:
                st.error(f"Sign up failed: {str(e)}")
    
    st.stop()

with st.sidebar:
    st.caption(f"Logged in as: {st.session_state.user_id}")
    if st.button("Logout"):
        st.session_state.access_token = None
        st.session_state.user_id = None
        st.session_state.messages = []
        st.rerun()
    
    st.header("📂 Upload Documents")

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
                        headers=auth_headers(),
                        timeout=REQUEST_TIMEOUT
                    )
                    if response.status_code == 200:
                        data = response.json()
                        st.session_state.user_id = str(data["user_id"])
                        st.success(f"✅ Uploaded {data['uploaded']}/{len(uploaded_files)} files")
                        st.info(f"💾 Your User ID: `{st.session_state.user_id}`")
                        for f in data["files"]:
                            st.caption(f"📄 {f['filename']} — {f['chunks_created']} chunks")
                        for err in data.get("errors", []):
                            st.warning(f"⚠️ {err['filename']}: {err['error']}")
                    else:
                        st.error(f"Upload failed: {response.status_code} — {response.text}")
                except requests.exceptions.Timeout:
                    st.error("⏳ Server is waking up, please try again in 30 seconds.")
                except requests.exceptions.ConnectionError:
                    st.error("❌ Cannot reach server. Check if backend is deployed.")
                except Exception as e:
                    st.error(f"Upload failed: {str(e)}")
        else:
            st.warning("Please select at least one file.")

    st.divider()

    st.subheader("♻️ Restore Session")
    existing_user_id = st.text_input(
        "User ID",
        placeholder="Paste your User ID to restore documents"
    )
    existing_session_id = st.text_input(
        "Session ID",
        placeholder="Paste your Session ID to restore chat"
    )
    if st.button("Restore Session"):
        if existing_user_id:
            st.session_state.user_id = existing_user_id.strip()
        if existing_session_id:
            st.session_state.session_id = existing_session_id.strip()
            try:
                response = requests.get(
                    f"{API_URL}/chat/{st.session_state.session_id}/history",
                    headers=auth_headers(),
                    timeout=REQUEST_TIMEOUT
                )
                if response.status_code == 200:
                    st.session_state.messages = response.json().get("messages", [])
                    st.success("✅ Session restored!")
                else:
                    st.session_state.messages = []
                    st.info("No previous messages found for this session.")
            except Exception as e:
                st.error(f"Failed to restore session: {str(e)}")
        else:
            st.warning("Please enter at least a User ID.")

    st.divider()

    st.subheader("🔑 Current Session")
    st.caption(f"User ID: `{st.session_state.user_id or 'not set'}`")
    st.caption(f"Session ID: `{st.session_state.session_id}`")

    st.divider()

    if st.button("🗑️ Clear Conversation"):
        try:
            response = requests.delete(
                f"{API_URL}/chat/{str(st.session_state.session_id)}",
                headers=auth_headers(),
                timeout=REQUEST_TIMEOUT
            )
            if response.status_code == 200:
                st.session_state.messages = []
                st.success("Conversation cleared.")
            else:
                st.error(f"Failed to clear: {response.status_code}")
        except requests.exceptions.Timeout:
            st.error("⏳ Server is waking up, please try again.")
        except requests.exceptions.ConnectionError:
            st.error("❌ Cannot reach server.")
        except Exception as e:
            st.error(f"Failed to clear: {str(e)}")


st.markdown("# 📄 RAG Chatbot")

if st.session_state.user_id is None:
    st.info("👈 Upload a document in the sidebar to start chatting.")
else:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message.get("sources"):
                st.caption(f"📄 Sources: {', '.join(message['sources'])}")

    if prompt := st.chat_input("Ask about your document..."):

        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        try:
            response = requests.post(
                f"{API_URL}/chat/",
                json={
                    "query":   str(prompt),                        
                    "session_id": str(st.session_state.session_id),
                },
                headers=auth_headers(),
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

            elif response.status_code == 422:
                st.error("❌ Request format error — check API schema.")
            else:
                st.error(f"Chat failed: {response.status_code} — {response.text}")

        except requests.exceptions.Timeout:
            st.error("⏳ Server is waking up, please try again in 30 seconds.")
        except requests.exceptions.ConnectionError:
            st.error("❌ Cannot reach server. Check if backend is deployed.")
        except Exception as e:
            st.error(f"Chat failed: {str(e)}")