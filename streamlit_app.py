import streamlit as st
import requests
import json
import sqlite3
import hashlib
import os
import time
import csv
from datetime import datetime, timedelta
from collections import deque
import pandas as pd

# Constants
API_KEY = "LA-54944fad3e444375aecc8601577db76d00dd4a8a12de4624864e0a7c5d5a4e0d"
MAX_RETRIES = 3
RATE_LIMIT_PERIOD = 60  # in seconds
MAX_REQUESTS_PER_PERIOD = 20

# Database setup
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users
        (username TEXT PRIMARY KEY,
         password TEXT NOT NULL,
         conversation_history TEXT DEFAULT '[]')
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS rate_limits
        (username TEXT PRIMARY KEY,
         requests JSON NOT NULL)
    ''')
    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def add_user(username, password):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", 
                 (username, hash_password(password)))
        c.execute("INSERT INTO rate_limits (username, requests) VALUES (?, ?)",
                 (username, '[]'))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def verify_user(username, password):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT password FROM users WHERE username=?", (username,))
    result = c.fetchone()
    conn.close()
    if result and result[0] == hash_password(password):
        return True
    return False

def save_conversation_history(username, history):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("UPDATE users SET conversation_history=? WHERE username=?",
              (json.dumps(history), username))
    conn.commit()
    conn.close()

def load_conversation_history(username):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT conversation_history FROM users WHERE username=?", (username,))
    result = c.fetchone()
    conn.close()
    return json.loads(result[0]) if result and result[0] else []

# Rate limiting
class RateLimiter:
    def __init__(self, username):
        self.username = username
        self.requests = self._load_requests()

    def _load_requests(self):
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("SELECT requests FROM rate_limits WHERE username=?", (self.username,))
        result = c.fetchone()
        if result:
            return json.loads(result[0])
        return []

    def _save_requests(self):
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("UPDATE rate_limits SET requests=? WHERE username=?",
                 (json.dumps(self.requests), self.username))
        conn.commit()
        conn.close()

    def can_make_request(self):
        current_time = time.time()
        # Remove old requests
        self.requests = [req for req in self.requests 
                        if current_time - req < RATE_LIMIT_PERIOD]
        
        if len(self.requests) < MAX_REQUESTS_PER_PERIOD:
            self.requests.append(current_time)
            self._save_requests()
            return True
        return False

    def time_until_next_request(self):
        if not self.requests:
            return 0
        current_time = time.time()
        oldest_request = min(self.requests)
        return max(0, RATE_LIMIT_PERIOD - (current_time - oldest_request))

# API Call with retry logic
def llamaapi_call(prompt, username, temperature=0.7, max_tokens=800):
    rate_limiter = RateLimiter(username)
    
    if not rate_limiter.can_make_request():
        wait_time = rate_limiter.time_until_next_request()
        st.warning(f"Rate limit reached. Please wait {int(wait_time)} seconds.")
        return "Rate limit reached. Please wait a moment before trying again."

    url = "https://api.llamaapi.net/chat"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    messages = [
        {"role": "system", "content": "You are a helpful assistant."}
    ]
    
    # Add the conversation history
    for msg in st.session_state.messages[-5:]:
        messages.append({"role": msg["role"], "content": msg["content"]})
    
    messages.append({"role": "user", "content": prompt})
    
    data = {
        "messages": messages,
        "stream": False,
        "max_tokens": max_tokens,
        "temperature": temperature
    }
    
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content']
        except requests.exceptions.RequestException as e:
            if attempt == MAX_RETRIES - 1:
                st.error(f"API Error: {str(e)}")
                if hasattr(e.response, 'text'):
                    st.error(f"API Response: {e.response.text}")
                return "I apologize, but I encountered an error while processing your request."
            time.sleep(2 ** attempt)  # Exponential backoff

# Initialize database
init_db()

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'temperature' not in st.session_state:
    st.session_state.temperature = 0.7
if 'max_tokens' not in st.session_state:
    st.session_state.max_tokens = 800

# Export conversation history
def export_conversation(messages, format='csv'):
    if format == 'csv':
        df = pd.DataFrame(messages)
        return df.to_csv(index=False).encode('utf-8')
    else:  # json
        return json.dumps(messages, indent=2).encode('utf-8')

# Authentication UI
def show_auth_ui():
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    
    with tab1:
        st.subheader("Login")
        login_username = st.text_input("Username", key="login_username")
        login_password = st.text_input("Password", type="password", key="login_password")
        
        if st.button("Login"):
            if login_username and login_password:
                if verify_user(login_username, login_password):
                    st.session_state.logged_in = True
                    st.session_state.username = login_username
                    st.session_state.messages = load_conversation_history(login_username)
                    st.success("Logged in successfully!")
                    st.rerun()
                else:
                    st.error("Invalid username or password")
            else:
                st.warning("Please fill in all fields")

    with tab2:
        st.subheader("Sign Up")
        new_username = st.text_input("Username", key="new_username")
        new_password = st.text_input("Password", type="password", key="new_password")
        confirm_password = st.text_input("Confirm Password", type="password")
        
        if st.button("Sign Up"):
            if new_username and new_password and confirm_password:
                if new_password == confirm_password:
                    if add_user(new_username, new_password):
                        st.success("Account created successfully! Please login.")
                    else:
                        st.error("Username already exists")
                else:
                    st.error("Passwords do not match")
            else:
                st.warning("Please fill in all fields")

# Main UI
def show_chat_ui():
    st.title("🦙 Llama Chatbot")
    
    # Sidebar
    with st.sidebar:
        st.title("Settings")
        st.write(f"Logged in as: {st.session_state.username}")
        
        # API Parameters
        st.subheader("API Parameters")
        st.session_state.temperature = st.slider(
            "Temperature",
            min_value=0.1,
            max_value=1.0,
            value=st.session_state.temperature,
            step=0.1,
            help="Higher values make the output more random, lower values make it more focused and deterministic"
        )
        
        st.session_state.max_tokens = st.slider(
            "Max Tokens",
            min_value=100,
            max_value=2000,
            value=st.session_state.max_tokens,
            step=100,
            help="Maximum length of the response"
        )
        
        # Export options
        st.subheader("Export Chat History")
        export_format = st.selectbox("Export Format", ["CSV", "JSON"])
        if st.button("Export Chat"):
            file_extension = "csv" if export_format == "CSV" else "json"
            st.download_button(
                label="Download Chat History",
                data=export_conversation(st.session_state.messages, export_format.lower()),
                file_name=f"chat_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{file_extension}",
                mime=f"text/{file_extension}"
            )
        
        if st.button("Clear Chat History"):
            st.session_state.messages = []
            save_conversation_history(st.session_state.username, [])
            st.rerun()
            
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.username = None
            st.session_state.messages = []
            st.rerun()

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    # Chat input
    if prompt := st.chat_input("What would you like to ask?"):
        with st.chat_message("user"):
            st.write(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = llamaapi_call(
                    prompt,
                    st.session_state.username,
                    st.session_state.temperature,
                    st.session_state.max_tokens
                )
                st.write(response)
        st.session_state.messages.append({"role": "assistant", "content": response})
        
        # Save conversation history
        save_conversation_history(st.session_state.username, st.session_state.messages)

    # Footer
    st.markdown("---")
    st.markdown("Made with ❤️ using Streamlit and Llama API")

# Main app logic
def main():
    if not st.session_state.logged_in:
        show_auth_ui()
    else:
        show_chat_ui()

if __name__ == "__main__":
    main()
