import streamlit as st
from groq import Groq
import cohere
import google.generativeai as genai
import uuid
from datetime import datetime

# Initialize your API clients
groq_client = Groq(
    api_key="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"
)
cohere_client = cohere.Client("ROWbUII6RetAgHi2cNzzmcpmql63sE3FB3mtQVmO")
genai.configure(api_key="AIzaSyD_lGJ3bvXdOZuLVbo0mfyGVAAQB0bky_Q")
gemini_model = genai.GenerativeModel('gemini-pro')

# Custom CSS to make Streamlit look like a modern React app
st.markdown("""
<style>
    /* Modern React-like styling */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    /* Main container */
    .stApp {
        font-family: 'Inter', sans-serif;
        background-color: #f8fafc;
    }
    
    /* Header styling with gradient */
    .header-text {
        background: linear-gradient(135deg, #6366f1 0%, #a855f7 50%, #3b82f6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    
    .subheader-text {
        font-size: 2rem;
        color: #1f2937;
        margin-bottom: 1.5rem;
    }
    
    /* Prompt cards */
    .prompt-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
        gap: 1rem;
        margin: 2rem 0;
    }
    
    .prompt-card {
        background: white;
        padding: 1.5rem;
        border-radius: 1rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        transition: all 0.2s ease;
        cursor: pointer;
    }
    
    .prompt-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background-color: white;
    }
    
    .sidebar-content {
        padding: 1rem;
    }
    
    .model-selector {
        background: #f8fafc;
        padding: 1rem;
        border-radius: 0.75rem;
        margin-bottom: 1rem;
    }
    
    /* Chat input styling */
    .stTextInput > div > div {
        background-color: white !important;
        border-radius: 1rem !important;
        border: none !important;
        padding: 1rem !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1) !important;
    }
    
    /* Custom file button */
    .stButton > button {
        background: white;
        color: #4b5563;
        border: 1px solid #e5e7eb;
        border-radius: 0.5rem;
        padding: 0.5rem 1rem;
        transition: all 0.2s ease;
    }
    
    .stButton > button:hover {
        background: #f9fafb;
        border-color: #d1d5db;
    }
    
    /* Message container */
    .chat-message {
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 0.75rem;
        background: white;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    
    .user-message {
        background: #f0f9ff;
        margin-left: 2rem;
    }
    
    .bot-message {
        background: white;
        margin-right: 2rem;
    }
    
    /* Custom select box */
    .stSelectbox > div > div {
        background: white;
        border-radius: 0.75rem;
        border: 1px solid #e5e7eb;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'selected_model' not in st.session_state:
    st.session_state.selected_model = 'Groq'

# Sidebar with modern styling
with st.sidebar:
    st.markdown("<div class='sidebar-content'>", unsafe_allow_html=True)
    st.markdown("### 🤖 Model Selection")
    
    # Model selection with icons
    model_options = {
        "Groq": "⚡ Groq",
        "Cohere": "🧠 Cohere",
        "Gemini": "✨ Gemini"
    }
    
    selected_model = st.selectbox(
        "Choose your AI model",
        list(model_options.keys()),
        format_func=lambda x: model_options[x],
        key='model_select'
    )
    
    st.markdown("### 💬 Chat History")
    if st.button("+ New Chat"):
        st.session_state.messages = []
    st.markdown("</div>", unsafe_allow_html=True)

# Main chat interface
st.markdown("<h1 class='header-text'>Hi there, John</h1>", unsafe_allow_html=True)
st.markdown("<h2 class='subheader-text'>What would you like to know?</h2>", unsafe_allow_html=True)

# Prompt suggestions
prompts = [
    ("👤", "Write a to-do list for a personal project or task"),
    ("✉️", "Generate an email to reply to a job offer"),
    ("📄", "Summarise this article or text for me in one paragraph"),
    ("🤖", "How does AI work in a technical capacity")
]

# Display prompt cards
st.markdown("<div class='prompt-container'>", unsafe_allow_html=True)
for icon, text in prompts:
    st.markdown(f"""
        <div class='prompt-card' onclick="document.querySelector('.stTextInput input').value='{text}'">
            <div style='font-size: 2rem; margin-bottom: 0.5rem;'>{icon}</div>
            <div style='color: #4b5563;'>{text}</div>
        </div>
    """, unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# Chat input and file upload
col1, col2 = st.columns([0.9, 0.1])
with col1:
    user_input = st.text_input("Ask whatever you want...", key="user_input")
with col2:
    uploaded_file = st.file_uploader("📎", type=["txt", "pdf", "doc"], label_visibility="collapsed")

# Display chat messages
for message in st.session_state.messages:
    message_class = "user-message" if message["role"] == "user" else "bot-message"
    with st.chat_message(message["role"]):
        st.markdown(f"<div class='chat-message {message_class}'>{message['content']}</div>", unsafe_allow_html=True)

# Process user input
if user_input:
    # Add user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # Get bot response based on selected model
    if selected_model == "Groq":
        response = groq_client.chat.completions.create(
            messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
            model="mixtral-8x7b-32768",
        ).choices[0].message.content
    elif selected_model == "Cohere":
        chat_history = [{"role": m["role"], "message": m["content"]} for m in st.session_state.messages[:-1]]
        response = cohere_client.chat(
            message=user_input,
            chat_history=chat_history
        ).text
    else:  # Gemini
        chat = gemini_model.start_chat(history=[{"role": m["role"], "parts": [m["content"]]} for m in st.session_state.messages[:-1]])
        response = chat.send_message(user_input).text
    
    # Add bot response
    st.session_state.messages.append({"role": "assistant", "content": response})
    
    # Clear input and rerun
    st.rerun()
