import os
from dotenv import load_dotenv
import streamlit as st
from groq import Groq
import cohere
import google.generativeai as genai
import uuid
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

# Load API keys from environment variables
groq_api_key = os.environ.get("GROQ_API_KEY")
cohere_api_key = os.environ.get("COHERE_API_KEY")
gemini_api_key = os.environ.get("GEMINI_API_KEY")

print("Groq API Key:", groq_api_key)
print("Cohere API Key:", cohere_api_key)
print("Gemini API Key:", gemini_api_key)

# Initialize Groq client and handle errors
try:
    groq_client = Groq(api_key=groq_api_key)
except GroqError as e:
    print("Error initializing Groq client:", e)
    groq_client = None

# Initialize other API clients
cohere_client = cohere.Client(cohere_api_key)
genai.configure(api_key=gemini_api_key)

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
        if groq_client:
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
        else:
            return "Groq client could not be initialized. Please check your API key."
    
    elif st.session_state.selected_provider == 'Cohere':
        # Convert messages to Cohere format
        chat_history = []
        for m in messages[:-1]:  # Exclude the last message
            chat_history.append({"role": m["role"], "message": m["content"]})
        
        response = cohere_client.chat(
            message=messages[-1]["content"],
            chat_history=chat_history,
            model="command",
            temperature=0.7,
            max_tokens=1024
        )
        return response.text
    
    else:  # Gemini
        # Convert messages to Gemini format
        gemini_messages = []
        for m in messages:
            role = "user" if m["role"] == "user" else "model"
            gemini_messages.append({"role": role, "parts": [m["content"]]})
        
        chat = gemini_model.start_chat(history=gemini_messages[:-1])
        response = chat.send_message(messages[-1]["content"])
        return response.text

# Streamlit UI
st.set_page_config(page_title="Chatbot", layout="wide")

# Custom CSS
st.markdown("""
# ... (rest of the code remains the same) ...
""", unsafe_allow_html=True)
