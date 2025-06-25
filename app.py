import streamlit as st
import requests
import time
from datetime import datetime, date

# ========== PAGE CONFIG ==========
st.set_page_config(page_title="💬 Chatbot | Groq", layout="wide")

# ========== SESSION STATE SETUP ==========
defaults = {
    "users": {},
    "logged_in": False,
    "email": "",
    "sessions": {},
    "active_session": None,
    "view": "chat",
    "planner_tasks": [],
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ========== GROQ CONFIG ==========
GROQ_API_KEY = "YOUR_GROQ_API_KEY"
MODEL_ID = "meta-llama/llama-4-scout-17b-16e-instruct"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

# ========== AUTH FUNCTIONS ==========
def signup():
    st.subheader("🔐 Signup")
    email = st.text_input("Email", key="signup_email")
    password = st.text_input("Password", type="password", key="signup_password")
    if st.button("Create Account"):
        if not email or not password:
            st.warning("Please fill in all fields.")
        elif email in st.session_state.users:
            st.error("User already exists.")
        else:
            st.session_state.users[email] = password
            st.success("Account created! You can now log in.")

def login():
    st.subheader("🔓 Login")
    email = st.text_input("Email", key="login_email")
    password = st.text_input("Password", type="password", key="login_password")
    if st.button("Login"):
        if st.session_state.users.get(email) == password:
            st.session_state.logged_in = True
            st.session_state.email = email
            st.success("Login successful!")
        else:
            st.error("Invalid credentials.")

# ========== PLANNER UI ==========
def planner_ui():
    st.title("🗓️ Your Planner")
    with st.form("add_task_form"):
        task = st.text_input("Task")
        due_date = st.date_input("Due Date", min_value=date.today())
        submitted = st.form_submit_button("Add Task")
        if submitted:
            if task:
                st.session_state.planner_tasks.append({"task": task, "done": False, "due": due_date})
            else:
                st.warning("Please enter a task.")

    delete_index = None
    for i, task in enumerate(st.session_state.planner_tasks):
        col1, col2, col3, col4 = st.columns([0.4, 0.3, 0.2, 0.1])
        with col1:
            st.session_state.planner_tasks[i]["done"] = st.checkbox(
                task["task"], value=task["done"], key=f"task_{i}"
            )
        with col2:
            st.markdown(f"**Due:** {task['due']}")
        with col3:
            status = "✅ Done" if task["done"] else "⏳ Pending"
            st.markdown(status)
        with col4:
            if st.button("❌", key=f"del_{i}"):
                delete_index = i

    if delete_index is not None:
        st.session_state.planner_tasks.pop(delete_index)
        st.experimental_rerun()

# ========== CHAT UI ==========
def chat_ui():
    if not st.session_state.active_session:
        st.info("Start a new chat to begin.")
        return

    st.title("💬 Chat with Groq LLaMA 4")
    st.markdown(f"### 🧠 {st.session_state.active_session}")

    chat_placeholder = st.empty()
    def render_chat(streamed_reply=""):
        html = '<div class="chat-box" style="background:#1e1e1e;padding:20px;height:500px;overflow:auto;border-radius:10px;border:1px solid #444;display:flex;flex-direction:column;gap:10px;margin-bottom:20px;">'
        for sender, msg in st.session_state.sessions[st.session_state.active_session]:
            role = "you" if sender == "You" else "bot"
            color = "#4CAF50" if role == "you" else "#3a3a3a"
            align = "right" if role == "you" else "left"
            html += f'<div style="align-self:{align};background:{color};padding:10px 15px;border-radius:20px;color:white;max-width:70%;">{msg}</div>'
        if streamed_reply:
            html += f'<div style="align-self:left;background:#3a3a3a;padding:10px 15px;border-radius:20px;color:white;max-width:70%;">{streamed_reply}</div>'
        html += '</div>'
        chat_placeholder.markdown(html, unsafe_allow_html=True)

    render_chat()

    col1, col2 = st.columns([5, 1])
    with col1:
        prompt = st.text_input("Your message:", label_visibility="collapsed", placeholder="Type your message here")
    with col2:
        send_clicked = st.button("Send")

    if send_clicked and prompt.strip():
        try:
            headers = {
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": MODEL_ID,
                "messages": [{"role": "user", "content": prompt}]
            }
            res = requests.post(GROQ_URL, headers=headers, json=payload)
            res.raise_for_status()
            reply = res.json()['choices'][0]['message']['content']

            session = st.session_state.active_session
            st.session_state.sessions[session].append(("You", prompt))
            streamed_text = ""
            for word in reply.split():
                streamed_text += word + " "
                render_chat(streamed_text)
                time.sleep(0.05)
            st.session_state.sessions[session].append(("Bot", reply))
            st.rerun()
        except Exception as e:
            st.error(f"\u274c Error: {e}")
    elif send_clicked:
        st.warning("Please enter a message.")

# ========== MAIN ROUTER ==========
st.markdown("<h2 style='text-align: center;'>🧠 Welcome to the Groq Chatbot</h2>", unsafe_allow_html=True)
st.markdown("---")

if not st.session_state.logged_in:
    tab1, tab2 = st.tabs(["Login", "Signup"])
    with tab1:
        login()
    with tab2:
        signup()
else:
    left, right = st.columns([1, 4])
    with left:
        st.markdown(f"**👤 `{st.session_state.email}`**")
        st.subheader("📁 Navigation")
        view = st.radio("Go to", ["💬 Chat", "🗓️ Planner"], label_visibility="collapsed")
        st.session_state.view = "chat" if view == "💬 Chat" else "planner"

        if st.session_state.view == "chat":
            if st.button("➕ New Chat"):
                name = f"Chat {len(st.session_state.sessions)+1} - {datetime.now().strftime('%H:%M:%S')}"
                st.session_state.sessions[name] = []
                st.session_state.active_session = name
            for chat_name in st.session_state.sessions:
                if st.button(chat_name, key=chat_name):
                    st.session_state.active_session = chat_name

        st.markdown("---")
        if st.button("🚪 Logout"):
            for key in defaults:
                st.session_state[key] = defaults[key]
            st.experimental_rerun()

    with right:
        if st.session_state.view == "planner":
            planner_ui()
        else:
            chat_ui()



