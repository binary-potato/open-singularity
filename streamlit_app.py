import streamlit as st
from groq import Groq
import cohere
import google.generativeai as genai
import uuid
from datetime import datetime
import os
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

# Load environment variables
load_dotenv()

# Initialize API clients
groq_client = Groq(api_key=os.getenv('GROQ_API_KEY'))
cohere_client = cohere.Client(os.getenv('COHERE_API_KEY'))
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
gemini_model = genai.GenerativeModel('gemini-pro')
hf_client = InferenceClient(token=os.getenv('HF_API_KEY'))

# Initialize session state variables
if 'chats' not in st.session_state:
    st.session_state.chats = {}
if 'current_chat_id' not in st.session_state:
    st.session_state.current_chat_id = None
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'show_file_upload' not in st.session_state:
    st.session_state.show_file_upload = False
if 'selected_provider' not in st.session_state:
    st.session_state.selected_provider = 'Groq'

# Function to create new chat
def create_new_chat():
    chat_id = str(uuid.uuid4())
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.chats[chat_id] = {
        'timestamp': timestamp,
        'messages': [],
        'provider': st.session_state.selected_provider
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

# Function to get bot response
def get_bot_response(messages):
    if st.session_state.selected_provider == 'Groq':
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {"role": m["role"], "content": m["content"]} 
                for m in messages
            ],
            model="mixtral-8x7b-32768",
            temperature=0.7,
            max_tokens=1024,
        )
        return chat_completion.choices[0].message.content
    
    elif st.session_state.selected_provider == 'Cohere':
        chat_history = []
        for m in messages[:-1]:
            chat_history.append({"role": m["role"], "message": m["content"]})
        
        response = cohere_client.chat(
            message=messages[-1]["content"],
            chat_history=chat_history,
            model="command",
            temperature=0.7,
            max_tokens=1024
        )
        return response.text
    
    elif st.session_state.selected_provider == 'Hugging Face':
        # Using text-generation-inference API
        conversation = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
        response = hf_client.text_generation(
            conversation,
            model="mistralai/Mixtral-8x7B-Instruct-v0.1",
            max_new_tokens=1024,
            temperature=0.7
        )
        return response
    
    else:  # Gemini
        gemini_messages = []
        for m in messages:
            role = "user" if m["role"] == "user" else "model"
            gemini_messages.append({"role": role, "parts": [m["content"]]})
        
        chat = gemini_model.start_chat(history=gemini_messages[:-1])
        response = chat.send_message(messages[-1]["content"])
        return response.text

# Streamlit UI
st.set_page_config(page_title="Chatbot", layout="wide")

# [Rest of the UI code remains exactly the same...]

# Update provider selection to include Hugging Face
with st.sidebar:
    st.title("💬 Chat History")
    
    st.session_state.selected_provider = st.selectbox(
        "Select Model Provider",
        ["Groq", "Cohere", "Gemini", "Hugging Face"],
        key="model_provider"
    )
    
    # [Rest of the sidebar code remains the same...]
