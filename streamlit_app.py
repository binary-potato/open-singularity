import streamlit as st
from groq import Groq
import os
from datetime import datetime
import json
from pathlib import Path
import uuid

# Initialize Groq client
client = Groq(
    api_key="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"
)

# Initialize session state variables
if 'chats' not in st.session_state:
    st.session_state.chats = {}
if 'current_chat_id' not in st.session_state:
    st.session_state.current_chat_id = None
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'show_file_upload' not in st.session_state:
    st.session_state.show_file_upload = False

# Function to save chat history
def save_chat_history():
    if not os.path.exists('chat_history'):
        os.makedirs('chat_history')
    
    for chat_id, chat_data in st.session_state.chats.items():
        file_path = f'chat_history/{chat_id}.json'
        with open(file_path, 'w') as f:
            json.dump(chat_data, f)

# Function to load chat history
def load_chat_history():
    if not os.path.exists('chat_history'):
        return
    
    for file_path in Path('chat_history').glob('*.json'):
        with open(file_path, 'r') as f:
            chat_data = json.load(f)
            chat_id = file_path.stem
            st.session_state.chats[chat_id] = chat_data

# Function to create new chat
def create_new_chat():
    chat_id = str(uuid.uuid4())
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.chats[chat_id] = {
        'timestamp': timestamp,
        'messages': []
    }
    st.session_state.current_chat_id = chat_id
    st.session_state.messages = []

# Function to process files
def process_file(uploaded_file):
    if uploaded_file is not None:
        file_contents = uploaded_file.read()
        if uploaded_file.type.startswith('text/'):
            return file_contents.decode('utf-8')
        return f"[File uploaded: {uploaded_file.name}]"
    return None

# Function to get chatbot response
def get_bot_response(messages):
    chat_completion = client.chat.completions.create(
        messages=[
            {"role": m["role"], "content": m["content"]} 
            for m in messages
        ],
        model="mixtral-8x7b-32768",
        temperature=0.7,
        max_tokens=1024,
    )
    return chat_completion.choices[0].message.content

# Toggle file upload popup
def toggle_file_upload():
    st.session_state.show_file_upload = not st.session_state.show_file_upload

# Streamlit UI
st.set_page_config(page_title="Chatbot", layout="wide")

# Custom CSS for the file upload button and popup
st.markdown("""
<style>
    .stButton button {
        width: 100%;
        border-radius: 20px;
        margin: 5px 0;
    }
    .stTextInput input {
        border-radius: 20px;
    }
    .chat-message {
        padding: 15px;
        border-radius: 10px;
        margin: 5px 0;
    }
    .file-upload-button {
        position: absolute;
        right: 60px;
        bottom: 15px;
        background: none;
        border: none;
        cursor: pointer;
    }
    .file-upload-button:hover {
        opacity: 0.7;
    }
    .file-upload-popup {
        position: fixed;
        bottom: 80px;
        right: 20px;
        background: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 0 10px rgba(0,0,0,0.1);
        z-index: 1000;
    }
    /* Hide Streamlit's default file uploader label */
    .stFileUploader label {
        display: none;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.title("💬 Chat History")
    
    # New Chat button
    if st.button("New Chat", key="new_chat"):
        create_new_chat()
    
    # Load existing chats
    load_chat_history()
    
    # Display chat history
    for chat_id, chat_data in sorted(st.session_state.chats.items(), 
                                   key=lambda x: x[1]['timestamp'], 
                                   reverse=True):
        timestamp = chat_data['timestamp']
        if st.button(f"Chat from {timestamp}", key=chat_id):
            st.session_state.current_chat_id = chat_id
            st.session_state.messages = chat_data['messages']
            st.rerun()

# Main chat interface
st.title("💬 Chatbot")

# Create new chat if none exists
if st.session_state.current_chat_id is None:
    create_new_chat()

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# File upload button and popup
col1, col2 = st.columns([12, 1])
with col2:
    st.markdown(
        f"""
        <button class="file-upload-button" onclick="document.getElementById('file-upload-popup').style.display='block'">
            📁
        </button>
        """,
        unsafe_allow_html=True
    )

# File upload popup
if st.session_state.show_file_upload:
    with st.container():
        st.markdown(
            """
            <div id="file-upload-popup" class="file-upload-popup">
                <h3>Upload File</h3>
            </div>
            """,
            unsafe_allow_html=True
        )
        uploaded_file = st.file_uploader("Choose a file", key="file_upload")
        if st.button("Close"):
            st.session_state.show_file_upload = False

# Chat input
if prompt := st.chat_input("What's on your mind?"):
    # Process file if uploaded
    file_content = None
    if 'file_upload' in st.session_state:
        file_content = process_file(st.session_state.file_upload)
    
    # Combine prompt with file content if present
    full_prompt = prompt
    if file_content:
        full_prompt = f"{prompt}\n\nFile contents:\n{file_content}"
    
    # Add user message to chat
    st.session_state.messages.append({"role": "user", "content": full_prompt})
    with st.chat_message("user"):
        st.write(full_prompt)
    
    # Get and display assistant response
    with st.chat_message("assistant"):
        response = get_bot_response(st.session_state.messages)
        st.write(response)
    
    # Add assistant response to chat
    st.session_state.messages.append({"role": "assistant", "content": response})
    
    # Update chat history
    st.session_state.chats[st.session_state.current_chat_id]['messages'] = st.session_state.messages
    save_chat_history()

# JavaScript for handling popup
st.markdown("""
<script>
    document.addEventListener('DOMContentLoaded', function() {
        const popup = document.getElementById('file-upload-popup');
        const btn = document.querySelector('.file-upload-button');
        
        // Close popup when clicking outside
        window.onclick = function(event) {
            if (event.target == popup) {
                popup.style.display = "none";
            }
        }
    });
</script>
""", unsafe_allow_html=True)
