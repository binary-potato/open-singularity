import streamlit as st
import requests
import json
import hashlib
import time
from datetime import datetime
import pandas as pd

# Constants
API_KEY = "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"
MAX_RETRIES = 3
RATE_LIMIT_PERIOD = 60  # in seconds
MAX_REQUESTS_PER_PERIOD = 20

# Initialize session state for user data storage
if 'users' not in st.session_state:
    st.session_state.users = {}
if 'rate_limits' not in st.session_state:
    st.session_state.rate_limits = {}
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

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def add_user(username, password):
    if username not in st.session_state.users:
        st.session_state.users[username] = {
            'password': hash_password(password),
            'conversation_history': []
        }
        st.session_state.rate_limits[username] = []
        return True
    return False

def verify_user(username, password):
    if username in st.session_state.users:
        return st.session_state.users[username]['password'] == hash_password(password)
    return False

# Rate limiting
class RateLimiter:
    def __init__(self, username):
        self.username = username
        if username not in st.session_state.rate_limits:
            st.session_state.rate_limits[username] = []

    def can_make_request(self):
        current_time = time.time()
        requests = st.session_state.rate_limits[self.username]
        
        # Remove old requests
        requests = [req for req in requests if current_time - req < RATE_LIMIT_PERIOD]
        st.session_state.rate_limits[self.username] = requests
        
        if len(requests) < MAX_REQUESTS_PER_PERIOD:
            st.session_state.rate_limits[self.username].append(current_time)
            return True
        return False

    def time_until_next_request(self):
        if not st.session_state.rate_limits[self.username]:
            return 0
        current_time = time.time()
        oldest_request = min(st.session_state.rate_limits[self.username])
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
                    st.session_state.messages = st.session_state.users[login_username]['conversation_history']
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
            st.session_state.users[st.session_state.username]['conversation_history'] = []
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
        st.session_state.users[st.session_state.username]['conversation_history'] = st.session_state.messages

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
