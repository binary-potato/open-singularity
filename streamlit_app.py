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

# Functions remain the same as before...
[Previous functions remain unchanged]

# Streamlit UI
st.set_page_config(page_title="Chatbot", layout="wide")

# Custom CSS with updated button positioning
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
    .upload-container {
        position: fixed;
        bottom: 120px;
        right: 20px;
        background: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 0 10px rgba(0,0,0,0.1);
        max-width: 300px;
        z-index: 1000;
    }
    /* Input container styles */
    .input-container {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 10px;
        background: white;
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        z-index: 1000;
    }
    /* Upload button styles */
    .upload-button {
        background: none;
        border: none;
        font-size: 20px;
        cursor: pointer;
        padding: 5px 10px;
        border-radius: 5px;
        transition: background-color 0.3s;
    }
    .upload-button:hover {
        background-color: #f0f0f0;
    }
    /* Main content padding to prevent overlap with fixed input */
    .main-content {
        padding-bottom: 80px;
    }
    /* Style for sidebar */
    .css-1d391kg {
        padding-bottom: 100px;
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

# Main content with padding
with st.container():
    st.markdown('<div class="main-content">', unsafe_allow_html=True)
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    st.markdown('</div>', unsafe_allow_html=True)

# Input area with file upload button
cols = st.columns([0.1, 0.8, 0.1])
with cols[0]:
    if st.button("📁", key="folder_button"):
        st.session_state.show_file_upload = not st.session_state.show_file_upload

# File upload popup
if st.session_state.show_file_upload:
    with st.container():
        st.markdown('<div class="upload-container">', unsafe_allow_html=True)
        st.subheader("Upload File")
        uploaded_file = st.file_uploader("Choose a file", key="file_upload")
        if st.button("Close", key="close_upload"):
            st.session_state.show_file_upload = False
        st.markdown('</div>', unsafe_allow_html=True)

# Chat input
with cols[1]:
    prompt = st.chat_input("What's on your mind?")

if prompt:
    # Process file if uploaded
    file_content = None
    if 'file_upload' in st.session_state and st.session_state.file_upload is not None:
        file_content = process_file(st.session_state.file_upload)
        st.session_state.show_file_upload = False
    
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
