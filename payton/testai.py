import requests
import json
import mysql.connector
from pydantic import BaseModel
from typing import List
import re
import streamlit as st
import time

# Pydantic models
class Message(BaseModel):
    role: str
    content: str

class ChatHistory(BaseModel):
    messages: List[Message]

# Function to get chatbot response
def get_chatbot_response(messages):
    api_key = "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"
    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer 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",
        "Content-Type": "application/json",
    }

    message_dicts = [message.dict() for message in messages]

    data = {
        "model": "deepseek/deepseek-chat-v3-0324:free",
        "messages": message_dicts,
    }

    response = requests.post(url, headers=headers, data=json.dumps(data))

    if response.status_code == 200:
        response_data = response.json()
        return response_data['choices'][0]['message']['content']
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return None

def connect_to_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",  # Replace with your MySQL username
        password="",  # Replace with your MySQL password
        database="aiprompt"  # Replace with your MySQL database name
    )

def store_chat_history(user_input: str, ai_response: str):
    db = connect_to_db()
    cursor = db.cursor()
    
    sql = "INSERT INTO chat_history (user_input, ai_response) VALUES (%s, %s)"
    cursor.execute(sql, (user_input, ai_response))
    
    db.commit()
    cursor.close()
    db.close()

def clean_ai_response(response: str) -> str:
    response = response.strip()
    response = re.sub(r'[^\w\s,.!?]', '', response)
    return response

# Streamlit UI
def main():
    st.set_page_config(page_title="Chatbot", page_icon="🤖", layout="wide")
    st.title("Chatbot 🤖")
    st.write("Welcome to the Chatbot! Type your message below.")

    # Initialize chat history
    chat_history = ChatHistory(messages=[])

    # Create a container for the chat messages
    chat_container = st.container()

    # User input
    user_input = st.text_input("You:", "")

    if st.button("Send"):
        if user_input:
            user_message = Message(role="user", content=user_input)
            chat_history.messages.append(user_message)

            # Display user message
            with chat_container:
                st.markdown(f"<div style='text-align: right;'> {user_input}</div>", unsafe_allow_html=True)

            # Simulate typing indicator
            typing_placeholder = st.empty()
            typing_placeholder.markdown("<div style='text-align: left;'><i>Chatbot is typing...</i></div>", unsafe_allow_html=True)

            # Simulate a delay for typing effect
            time.sleep(2)  # Simulate typing time (adjust as needed)

            # Get AI response
            response = get_chatbot_response(chat_history.messages)

            if response:
                # Clean the AI response
                cleaned_response = clean_ai_response(response)
                chat_history.messages.append(Message(role="assistant", content=cleaned_response))

                # Store user input and cleaned AI response in the database
                store_chat_history(user_input, cleaned_response)

                # Clear typing indicator
                typing_placeholder.empty()

                # Display chatbot response
                with chat_container:
                    st.markdown(f"<div style='text-align: left;'> {cleaned_response}</div>", unsafe_allow_html=True)

            else:
                typing_placeholder.empty()
                st.write("Chatbot: Sorry, I couldn't get a response.")

if __name__ == "__main__":
    main()