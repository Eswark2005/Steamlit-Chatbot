import streamlit as st
import requests
import time
import json
from datetime import datetime, date

st.set_page_config("💬 Chatbot + Planner", layout="wide")

def initialize_state():
    defaults = {
        "users": {},
        "logged_in": False,
        "email": "",
        "sessions": {},
        "active_session": None,
        "view": "chat",
        "planner_tasks": [],
        "last_user_msg": "",
        "rerun_trigger": False,
        "send_trigger": False
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val
initialize_state()

if st.session_state.rerun_trigger:
    st.session_state.rerun_trigger = False
    st.experimental_rerun()

GROQ_API_KEY = "your-groq-key"
MODEL_ID = "meta-llama/llama-4-scout-17b-16e-instruct"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

def login():
    st.subheader("🔓 Login")
    email = st.text_input("Email", key="login_email")
    password = st.text_input("Password", type="password", key="login_pass")
    if st.button("Login"):
        if st.session_state.users.get(email) == password:
            st.session_state.logged_in = True
            st.session_state.email = email
            st.success("Login successful!")
        else:
            st.error("Invalid credentials.")

def signup():
    st.subheader("🔐 Signup")
    email = st.text_input("Email", key="signup_email")
    password = st.text_input("Password", type="password", key="signup_pass")
    if st.button("Create Account"):
        if not email or not password:
            st.warning("Please fill in all fields.")
        elif email in st.session_state.users:
            st.error("User already exists.")
        else:
            st.session_state.users[email] = password
            st.success("Account created!")

def planner_ui():
    st.title("📆 Your Planner")
    with st.form("planner_form", clear_on_submit=True):
        col1, col2 = st.columns([4, 2])
        with col1:
            task = st.text_input("📝 Task")
        with col2:
            due = st.date_input("📅 Due Date", value=date.today())
        add = st.form_submit_button("➕ Add Task")
        if add and task:
            st.session_state.planner_tasks.append({"task": task, "due": str(due), "done": False})

    st.markdown("### 📋 Task List")
    with st.expander("View & Manage Tasks", expanded=True):
        updated_tasks = []
        for i, item in enumerate(st.session_state.planner_tasks):
            color = "✅" if item["done"] else "🟡"
            col1, col2, col3 = st.columns([6, 1, 1])
            with col1:
                done = st.checkbox(f"{color} {item['task']} (Due: {item['due']})", value=item["done"], key=f"task_{i}")
            with col2:
                delete = st.button("❌", key=f"delete_{i}")
            if not delete:
                updated_tasks.append({"task": item["task"], "due": item["due"], "done": done})
        st.session_state.planner_tasks = updated_tasks

def chat_ui():
    left, right = st.columns([1, 4])
    with left:
        st.markdown(f"👤 **{st.session_state.email}**")
        st.subheader("📁 Navigation")
        st.radio("Select View", ["💬 Chat", "📆 Planner"], key="view_radio")
        st.session_state.view = "chat" if st.session_state.view_radio == "💬 Chat" else "planner"

        if st.session_state.view == "chat":
            if st.button("➕ New Chat"):
                name = f"Chat {len(st.session_state.sessions)+1} - {datetime.now().strftime('%H:%M:%S')}"
                st.session_state.sessions[name] = []
                st.session_state.active_session = name
            for chat in st.session_state.sessions:
                if st.button(chat, key=chat):
                    st.session_state.active_session = chat

        st.markdown("---")
        if st.button("🚪 Logout"):
            for key in ["logged_in", "email", "active_session"]:
                st.session_state[key] = ""
            st.session_state.logged_in = False
            st.session_state.sessions = {}
            st.session_state.planner_tasks = []
            st.session_state.rerun_trigger = True
            st.stop()

    with right:
        if st.session_state.view == "planner":
            planner_ui()
            return

        if not st.session_state.active_session:
            st.info("Start a new chat to begin.")
            return

        st.title("💬 Chat with Groq")
        chat_box = st.empty()

        def render_chat(temp_reply=""):
            html = '<div style="height:500px; overflow-y:auto; padding:1em;">'
            for sender, msg in st.session_state.sessions[st.session_state.active_session]:
                bubble_color = "#4CAF50" if sender == "You" else "#3a3a3a"
                html += f'<div style="margin:10px; padding:10px; border-radius:10px; background:{bubble_color}; color:white;">{sender}: {msg}</div>'
            if temp_reply:
                html += f'<div style="margin:10px; padding:10px; border-radius:10px; background:#3a3a3a; color:white;">Bot: {temp_reply}</div>'
            html += "</div>"
            chat_box.markdown(html, unsafe_allow_html=True)

        render_chat()

        col1, col2, col3 = st.columns([4, 1, 1])
        with col1:
            user_msg = st.text_input("Type your message...", label_visibility="collapsed", key="input_msg")
        with col2:
            send = st.button("Send")
        with col3:
            retry = st.button("Retry")

        # Handle triggers
        if retry and st.session_state.last_user_msg:
            st.session_state.send_trigger = True
        elif send and user_msg.strip():
            st.session_state.last_user_msg = user_msg
            st.session_state.send_trigger = True

        if st.session_state.send_trigger:
            with st.spinner("💬 Waiting for Groq..."):
                st.session_state.send_trigger = False
                st.session_state.sessions[st.session_state.active_session].append(("You", st.session_state.last_user_msg))

                try:
                    headers = {
                        "Authorization": f"Bearer {GROQ_API_KEY}",
                        "Content-Type": "application/json"
                    }
                    data = {
                        "model": MODEL_ID,
                        "messages": [{"role": "user", "content": st.session_state.last_user_msg}]
                    }

                    res = requests.post(GROQ_URL, headers=headers, json=data)
                    res.raise_for_status()
                    reply = res.json()["choices"][0]["message"]["content"]

                    rendered = ""
                    for word in reply.split():
                        rendered += word + " "
                        render_chat(rendered)
                        time.sleep(0.01)

                    st.session_state.sessions[st.session_state.active_session].append(("Bot", reply))

                except Exception:
                    st.error("❌ Error: Could not get a reply from Groq.")
                else:
                    st.session_state.rerun_trigger = True
                    st.stop()

        if st.button("📥 Save Chat to File"):
            session = st.session_state.sessions[st.session_state.active_session]
            filename = f"chat_{st.session_state.active_session.replace(':', '-')}.json"
            with open(filename, "w") as f:
                json.dump(session, f, indent=2)
            st.success(f"Chat saved to {filename}")

st.markdown("<h2 style='text-align: center;'>🧠 Groq Chatbot + Planner</h2>", unsafe_allow_html=True)
st.markdown("---")

if not st.session_state.logged_in:
    login_tab, signup_tab = st.tabs(["Login", "Signup"])
    with login_tab: login()
    with signup_tab: signup()
else:
    chat_ui()


