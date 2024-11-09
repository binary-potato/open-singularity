import streamlit as st
from groq import Groq
import cohere
import google.generativeai as genai
import uuid
from datetime import datetime

# Your existing API client initialization code here...

# Custom CSS with gradients and modern styling
st.markdown("""
<style>
    /* Main container styling */
    .stApp {
        background-color: #f8fafc;
    }
    
    /* Gradient text styling */
    .gradient-text {
        background: linear-gradient(90deg, #6366f1, #a855f7, #3b82f6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.5rem;
        font-weight: 600;
    }
    
    .subtitle {
        color: #6b7280;
        font-size: 1rem;
        margin-bottom: 2rem;
    }
    
    /* Prompt cards styling */
    .prompt-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 1rem;
        margin-bottom: 2rem;
    }
    
    .prompt-card {
        background: white;
        padding: 1.5rem;
        border-radius: 0.75rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        transition: all 0.2s;
        cursor: pointer;
    }
    
    .prompt-card:hover {
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    .prompt-icon {
        font-size: 1.5rem;
        margin-bottom: 0.5rem;
    }
    
    /* Chat input styling */
    .stTextInput > div > div {
        background-color: white;
        border-radius: 0.75rem;
        border: none;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        padding: 0.75rem;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background-color: white;
    }
    
    .model-selector {
        background: white;
        padding: 1rem;
        border-radius: 0.75rem;
        margin-bottom: 1rem;
    }
    
    .model-option {
        display: flex;
        align-items: center;
        padding: 0.75rem;
        border-radius: 0.5rem;
        cursor: pointer;
        transition: all 0.2s;
    }
    
    .model-option:hover {
        background: #f3f4f6;
    }
    
    .model-icon {
        margin-right: 0.75rem;
        font-size: 1.25rem;
    }
    
    /* Custom file upload button */
    .file-upload-btn {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 0.5rem;
        padding: 0.5rem 1rem;
        cursor: pointer;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    /* Message container styling */
    .chat-message {
        background: white;
        padding: 1rem;
        border-radius: 0.75rem;
        margin: 0.5rem 0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# Sidebar with modern model selection
with st.sidebar:
    st.markdown("<h2 style='text-align: left; color: #1f2937;'>🤖 Model Selection</h2>", unsafe_allow_html=True)
    
    # Modern model selection cards
    models = {
        "Groq": "⚡",
        "Cohere": "🧠",
        "Gemini": "🌟"
    }
    
    st.markdown("<div class='model-selector'>", unsafe_allow_html=True)
    selected_model = st.radio(
        "Choose your AI model",
        list(models.keys()),
        format_func=lambda x: f"{models[x]} {x}",
        key="model_choice",
        label_visibility="collapsed"
    )
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Chat history section
    st.markdown("<h3 style='text-align: left; color: #1f2937;'>💬 Chat History</h3>", unsafe_allow_html=True)
    if st.button("+ New Chat", key="new_chat"):
        create_new_chat()
    
    # Display chat history with modern styling
    for chat_id, chat_data in sorted(st.session_state.chats.items(), 
                                   key=lambda x: x[1]['timestamp'],
                                   reverse=True):
        timestamp = chat_data['timestamp']
        provider = chat_data.get('provider', 'Groq')
        if st.button(
            f"{models.get(provider, '💭')} Chat from {timestamp}",
            key=chat_id,
            help=f"Open chat from {timestamp}"
        ):
            st.session_state.current_chat_id = chat_id
            st.session_state.messages = chat_data['messages']
            st.session_state.selected_provider = provider
            st.rerun()

# Main chat interface
st.markdown("<h1 class='gradient-text'>Hi there, John</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>What would you like to know?</p>", unsafe_allow_html=True)

# Prompt suggestions grid
prompts = [
    ("👤", "Write a to-do list for a personal project or task"),
    ("✉️", "Generate an email to reply to a job offer"),
    ("📄", "Summarise this article or text for me in one paragraph"),
    ("🤖", "How does AI work in a technical capacity")
]

st.markdown("<div class='prompt-grid'>", unsafe_allow_html=True)
for icon, text in prompts:
    st.markdown(f"""
        <div class='prompt-card' onclick="document.querySelector('.stTextInput input').value='{text}'">
            <div class='prompt-icon'>{icon}</div>
            <div>{text}</div>
        </div>
    """, unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# Refresh prompts button
if st.button("🔄 Refresh Prompts"):
    st.rerun()

# File upload and chat input
col1, col2 = st.columns([0.9, 0.1])
with col1:
    user_input = st.text_input("Ask whatever you want...", key="user_input")

with col2:
    uploaded_file = st.file_uploader("📎", type=["txt", "pdf", "doc"], label_visibility="collapsed")

# Display chat messages
if st.session_state.messages:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(f"<div class='chat-message'>{message['content']}</div>", unsafe_allow_html=True)

# Process user input
if user_input:
    # Add user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # Process file if uploaded
    if uploaded_file:
        file_content = process_file(uploaded_file)
        if file_content:
            user_input = f"{user_input}\n\nFile contents:\n{file_content}"
    
    # Get bot response
    response = get_bot_response(st.session_state.messages)
    
    # Add bot response
    st.session_state.messages.append({"role": "assistant", "content": response})
    
    # Update chat history
    if st.session_state.current_chat_id:
        st.session_state.chats[st.session_state.current_chat_id]['messages'] = st.session_state.messages
        st.session_state.chats[st.session_state.current_chat_id]['provider'] = st.session_state.selected_provider
    
    # Clear input
    st.rerun()
