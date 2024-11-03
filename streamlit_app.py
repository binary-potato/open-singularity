import streamlit as st
import groq
from typing import List
import os
import tempfile
import json
from datetime import datetime

# Initialize Groq client
client = groq.Groq(api_key="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")

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []

if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

def save_chat_history():
    """Save chat history to a JSON file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    history = {
        'timestamp': timestamp,
        'messages': st.session_state.messages
    }
    st.session_state.chat_history.append(history)
    
    # Save to file
    with open(f'chat_history_{timestamp}.json', 'w') as f:
        json.dump(history, f, indent=2)

def load_chat_history(file):
    """Load chat history from a JSON file"""
    content = file.read()
    history = json.loads(content)
    return history['messages']

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

# Streamlit UI
st.title("💬 Chatbot with File Support")

# File upload
uploaded_file = st.file_uploader("Upload a file", type=['txt', 'pdf', 'doc', 'docx'])
if uploaded_file:
    file_content = process_file(uploaded_file)
    st.session_state.messages.append({"role": "user", "content": f"I've uploaded a file with the following content:\n\n{file_content}"})

# Load previous chat
uploaded_history = st.file_uploader("Load previous chat", type=['json'])
if uploaded_history:
    st.session_state.messages = load_chat_history(uploaded_history)
    st.rerun()

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("What would you like to discuss?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Get assistant response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = get_groq_response(st.session_state.messages)
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})

# Save chat button
if st.button("Save Chat History"):
    save_chat_history()
    st.success("Chat history saved!")

# Display chat history
if st.session_state.chat_history:
    st.subheader("Previous Chats")
    for history in st.session_state.chat_history:
        st.write(f"Chat from {history['timestamp']}")
