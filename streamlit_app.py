import streamlit as st
from groq import Groq
from typing import List
import os
import tempfile
import json
from datetime import datetime

# Initialize Groq client
client = Groq(api_key="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")

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []

if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

if 'selected_chat' not in st.session_state:
    st.session_state.selected_chat = None

def save_chat_history():
    """Save current chat to history"""
    if st.session_state.messages:  # Only save if there are messages
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        history = {
            'timestamp': timestamp,
            'messages': st.session_state.messages.copy()
        }
        st.session_state.chat_history.append(history)

def load_chat(timestamp: str):
    """Load a specific chat from history"""
    for chat in st.session_state.chat_history:
        if chat['timestamp'] == timestamp:
            st.session_state.messages = chat['messages'].copy()
            st.session_state.selected_chat = timestamp
            st.rerun()

def new_chat():
    """Start a new chat"""
    if st.session_state.messages:  # Save current chat if it exists
        save_chat_history()
    st.session_state.messages = []
    st.session_state.selected_chat = None
    st.rerun()

def process_file(file) -> str:
    """Process uploaded file and return its content"""
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_file.write(file.getvalue())
        tmp_file.flush()
        
        # Read file content based on file type
        if file.type == "text/plain":
            with open(tmp_file.name, 'r') as f:
                content = f.read()
        else:
            content = f"File uploaded: {file.name} (type: {file.type})"
            
        os.unlink(tmp_file.name)
        return content

def get_groq_response(messages: List[dict]) -> str:
    """Get response from Groq API"""
    try:
        chat_completion = client.chat.completions.create(
            messages=messages,
            model="mixtral-8x7b-32768",
            temperature=0.7,
            max_tokens=1024,
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        return f"Error getting response: {str(e)}"

# Sidebar for chat history
with st.sidebar:
    st.button("New Chat", on_click=new_chat, key="new_chat")
    
    if st.session_state.chat_history:
        st.header("Chat History")
        for chat in reversed(st.session_state.chat_history):
            # Format timestamp for display
            display_time = datetime.strptime(chat['timestamp'], "%Y%m%d_%H%M%S").strftime("%Y-%m-%d %H:%M:%S")
            # Calculate preview from first message
            preview = chat['messages'][0]['content'][:30] + "..." if chat['messages'] else "Empty chat"
            
            # Create a unique key for each button based on timestamp
            if st.button(
                f"📝 {display_time}\n{preview}",
                key=chat['timestamp'],
                help="Click to load this chat"
            ):
                load_chat(chat['timestamp'])

# Main chat interface
st.title("💬 Chatbot with File Support")

# File upload
uploaded_file = st.file_uploader("Upload a file", type=['txt', 'pdf', 'doc', 'docx'])
if uploaded_file:
    file_content = process_file(uploaded_file)
    st.session_state.messages.append({"role": "user", "content": f"I've uploaded a file with the following content:\n\n{file_content}"})

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("What would you like to discuss?"):
    # Save current chat before adding new message if it's not already saved
    if not st.session_state.selected_chat and st.session_state.messages:
        save_chat_history()
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Get assistant response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = get_groq_response(st.session_state.messages)
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
