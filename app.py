import streamlit as st
import requests
import time
from datetime import datetime

# ========== PAGE CONFIG ==========
st.set_page_config(page_title="💬 Chatbot | Groq", layout="wide")

# ========== SESSION STATE SETUP ==========
if 'users' not in st.session_state:
    st.session_state.users = {}
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'email' not in st.session_state:
    st.session_state.email = ""
if 'sessions' not in st.session_state:
    st.session_state.sessions = {}
if 'active_session' not in st.session_state:
    st.session_state.active_session = None

# ========== GROQ CONFIG ==========
GROQ_API_KEY = "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"
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

# ========== CHAT UI ==========
def chat_ui():
    left, right = st.columns([1, 4])

    # ========== SIDEBAR ==========
    with left:
        st.markdown(f"**👤 `{st.session_state.email}`**")
        st.subheader("📁 Sessions")

        if st.button("➕ New Chat"):
            chat_name = f"Chat {len(st.session_state.sessions) + 1} - {datetime.now().strftime('%H:%M:%S')}"
            st.session_state.sessions[chat_name] = []
            st.session_state.active_session = chat_name

        for chat_name in st.session_state.sessions:
            if st.button(chat_name, key=chat_name):
                st.session_state.active_session = chat_name

        st.markdown("---")
        
        if st.button("🚪 Logout"):
            st.session_state.logged_in = False
            st.session_state.email = ""
            st.session_state.active_session = None
            st.rerun()

    # ========== MAIN CHAT PANEL ==========
    with right:
        if not st.session_state.active_session:
            st.info("Start a new chat to begin.")
            return

        st.title("💬 Chat with Groq LLaMA 4")
        st.markdown(f"### 🧠 {st.session_state.active_session}")

        # Chat bubble styling
        st.markdown("""
        <style>
        .chat-box {
            background-color: #1e1e1e;
            padding: 20px;
            height: 500px;
            overflow-y: auto;
            border-radius: 10px;
            border: 1px solid #444;
            display: flex;
            flex-direction: column;
            gap: 10px;
            margin-bottom: 20px;
        }
        .bubble {
            max-width: 70%;
            padding: 10px 15px;
            border-radius: 20px;
            font-size: 15px;
            word-wrap: break-word;
            display: inline-block;
            color: white;
        }
        .you {
            align-self: flex-end;
            background-color: #4CAF50;
            border-bottom-right-radius: 0;
        }
        .bot {
            align-self: flex-start;
            background-color: #3a3a3a;
            border-bottom-left-radius: 0;
        }
        .timestamp {
            font-size: 10px;
            color: #aaa;
            text-align: right;
            margin-top: -6px;
        }
        </style>
        """, unsafe_allow_html=True)

        chat_placeholder = st.empty()

        def render_chat(streamed_reply=""):
            html = '<div class="chat-box">'
            for sender, msg in st.session_state.sessions[st.session_state.active_session]:
                role = "you" if sender == "You" else "bot"
                timestamp = datetime.now().strftime("%H:%M")
                html += f'<div class="bubble {role}">{msg}</div><div class="timestamp">{timestamp}</div>'
            if streamed_reply:
                html += f'<div class="bubble bot">{streamed_reply}</div><div class="timestamp">{datetime.now().strftime("%H:%M")}</div>'
            html += '</div>'
            chat_placeholder.markdown(html, unsafe_allow_html=True)

        # Render chat initially
        render_chat()

        # ========== INPUT + SEND ==========
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
                st.error(f"❌ Error: {e}")
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
    chat_ui()

