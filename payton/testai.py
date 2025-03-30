import requests
import json
import mysql.connector
from pydantic import BaseModel
from typing import List
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
        "Authorization": f"Bearer {api_key}",
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
        return clean_response(response_data['choices'][0]['message']['content'])
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return None

# Function to clean the response
def clean_response(response):
    cleaned_response = response.strip()  # Remove leading/trailing whitespace
    cleaned_response = cleaned_response.replace('*', '')  # Remove asterisks
    cleaned_response = cleaned_response.replace('`', '')  # Remove backticks if present
    return cleaned_response

def connect_to_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="aiprompt"
    )

def store_chat_history(user_input: str, ai_response: str):
    db = connect_to_db()
    cursor = db.cursor()
    
    sql = "INSERT INTO chat_history (user_input, ai_response) VALUES (%s, %s)"
    cursor.execute(sql, (user_input, ai_response))
    
    db.commit()
    cursor.close()
    db.close()

def main():
    st.set_page_config(page_title="BLOOMEDGE", page_icon="🧠", layout="wide")
    st.title("Bloomedge 🧠")
    st.write("Welcome to the Bloomedge Chatbot! Type your message below.")

    # Dropdown for Learner Level
    learner_level = ["Slow Learner", "Average Learner", "Advanced Learner"]
    selected_learner_level = st.selectbox("Select Learner Level:", learner_level)

    # Dropdown for Learner Grade
    learner_grade = ["Grade 1", "Grade 2", "Grade 3", "Grade 4", "Grade 5", "Grade 6", "Grade 7", "Grade 8", "Grade 9", "Grade 10", "Grade 11", "Grade 12"]
    selected_learner_grade = st.selectbox("Select Grade Level:", learner_grade)

    # Dropdown for Type of Learner
    learner_type = ["Visual Learner", "Auditory Learner", "Kinesthetic Learner", "Read/Write Learner"]
    selected_learner_type = st.selectbox("Select Type of Learner:", learner_type)

    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = ChatHistory(messages=[])

    chat_container = st.container()

    # Display chat messages
    with chat_container:
        for message in st.session_state.chat_history.messages:
            if message.role == "user":
                st.markdown(f"""
                    <div style='text-align: right;'>
                        <div style='border-radius: 15px; background-color: #4287f5; padding: 10px; margin: 5px; max-width: 70%; display: inline-block; color: white;'>
                            {message.content}
                        </div>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                    <div style='text-align: left;'>
                        <div style='border-radius: 15px; background-color: #334f7a; padding: 10px; margin: 5px; max-width: 70%; display: inline-block;'>
                            {message.content}
                        </div>
                    </div>
                """, unsafe_allow_html=True)

    # User input field at the bottom using text_area for better formatting
    user_input = st.text_area("Type your message here...", key="input_field", placeholder="Type your message...", height=150)

    def send_message():
        if user_input:
            user_message = Message(role="user", content=user_input)
            st.session_state.chat_history.messages.append(user_message)

            with chat_container:
                st.markdown(f"""
                    <div style='text-align: right;'>
                        <div style='border-radius: 15px; text-align: left; background-color:  #4287f5; padding: 10px; margin: 5px; max-width: 70%; display: inline-block; color: white;'>
                            {user_input}
                        </div>
                    </div>
                """, unsafe_allow_html=True)

            typing_placeholder = st.empty()
            typing_placeholder.markdown("<div style='text-align: left;'><i>Chatbot is typing...</i></div>", unsafe_allow_html=True)

            time.sleep(2)

            response = get_chatbot_response(st.session_state.chat_history.messages + [
                Message(role="system", content=f"Learner Level: {selected_learner_level}, Grade: {selected_learner_grade}, Type: {selected_learner_type}")
            ])

            if response:
                st.session_state.chat_history.messages.append(Message(role="assistant", content=response))

                store_chat_history(user_input, response)

                typing_placeholder.empty()

                with chat_container:
                    st.markdown(f"""
                        <div style='text-align: left;'>
                            <div style='border-radius: 15px; background-color:#444a46; padding: 10px; margin: 5px; max-width: 70%; display: inline-block;'>
                                {response}
                            </div>
                        </div>
                    """, unsafe_allow_html=True)

            else:
                typing_placeholder.empty()
                st.write("Chatbot: Sorry, I couldn't get a response.")

    if user_input:
        send_message()

if __name__ == "__main__":
    main()